import re

from app.services import entity_extractor

FLIP_CUES = {"not", "never", "no", "n't", "cannot", "can't", "but", "however"}

_SEVERITIES = {"CRITICAL", "WARNING", "MINOR"}


def _has_flip(text: str) -> bool:
    low = (text or "").lower()
    if "n't" in low:
        return True
    words = set(re.findall(r"[a-z']+", low))
    return bool(words & FLIP_CUES)


def _actors_in_sentence(sentence: str, names: list, speakers: list) -> set:
    actors = set()
    for sp in speakers:
        if re.search(rf"\b{re.escape(sp)}\b", sentence):
            actors.add(sp)
    for name in names:
        # subject-before-verb heuristic: Name followed by a lowercase word
        if re.search(rf"\b{re.escape(name)}\b\s+[a-z]{{2,}}\b", sentence):
            actors.add(name)
    return actors


def check(episode_text: str, episode_no: int, bible: dict) -> list:
    bible = bible or {}
    deaths = list(bible.get("deaths") or [])
    rules = list(bible.get("rules") or [])
    facts = list(bible.get("facts") or [])

    extracted = entity_extractor.extract(episode_text or "")
    sentences = extracted.get("sentences", [])
    names = extracted.get("names", [])
    speakers = extracted.get("speakers", [])

    issues = []

    for sent in sentences:
        actors = _actors_in_sentence(sent, names, speakers)
        for actor in actors:
            if actor in deaths:
                issues.append(
                    {
                        "severity": "CRITICAL",
                        "kind": "DEAD_ALIVE",
                        "detail": f"{actor} acts after recorded death",
                        "passage": sent[:300],
                    }
                )
        # avoid duplicate DEAD_ALIVE for same sentence+actor handled above

    # de-duplicate DEAD_ALIVE by (detail, passage)
    seen = set()
    deduped = []
    for iss in issues:
        key = (iss["kind"], iss["detail"], iss["passage"])
        if key not in seen:
            seen.add(key)
            deduped.append(iss)
    issues = deduped

    for sent in sentences:
        sent_keys = entity_extractor.keywords(sent)
        sent_flip = _has_flip(sent)
        for rule in rules:
            if not rule:
                continue
            shared = sent_keys & entity_extractor.keywords(rule)
            if len(shared) >= 2 and (sent_flip != _has_flip(rule)):
                issues.append(
                    {
                        "severity": "WARNING",
                        "kind": "RULE_BREAK",
                        "detail": f"Possible break of rule '{rule}'",
                        "passage": sent[:300],
                    }
                )
        for fact in facts:
            if isinstance(fact, dict):
                subject = fact.get("subject", "")
                ftext = fact.get("text", "")
            else:
                subject = str(fact)
                ftext = str(fact)
            if not ftext:
                continue
            shared = sent_keys & entity_extractor.keywords(ftext)
            if len(shared) >= 2 and (sent_flip != _has_flip(ftext)):
                issues.append(
                    {
                        "severity": "WARNING",
                        "kind": "CONTRADICTION",
                        "detail": f"Contradicts established fact about {subject}",
                        "passage": sent[:300],
                    }
                )

    for iss in issues:
        assert iss["severity"] in _SEVERITIES, iss["severity"]
    return issues
