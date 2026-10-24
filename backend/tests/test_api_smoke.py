"""Smoke: story -> character -> ep1 death (pending) -> confirm dead -> ep2 dead speaks CRITICAL -> suggest -> continuity -> threads."""

from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app


def test_api_smoke():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    c = TestClient(app)

    r = c.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    # create story with rules -> setting_rules mapping
    r = c.post(
        "/api/story/bible",
        json={
            "title": "The Long Night",
            "genre": "drama",
            "setting": "A coastal town",
            "rules": ["No magic without cost"],
        },
    )
    assert r.status_code == 200
    story_id = r.json()["story_id"]

    # full bible shows rules mapping
    r = c.get(f"/api/story/bible/{story_id}/full")
    assert r.status_code == 200
    full = r.json()
    assert full["story"]["setting_rules"] == ["No magic without cost"]

    # add character
    r = c.post(
        f"/api/story/{story_id}/characters",
        json={"name": "Kael", "status": "alive"},
    )
    assert r.status_code == 200

    # ep1 death -> pending confirm_dead, status still alive
    r = c.post(
        f"/api/story/{story_id}/episode",
        json={"number": 1, "title": "Farewell", "text": "Kael died."},
    )
    assert r.status_code == 200
    body = r.json()
    assert "episode_id" in body
    pending = [p for p in body["pending"] if p["action"] == "confirm_dead"]
    assert len(pending) == 1
    assert (pending[0]["payload"] or {}).get("name") == "Kael"
    cid = pending[0]["id"]

    r = c.get(f"/api/story/bible/{story_id}/full")
    chars = {ch["name"]: ch for ch in r.json()["characters"]}
    assert chars["Kael"]["status"] == "alive"

    # confirm -> status dead
    r = c.patch(f"/api/story/changes/{cid}", json={"decision": "confirm"})
    assert r.status_code == 200
    r = c.get(f"/api/story/bible/{story_id}/full")
    chars = {ch["name"]: ch for ch in r.json()["characters"]}
    assert chars["Kael"]["status"] == "dead"

    # ep2 dead speaks -> CRITICAL
    r = c.post(
        f"/api/story/{story_id}/episode",
        json={"number": 2, "title": "Ghost", "text": 'Kael said "I am back."'},
    )
    assert r.status_code == 200
    kinds = [(i["severity"], i["kind"]) for i in r.json()["issues"]]
    assert ("CRITICAL", "DEAD_ALIVE") in kinds

    # suggest non-empty
    r = c.post(f"/api/story/{story_id}/suggest")
    assert r.status_code == 200
    s = r.json()
    assert s["payoff"] and s["beat"] and s["world"]

    # continuity ordered, each with episode_no
    r = c.get(f"/api/story/{story_id}/continuity")
    assert r.status_code == 200
    issues = r.json()["issues"]
    assert any(i["severity"] == "CRITICAL" and i["kind"] == "DEAD_ALIVE" for i in issues)
    for i in issues:
        assert "episode_no" in i

    # threads buckets
    r = c.get(f"/api/story/{story_id}/threads")
    assert r.status_code == 200
    buckets = r.json()
    assert {"active", "dormant", "resolved"} <= set(buckets)
