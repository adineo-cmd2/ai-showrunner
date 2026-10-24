from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.bible_change import BibleChange
from app.models.character import Character
from app.models.story import Story
from app.models.user import User
from app.services.episode_pipeline import analyse_episode


def _fresh_story(db):
    u = User(email="pipe@example.com", password_hash=hash_password("secret123"))
    db.add(u)
    db.commit()
    db.refresh(u)
    story = Story(
        user_id=u.id, title="Saga", genre="drama", setting="town", setting_rules=[]
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    db.add(Character(story_id=story.id, name="Kael", status="alive"))
    db.commit()
    return story


def test_death_episode_has_no_dead_alive_but_pending():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    story = _fresh_story(db)

    result = analyse_episode(db, story, 1, "Farewell", "Kael died.")
    dead_alive = [i for i in result["issues"] if i["kind"] == "DEAD_ALIVE"]
    assert dead_alive == []
    pending = [
        p
        for p in result["pending"]
        if p["action"] == "confirm_dead"
        and (p["payload"] or {}).get("name") == "Kael"
        and p["status"] == "pending"
    ]
    assert len(pending) == 1
    # Pending-gate: Character row untouched until PATCH confirm.
    assert (
        db.query(Character)
        .filter(Character.story_id == story.id, Character.name == "Kael")
        .one()
        .status
        == "alive"
    )
    db.close()


def test_prior_death_then_speaking_is_critical():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    story = _fresh_story(db)

    analyse_episode(db, story, 1, "Farewell", "Kael died.")
    result = analyse_episode(db, story, 2, "Ghost", 'Kael said "I am back."')
    critical = [
        i
        for i in result["issues"]
        if i["kind"] == "DEAD_ALIVE" and i["severity"] == "CRITICAL"
    ]
    assert len(critical) == 1
    assert "Kael" in critical[0]["detail"]
    db.close()
