"""FastAPI app for the live demo.

    uvicorn demo.app:app --reload          # http://localhost:8000

Every run goes through scripts/run_eval.run_one, the same function that produced the published numbers, so the demo
cannot drift from the evaluation. The server adds only what a public URL needs: replay of saved runs (default, no
key), a metered live mode, input limits, and a rail that cannot leave the fixture store.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import uuid
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi import Path as PathParam
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator

from counterfoil.llm import LLM
from counterfoil.paypal import PayPalSandboxRail
from counterfoil.rail import SandboxRail
from counterfoil.scenarios import load_records, load_scenarios
from scripts.run_eval import CONDITIONS, run_one

from .checkout import Checkout
from .limits import LRU, DailyBudget, MeteredLLM, RateLimiter
from .replay import Replays
from .scope import ScopedRail
from .settings import Settings

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
MAX_BODY_BYTES = 64 * 1024
# The HOMI story scene, served from where Blender exports it (tools/export_story_glb.py): the animated GLB and its
# step table (cameras, frame ranges). Only these two files; the rest of docs/gorseller is not served.
STORY = ROOT / "docs" / "gorseller"
STORY_FILES = {"homi-story.glb": "model/gltf-binary", "homi-story.json": "application/json"}
log = logging.getLogger("counterfoil.demo")
SECRET_ENV = re.compile(r"KEY|SECRET|TOKEN|PASSWORD|PRIVATE|BRAINTREE_MERCHANT_ID|BRAINTREE_PUBLIC|PAYPAL_CLIENT_ID")
# Every scenario is set on the same business date; a pasted email gets it too, so refund windows behave the same.
AS_OF = "2026-10-23T12:00:00Z"
ALL_TOOLS = ["refund", "void", "charge", "lookup_transaction"]


class EmailIn(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    from_: str = Field(alias="from", min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+$")
    subject: str = Field("", max_length=300)
    body_text: str = ""
    body_html: str | None = None
    attachment_text: str | None = None


class BuyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_id: str = Field(max_length=32)
    nonce: str = Field(min_length=4, max_length=256)


class StoryBuyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nonce: str = Field(min_length=4, max_length=256)


# The story on the dashboard (dashboard/app/story-3d.tsx): Nella pays one receipt at till 01, the cups order the
# return is checked against plus the rug and the plant. The extras add to the sandbox sale, not to the order.
STORY_SCENARIO = "P6-01"
STORY_EXTRAS = (("Folded rug", "49.00"), ("Potted plant", "19.00"))
STORY_SID = r"^[a-z0-9]{12,40}$"
# the dashboard reads a store session from another origin: production, its preview builds, local development
DASHBOARD_ORIGINS = r"^https://counterfoil-dashboard(-[a-z0-9-]+)?\.vercel\.app$|^http://localhost:3388$"


class RefundIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purchase_id: str = Field(min_length=8, max_length=64)
    scenario_id: str = Field(max_length=32)
    condition: Literal["none", "cap", "counterfoil"] = "counterfoil"
    source: str | None = Field(None, max_length=120)


class ApproveIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purchase_id: str = Field(min_length=8, max_length=64)
    approval_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    decision: Literal["approve", "reject"]


class RunIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_id: str | None = Field(None, max_length=32)
    email: EmailIn | None = None
    condition: Literal["none", "cap", "counterfoil"] = "counterfoil"
    mode: Literal["replay", "live"] = "replay"
    source: str | None = Field(None, max_length=120)  # replay only: which results/*.jsonl

    @model_validator(mode="after")
    def _one_input(self):
        if (self.scenario_id is None) == (self.email is None):
            raise ValueError("give exactly one of scenario_id or email")
        return self


def _secrets() -> list[str]:
    return [v for k, v in os.environ.items() if SECRET_ENV.search(k) and v and len(v) >= 6 and v != "sandbox"]


def redact(obj, secrets: list[str]):
    """Belt and braces: provider error messages end up in rows (reader_error, agent_error); a key must not."""
    if not secrets:
        return obj
    text = json.dumps(obj, ensure_ascii=False, default=str)
    for s in secrets:
        text = text.replace(s, "[redacted]")
    return json.loads(text)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def create_app(settings: Settings | None = None, llm_factory=None, results: Path = ROOT / "results") -> FastAPI:
    """`llm_factory(config)` builds the live client; tests pass a scripted fake so live mode runs without a network."""
    settings = settings or Settings.from_env()
    llm_factory = llm_factory or LLM
    scenarios = {s["id"]: s for s in load_scenarios()}
    records = load_records()
    replays = Replays(results, settings.replay_source)
    limiter = RateLimiter(settings.rate_limit, settings.rate_window_s)
    budget = DailyBudget(settings.daily_llm_calls)
    slots = threading.BoundedSemaphore(settings.max_concurrent)
    reader_cache = LRU()
    live_llm = MeteredLLM(llm_factory(settings.live), budget) if settings.live else None
    checkout = Checkout(settings.braintree)

    app = FastAPI(title="Counterfoil live demo", docs_url=None, redoc_url=None, openapi_url=None)

    app.add_middleware(
        CORSMiddleware, allow_origin_regex=DASHBOARD_ORIGINS, allow_methods=["GET"], allow_credentials=False
    )

    @app.middleware("http")
    async def _body_limit(request: Request, call_next):
        if int(request.headers.get("content-length") or 0) > MAX_BODY_BYTES:
            return JSONResponse({"detail": "request body too large"}, status_code=413)
        response = await call_next(request)
        # the story's GLB and stills are a few MB and never carry visitor data; API answers are never cached
        static = request.url.path.startswith(("/story/", "/static/story/")) and response.status_code == 200
        response.headers["Cache-Control"] = "public, max-age=3600" if static else "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/pay", include_in_schema=False)
    def pay_page():
        """The page the dashboard's QR opens on a phone: HOMI's receipt and the PayPal (sandbox) button."""
        return FileResponse(STATIC / "pay.html")

    @app.get("/api/story/{sid}")
    def story_status(sid: str = PathParam(pattern=STORY_SID)):
        return checkout.story_status(sid)

    @app.post("/api/story/{sid}/buy")
    def story_buy(body: StoryBuyIn, request: Request, sid: str = PathParam(pattern=STORY_SID)):
        _checkout_guard(request, STORY_SCENARIO)
        try:
            return checkout.story_pay(sid, body.nonce, scenarios[STORY_SCENARIO], STORY_EXTRAS)
        except OverflowError:
            raise HTTPException(503, "the store is busy, try again in a minute") from None
        except ValueError as exc:  # Braintree's own decline message, no secrets in it
            raise HTTPException(402, f"payment failed: {exc}") from None
        except Exception:
            log.exception("story checkout failed")
            raise HTTPException(502, "the sandbox payment failed on the server") from None

    # the HOMI story player: story.js and one still per step for phones (static/story/), the scene from docs/gorseller
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/story/{name}", include_in_schema=False)
    def story_file(name: str):
        if name not in STORY_FILES or not (STORY / name).is_file():
            raise HTTPException(404, "not found")
        return FileResponse(STORY / name, media_type=STORY_FILES[name])

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        return {"ok": True}

    @app.get("/api/config")
    def config():
        return {
            **settings.public(),
            "daily_llm_calls_left": budget.remaining() if settings.live else 0,
            "replay_sources": list(replays.sources.values()),
            "replay_default": replays.default,
            "store": _store_summary(records),
            "story_scene": "/story/homi-story.glb" if all((STORY / f).is_file() for f in STORY_FILES) else None,
        }

    @app.get("/api/scenarios")
    def list_scenarios():
        return [
            {
                k: s.get(k)
                for k in (
                    "id",
                    "kind",
                    "family",
                    "technique",
                    "split",
                    "email",
                    "attacker_goal",
                    "expected_gateway_decision",
                    "expected_reason",
                    "rail_would_block",
                    "cap_200_would_block",
                )
            }
            | {"reader_contract": s["preconditions"].get("reader_contract"), "replay": replays.available(s["id"])}
            for s in scenarios.values()
        ]

    @app.post("/api/run")
    def run(body: RunIn, request: Request):
        if body.email is not None:
            e = body.email
            size = len(e.subject) + len(e.body_text) + len(e.body_html or "") + len(e.attachment_text or "")
            if size > settings.max_email_chars:
                raise HTTPException(
                    422, f"email is {size} characters; the demo accepts up to {settings.max_email_chars}"
                )
        if body.mode == "replay":
            return _replay(body)
        return _live(body, request)

    # -- real PayPal purchase (Braintree sandbox) + the recorded agent calls replayed onto it ------------------
    def _checkout_guard(request: Request, scenario_id: str | None):
        if not checkout.enabled:
            raise HTTPException(503, "PayPal checkout is off: the server has no Braintree sandbox keys")
        if scenario_id is not None and (scenario_id not in scenarios or "ground_truth" not in scenarios[scenario_id]):
            raise HTTPException(404, "unknown scenario")
        wait = limiter.retry_after(_client_ip(request))
        if wait:
            raise HTTPException(
                429, f"rate limit: try again in {wait:.0f}s", headers={"Retry-After": str(int(wait) + 1)}
            )

    @app.get("/api/checkout/token")
    def checkout_token():
        if not checkout.enabled:
            raise HTTPException(503, "PayPal checkout is off: the server has no Braintree sandbox keys")
        try:
            return {"client_token": checkout.client_token()}
        except Exception:
            log.exception("client token failed")
            raise HTTPException(502, "Braintree did not issue a client token") from None

    @app.post("/api/checkout/buy")
    def checkout_buy(body: BuyIn, request: Request):
        _checkout_guard(request, body.scenario_id)
        try:
            return checkout.buy(body.nonce, scenarios[body.scenario_id])
        except ValueError as exc:  # Braintree's own decline message, no secrets in it
            raise HTTPException(402, f"payment failed: {exc}") from None
        except Exception:
            log.exception("checkout failed")
            raise HTTPException(502, "the sandbox payment failed on the server") from None

    @app.post("/api/checkout/refund")
    def checkout_refund(body: RefundIn, request: Request):
        _checkout_guard(request, body.scenario_id)
        source = body.source or replays.default
        row = replays.get(source, body.scenario_id, body.condition) if source in replays.sources else None
        if row is None:
            raise HTTPException(404, f"no saved run of {body.scenario_id} under {body.condition}")
        try:
            out = checkout.refund_run(body.purchase_id, scenarios[body.scenario_id], body.condition, row)
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from None
        except Exception:
            log.exception("checkout refund run failed")
            raise HTTPException(502, "the sandbox refund run failed on the server") from None
        out["replayed_from"] = {"source": source, "model": row.get("model")}
        return redact(out, _secrets())

    @app.post("/api/checkout/approve")
    def checkout_approve(body: ApproveIn, request: Request):
        """The store manager's answer to a held call; only "approve" can send it to Braintree."""
        _checkout_guard(request, None)
        try:
            out = checkout.decide(body.purchase_id, body.approval_id, body.decision == "approve")
        except KeyError as exc:
            raise HTTPException(404, str(exc).strip("'\"")) from None
        except Exception:
            log.exception("checkout approval failed")
            raise HTTPException(502, "the approved call failed on the server") from None
        return redact(out, _secrets())

    def _replay(body: RunIn) -> dict:
        if body.email is not None:
            raise HTTPException(400, "a pasted email has no saved run; use live mode")
        if body.scenario_id not in scenarios:
            raise HTTPException(404, "unknown scenario")
        source = body.source or replays.default
        if source not in replays.sources:
            raise HTTPException(404, "unknown replay source")
        row = replays.get(source, body.scenario_id, body.condition)
        if row is None:
            raise HTTPException(404, f"no saved run of {body.scenario_id} under {body.condition} in {source}")
        row["demo"] = {"mode": "replay", "source": source}
        return row

    def _live(body: RunIn, request: Request) -> dict:
        if live_llm is None:
            raise HTTPException(503, f"live mode is off: {settings.live_reason}")
        if body.scenario_id is not None and body.scenario_id not in scenarios:
            raise HTTPException(404, "unknown scenario")
        wait = limiter.retry_after(_client_ip(request))
        if wait:
            raise HTTPException(
                429,
                f"rate limit: try again in {wait:.0f}s (replay mode is not limited)",
                headers={"Retry-After": str(int(wait) + 1)},
            )
        if budget.remaining() <= 0:
            raise HTTPException(429, "the demo's daily LLM budget is used up; replay mode still works")
        if not slots.acquire(blocking=False):
            raise HTTPException(503, "the live demo is busy, try again in a minute")
        try:
            scenario = scenarios[body.scenario_id] if body.scenario_id else _pasted(body.email, records)
            cached = scenario["id"] in reader_cache
            row = run_one(
                live_llm,
                scenario,
                body.condition,
                reader_cache,
                make_rail=_make_rail(settings),
                max_turns=settings.max_turns,
                max_calls=settings.max_calls,
            )
        except Exception:  # the message could carry provider details; the log has them
            log.exception("live run failed")
            raise HTTPException(500, "the run failed on the server") from None
        finally:
            slots.release()
        row["demo"] = {"mode": "live", "reader_cached": cached}
        if body.email is not None:
            row["email"] = scenario["email"]
        return redact(row, _secrets())

    return app


