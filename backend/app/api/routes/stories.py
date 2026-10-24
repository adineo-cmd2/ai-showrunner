from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.bible_change import BibleChange
from app.models.character import Character
from app.models.consistency_issue import ConsistencyIssue
from app.models.episode import Episode
from app.models.location import Location
from app.models.plot_thread import PlotThread
from app.models.story import Story
from app.models.timeline_event import TimelineEvent
from app.models.user import User
from app.schemas.story import StoryCreate

router = APIRouter()


def _own_story(db: Session, user_id: int, story_id: int) -> Story:
    story = (
        db.query(Story)
        .filter(Story.id == story_id, Story.user_id == user_id)
        .first()
    )
    if story is None:
        raise HTTPException(status_code=404, detail="story not found")
    return story


@router.post("/bible")
def create_bible(
    body: StoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    story = Story(
        user_id=user.id,
        title=body.title,
        genre=body.genre or "",
        setting=body.setting or "",
        setting_rules=list(body.rules or []),
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    return {"story_id": story.id}


@router.get("/bible/{story_id}/full")
def full_bible(
    story_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    story = _own_story(db, user.id, story_id)
    characters = (
        db.query(Character).filter(Character.story_id == story.id).order_by(Character.id).all()
    )
    locations = (
        db.query(Location).filter(Location.story_id == story.id).order_by(Location.id).all()
    )
    events = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.story_id == story.id)
        .order_by(TimelineEvent.id)
        .all()
    )
    threads = (
        db.query(PlotThread)
        .filter(PlotThread.story_id == story.id)
        .order_by(PlotThread.id)
        .all()
    )
    episodes = (
        db.query(Episode).filter(Episode.story_id == story.id).order_by(Episode.number).all()
    )
    pending = (
        db.query(BibleChange)
        .filter(BibleChange.story_id == story.id, BibleChange.status == "pending")
        .order_by(BibleChange.id)
        .all()
    )
    return {
        "story": {
            "id": story.id,
            "title": story.title,
            "genre": story.genre,
            "setting": story.setting,
            "setting_rules": list(story.setting_rules or []),
        },
        "characters": [
            {
                "id": c.id,
                "name": c.name,
                "traits": c.traits,
                "backstory": c.backstory,
                "status": c.status,
                "arc": c.arc,
            }
            for c in characters
        ],
        "locations": [
            {"id": loc.id, "name": loc.name, "description": loc.description}
            for loc in locations
        ],
        "events": [
            {"id": e.id, "episode_no": e.episode_no, "label": e.label, "detail": e.detail}
            for e in events
        ],
        "threads": [
            {"id": t.id, "title": t.title, "status": t.status, "last_seen": t.last_seen}
            for t in threads
        ],
        "episodes": [
            {"id": e.id, "number": e.number, "title": e.title, "text": e.text}
            for e in episodes
        ],
        "pending_changes": [
            {
                "id": p.id,
                "action": p.action,
                "payload": p.payload,
                "status": p.status,
                "episode_id": p.episode_id,
            }
            for p in pending
        ],
    }


@router.delete("/{story_id}")
def delete_story(
    story_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    story = _own_story(db, user.id, story_id)
    db.query(ConsistencyIssue).filter(ConsistencyIssue.story_id == story.id).delete(
        synchronize_session=False
    )
    db.query(BibleChange).filter(BibleChange.story_id == story.id).delete(
        synchronize_session=False
    )
    db.query(Episode).filter(Episode.story_id == story.id).delete(
        synchronize_session=False
    )
    db.query(PlotThread).filter(PlotThread.story_id == story.id).delete(
        synchronize_session=False
    )
    db.query(TimelineEvent).filter(TimelineEvent.story_id == story.id).delete(
        synchronize_session=False
    )
    db.query(Location).filter(Location.story_id == story.id).delete(
        synchronize_session=False
    )
    db.query(Character).filter(Character.story_id == story.id).delete(
        synchronize_session=False
    )
    db.delete(story)
    db.commit()
    return {"ok": True}
