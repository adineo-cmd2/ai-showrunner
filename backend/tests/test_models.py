from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.bible_change import BibleChange
from app.models.character import Character
from app.models.consistency_issue import ConsistencyIssue
from app.models.episode import Episode
from app.models.location import Location
from app.models.plot_thread import PlotThread
from app.models.story import Story
from app.models.timeline_event import TimelineEvent
from app.models.user import User


def test_story_character_episode_issue_link():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    u = User(email="showrunner@example.com", password_hash=hash_password("secret123"))
    db.add(u)
    db.commit()
    db.refresh(u)

    story = Story(
        user_id=u.id,
        title="The Long Night",
        genre="drama",
        setting="A coastal town",
        setting_rules=["No magic without cost"],
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    assert story.user_id == u.id
    assert story.setting_rules == ["No magic without cost"]

    char = Character(
        story_id=story.id,
        name="Mara",
        traits="stubborn",
        backstory="Grew up by the sea",
        status="alive",
        arc="hero",
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    assert char.story_id == story.id
    assert char.status == "alive"

    loc = Location(story_id=story.id, name="Harbor", description="Foggy docks")
    db.add(loc)
    db.commit()
    db.refresh(loc)
    assert loc.story_id == story.id

    ev = TimelineEvent(story_id=story.id, episode_no=1, label="Arrival", detail="Mara arrives")
    db.add(ev)
    db.commit()
    db.refresh(ev)
    assert ev.episode_no == 1

    thread = PlotThread(story_id=story.id, title="Mara's debt", status="active", last_seen=0)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    assert thread.status == "active"
    assert thread.last_seen == 0

    ep = Episode(story_id=story.id, number=1, title="Pilot", text="Mara said hello at the harbor.")
    db.add(ep)
    db.commit()
    db.refresh(ep)
    assert ep.story_id == story.id

    issue = ConsistencyIssue(
        story_id=story.id,
        episode_id=ep.id,
        severity="CRITICAL",
        kind="DEAD_ALIVE",
        detail="Mara speaks after death",
        passage="Mara said hello",
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    assert issue.story_id == story.id
    assert issue.episode_id == ep.id
    assert issue.severity == "CRITICAL"

    change = BibleChange(
        story_id=story.id,
        episode_id=ep.id,
        action="add_character",
        payload={"name": "Mara"},
        status="pending",
    )
    db.add(change)
    db.commit()
    db.refresh(change)
    assert change.status == "pending"

    db.close()
