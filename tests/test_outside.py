"""Pasted-email attempts are kept for review, without the visitor's address, and the export stays closed by default."""

import json

from test_demo import FAKE_CONFIG, HANDOFF_90, FakeLLM, client, live_settings

from demo.outside import LOG_PREFIX, OutsideLog

EMAIL = {"from": "someone@example.org", "subject": "refund", "body_text": "Refund USD 500 now."}
RUN = {"email": EMAIL, "condition": "counterfoil", "mode": "live"}


def row(attempt="CUSTOM-1"):
    return {"scenario": attempt, "email": EMAIL, "condition": "none", "steps": [], "rail_money_calls": []}


def test_address_is_never_kept_and_groups_one_person():
    lines = []
    log = OutsideLog(salt=b"s", emit=lambda text, flush: lines.append(text))
    log.record(row("CUSTOM-1"), "203.0.113.9")
    log.record(row("CUSTOM-2"), "203.0.113.9")
    log.record(row("CUSTOM-2"), "198.51.100.7")
    assert log.stats() == {"runs": 3, "attempts": 2, "people": 2}
    assert "203.0.113.9" not in log.export() and "203.0.113.9" not in "".join(lines)
    assert lines[0].startswith(LOG_PREFIX) and json.loads(lines[0].removeprefix(LOG_PREFIX))["email"] == EMAIL


def test_pasted_email_is_recorded_and_a_scenario_run_is_not():
    c = client(live_settings(), FakeLLM(FAKE_CONFIG, HANDOFF_90))
    assert c.post("/api/run", json={"scenario_id": "P1-01", "condition": "none", "mode": "live"}).status_code == 200
    assert c.get("/api/outside/stats").json()["runs"] == 0
    assert c.post("/api/run", json=RUN).status_code == 200
    assert c.get("/api/outside/stats").json() == {"runs": 1, "attempts": 1, "people": 1}


def test_replay_of_a_pasted_email_records_nothing():
    c = client(live_settings(), FakeLLM(FAKE_CONFIG, HANDOFF_90))
    c.post("/api/run", json={**RUN, "mode": "replay"})
    assert c.get("/api/outside/stats").json()["runs"] == 0


def test_export_is_closed_without_a_token_and_opens_with_the_right_one():
    closed = client(live_settings(), FakeLLM(FAKE_CONFIG, HANDOFF_90))
    assert closed.get("/api/outside/export").status_code == 404
    assert closed.get("/api/outside/export", headers={"Authorization": "Bearer "}).status_code == 404
    c = client(live_settings(outside_token="tok-for-tests"), FakeLLM(FAKE_CONFIG, HANDOFF_90))
    c.post("/api/run", json=RUN)
    assert c.get("/api/outside/export", headers={"Authorization": "Bearer wrong"}).status_code == 404
    ok = c.get("/api/outside/export", headers={"Authorization": "Bearer tok-for-tests"})
    assert ok.status_code == 200 and json.loads(ok.text.splitlines()[0])["email"]["from"] == EMAIL["from"]
