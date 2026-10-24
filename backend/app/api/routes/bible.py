from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.stories import _own_story
from app.db.session import get_db
from app.models.bible_change import BibleChange
from app.models.character import Character
from app.models.location import Location
from app.models.plot_thread import PlotThread
from app.models.story import Story
from app.models.timeline_event import TimelineEvent
from app.models.user import User
from app.schemas.story import CharacterIn, ChangePatch, EventIn, LocationIn, ThreadIn, ThreadPatch

router = APIRouter()

_VALID_THREAD_STATUS = {"active", "dormant", "resolved"}


@router.post("/{story_id}/characters")
def add_character(
    story_id: int,
    body: CharacterIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    story = _own_story(db, user.id, story_id)
    char = Character(
        story_id=story.id,
        name=body.name,
        traits=body.traits or "",
        backstory=body.backstory or "",
        status=body.status or "alive",
        arc=body.arc or "",
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    return {"id": char.id, "name": char.name, "status": char.status}


@router.post("/{story_id}/locations")
def add_location(
    story_id: int,
    body: LocationIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    story = _own_story(db, user.id, story_id)
    loc = Location(story_id=story.id, name=body.name, description=body.description or "")
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return {"id": loc.id, "name": loc.name}


@router.post("/{story_id}/events")
def add_event(
    story_id: int,
    body: EventIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    story = _own_story(db, user.id, story_id)
    ev = TimelineEvent(
        story_id=story.id,
        episode_no=body.episode_no or 0,
        label=body.label or "",
        detail=body.detail or "",
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return {"id": ev.id}


@router.post("/{story_id}/threads")
def add_thread(
    story_id: int,
    body: ThreadIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    story = _own_story(db, user.id, story_id)
    status = body.status or "active"
    if status not in _VALID_THREAD_STATUS:
        raise HTTPException(status_code=400, detail="bad status")
    thread = PlotThread(
        story_id=story.id,
        title=body.title,
        status=status,
        last_seen=body.last_seen or 0,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return {"id": thread.id, "title": thread.title, "status": thread.status}


def _own_thread(db: Session, user_id: int, tid: int) -> PlotThread:
    thread = db.query(PlotThread).filter(PlotThread.id == tid).first()
    if thread is None:
        raise HTTPException(status_code=404, detail="thread not found")
    story = (
        db.query(Story)
        .filter(Story.id == thread.story_id, Story.user_id == user_id)
        .first()
    )
    if story is None:
        raise HTTPException(status_code=404, detail="thread not found")
    return thread


def _own_change(db: Session, user_id: int, cid: int) -> BibleChange:
    change = db.query(BibleChange).filter(BibleChange.id == cid).first()
    if change is None:
        raise HTTPException(status_code=404, detail="change not found")
    story = (
        db.query(Story)
        .filter(Story.id == change.story_id, Story.user_id == user_id)
        .first()
    )
    if story is None:
        raise HTTPException(status_code=404, detail="change not found")
    return change


@router.patch("/threads/{tid}")
def patch_thread(
    tid: int,
    body: ThreadPatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.status not in _VALID_THREAD_STATUS:
        raise HTTPException(status_code=400, detail="bad status")
    thread = _own_thread(db, user.id, tid)
    thread.status = body.status
    db.commit()
    db.refresh(thread)
    return {"id": thread.id, "status": thread.status}


@router.patch("/changes/{cid}")
def patch_change(
    cid: int,
    body: ChangePatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.decision not in ("confirm", "reject"):
        raise HTTPException(status_code=400, detail="bad decision")
    change = _own_change(db, user.id, cid)
    if body.decision == "reject":
        change.status = "rejected"
        db.commit()
        db.refresh(change)
        return {"id": change.id, "status": change.status}
    # confirm: materialise per ruling 4
    if change.action == "confirm_dead":
        name = (change.payload or {}).get("name") if isinstance(change.payload, dict) else None
        if name:
            char = (
                db.query(Character)
                .filter(
                    Character.story_id == change.story_id,
                    Character.name == name,
                )
                .first()
            )
            if char is None:
                char = Character(
                    story_id=change.story_id,
                    name=name,
                    traits="",
                    backstory="",
                    status="dead",
                    arc="",
                )
                db.add(char)
            else:
                char.status = "dead"
        change.status = "confirmed"
    elif change.action in ("add_character", "add_location"):
        # shells already confirmed in pipeline; just mark confirmed
        change.status = "confirmed"
    else:
        change.status = "confirmed"
    db.commit()
    db.refresh(change)
    return {"id": change.id, "status": change.status}