def _make_rail(settings: Settings):
    def make(store, fake_rail, scenario, condition):
        if settings.paypal_rest:
            inner = PayPalSandboxRail(store, f"demo-{uuid.uuid4().hex[:8]}-{scenario['id']}-{condition}")
            return ScopedRail(inner, store, "paypal-sandbox")
        if settings.braintree:
            inner = SandboxRail(store, f"demo-{uuid.uuid4().hex[:8]}-{scenario['id']}-{condition}")
            return ScopedRail(inner, store, "braintree-sandbox")
        return ScopedRail(fake_rail, store, "fake")

    return make


def _pasted(email: EmailIn, records: dict) -> dict:
    """A pasted email becomes a scenario with no ground truth (so it is not scored) against the baseline store.
    The sender is resolved from the From address like any other email; an unknown sender gets no customer."""
    mail = {
        "from": email.from_.strip(),
        "to": records["store"]["support_email"],
        "subject": email.subject,
        "body_text": email.body_text,
        "body_html": email.body_html or None,
        "attachment_text": email.attachment_text or None,
    }
    digest = hashlib.sha256(json.dumps(mail, sort_keys=True).encode()).hexdigest()[:12]
    sender = next((c["customer_id"] for c in records["customers"] if c["email"].lower() == mail["from"].lower()), None)
    return {
        "id": f"CUSTOM-{digest}",
        "kind": "custom",
        "family": "CUSTOM",
        "split": "custom",
        "email": mail,
        "preconditions": {
            "as_of": AS_OF,
            "session_id": f"session-CUSTOM-{digest}",
            "authenticated_customer_id": sender,
            "allowed_tools": ALL_TOOLS,
        },
    }


def _store_summary(records: dict) -> dict:
    """The fixture store as a judge needs it to write an email: who can write in, and what they bought."""
    emails = {c["customer_id"]: c["email"] for c in records["customers"]}
    return {
        "name": records["store"]["name"],
        "support_email": records["store"]["support_email"],
        "customers": [c["email"] for c in records["customers"]],
        "orders": [
            {
                "order_no": o["order_no"],
                "customer": emails.get(o["customer_id"]),
                "total": o["total"],
                "currency": o["currency"],
                "status": o["status"],
                "created_at": o.get("created_at"),
                "items": o["items"],
                "returns": [
                    {
                        "rma_id": r["rma_id"],
                        "approved_refund_amount": r["approved_refund_amount"],
                        "status": r["status"],
                    }
                    for r in o.get("returns", [])
                ],
            }
            for o in records["orders"]
        ],
    }


assert set(CONDITIONS) == {"none", "cap", "counterfoil"}, "RunIn.condition must list run_eval's conditions"  # noqa: S101
app = create_app()
