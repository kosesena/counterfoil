"""counterfoil-mcp: start the MCP server, or answer the refunds it is holding.

    .venv/bin/python scripts/counterfoil_mcp.py serve --scenario P6-01                   # stdio MCP server, fake rail
    .venv/bin/python scripts/counterfoil_mcp.py serve --scenario P6-01 --rail braintree  # Braintree sandbox (.env)
    .venv/bin/python scripts/counterfoil_mcp.py holds                                    # what is waiting, desk URL
    .venv/bin/python scripts/counterfoil_mcp.py approve <hold_id>
    .venv/bin/python scripts/counterfoil_mcp.py reject <hold_id>

`serve` speaks MCP on stdout; logs go to stderr. The other commands talk to the running server's approval desk on
127.0.0.1, using the address and token it wrote to ~/.counterfoil/mcp-desk.json. See docs/mcp.md.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from counterfoil.mcp_server import DESK_FILE, Desk, Session, build_server  # noqa: E402


def _desk_call(method: str, path: str) -> object:
    try:
        desk = json.loads(DESK_FILE.read_text())
    except FileNotFoundError:
        raise SystemExit(f"no running counterfoil-mcp server ({DESK_FILE} not found)") from None
    req = urllib.request.Request(  # noqa: S310 - fixed http://127.0.0.1 address the server wrote
        desk["url"] + path, method=method, headers={"Authorization": f"Bearer {desk['token']}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:  # noqa: S310
            return json.loads(r.read())
    except OSError as exc:
        raise SystemExit(f"the approval desk at {desk['url']} did not answer ({exc}); is the server running?") from None


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    serve = sub.add_parser("serve", help="run the MCP server on stdio")
    serve.add_argument("--scenario", help="scenario id from docs/senaryolar/scenarios.json (sender, state, hand-off)")
    serve.add_argument("--customer-email", help="verified sender, when no --scenario is given")
    serve.add_argument("--rail", choices=("fake", "braintree"), default="fake")
    serve.add_argument("--env-file", type=Path, default=ROOT / ".env", help="where the BRAINTREE_* keys are")
    serve.add_argument("--desk-port", type=int, default=0, help="approval desk port on 127.0.0.1 (0: any free port)")
    sub.add_parser("holds", help="list refunds waiting for a decision")
    for name in ("approve", "reject"):
        p = sub.add_parser(name, help=f"{name} a held refund")
        p.add_argument("hold_id")
    args = ap.parse_args(argv)

    if args.cmd == "serve":
        logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="counterfoil-mcp: %(message)s")
        if args.rail == "braintree":
            from dotenv import load_dotenv

            load_dotenv(args.env_file)
        session = Session.create(args.scenario, args.customer_email, args.rail)
        desk = Desk(session, args.desk_port).start()
        try:
            build_server(session).run("stdio")
        finally:
            desk.stop()
        return
    if args.cmd == "holds":
        desk = json.loads(DESK_FILE.read_text()) if DESK_FILE.exists() else None
        if desk:
            print(f"desk page: {desk['url']}/?token={desk['token']}")
        print(json.dumps(_desk_call("GET", "/holds"), indent=2))
        return
    print(json.dumps(_desk_call("POST", f"/holds/{args.hold_id}/{args.cmd}"), indent=2))


if __name__ == "__main__":
    main()
