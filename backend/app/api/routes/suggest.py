from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.stories import _own_story
from app.db.session import get_db
from app.models.character import Character
from app.models.episode import Episode
from app.models.plot_thread import PlotThread
from app.models.user import User
from app.services import entity_extractor, payoff_detector, suggestion_engine

router = APIRouter()


@router.post("/{story_id}/suggest")
def suggest(
    story_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    story = _own_story(db, user.id, story_id)
    episodes = (
        db.query(Episode)
        .filter(Episode.story_id == story.id)
        .order_by(Episode.number)
        .all()
    )
    characters = db.query(Character).filter(Character.story_id == story.id).all()
    threads = db.query(PlotThread).filter(PlotThread.story_id == story.id).all()
    rules = list(getattr(story, "setting_rules", None) or [])
    max_ep = max((e.number for e in episodes), default=0)

    mentions = []
    for e in episodes:
        ex = entity_extractor.extract(e.text or "")
        for n in ex.get("names", []):
            mentions.append({"entity": n, "episode": e.number})
    active_titles = [t.title for t in threads if (t.status or "") == "active"]
    guns = payoff_detector.find_guns(mentions, max_ep, active_titles)

    char_last_seen: dict = {}
    for c in characters:
        last = 0
        for e in episodes:
            if c.name and c.name in (e.text or ""):
                last = max(last, e.number)
        char_last_seen[c.name] = last

    rules_refcounts: dict = {}
    for rule in rules:
        rules_refcounts[rule] = 0
    for e in episodes:
        ex = entity_extractor.extract(e.text or "", rules=rules)
        for hit in ex.get("rule_hits", []):
            rule = hit.get("rule")
            if rule in rules_refcounts:
                rules_refcounts[rule] += 1

    return suggestion_engine.suggest(
        {"guns": guns, "char_last_seen": char_last_seen, "rules_refcounts": rules_refcounts}
    )
