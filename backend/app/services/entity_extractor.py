import re

NAME_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b")
SPEAKER_RE = re.compile(
    r"\b([A-Z][a-z]+)\s+(?i:said|asked|replied|shouted|whispered)\b",
)
LOCATION_RE = re.compile(
    r"\b(?i:in|at|to|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
)
DEATH_CUE_RE = re.compile(
    r"\b(?i:died|dead|killed|murdered|death of|was killed|was murdered|is dead|is killed)\b",
)
CUE_BEFORE_NAME_RE = re.compile(
    r"\b(?i:died|dead|killed|murdered|death of)\b[^.?!]{0,60}?\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b",
)
NAME_BEFORE_CUE_RE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b[^.?!]{0,40}?\b(?i:died|was killed|was murdered|is dead|is killed)\b",
)

STOPLIST = {
    "The", "And", "But", "When", "Then", "There", "Here",
    "She", "He", "They", "We", "You", "It",
    "His", "Her", "Their", "Our", "Your", "My",
    "This", "That", "These", "Those",
    "What", "Where", "Who", "How", "Why",
    "Not", "No", "Yes",
    "Nobody", "Nothing", "Somebody", "Someone", "Something",
    "Everybody", "Everyone", "Everything", "Anybody", "Anyone", "Anything",
    "On", "In", "At", "Of", "To", "For", "With", "From", "As", "By", "An", "A",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
}

_KEYWORD_RE = re.compile(r"[a-z]{4,}")


def keywords(text: str) -> set:
    return set(_KEYWORD_RE.findall((text or "").lower()))


def _clean_name(raw: str) -> str | None:
    words = raw.strip().split()
    while words and words[0] in STOPLIST:
        words.pop(0)
    if not words:
        return None
    cleaned = " ".join(words)
    if cleaned in STOPLIST:
        return None
    if not re.fullmatch(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}", cleaned):
        return None
    return cleaned


def _split_sentences(text: str) -> list:
    parts = re.split(r"[.?!]+", text or "")
    return [p.strip() for p in parts if p.strip()]


def _unique(seq: list) -> list:
    seen = set()
    out = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def extract(text: str, known_names=None, rules=None, known_locations=None) -> dict:
    known_names = list(known_names or [])
    rules = list(rules or [])
    known_locations = list(known_locations or [])
    sentences = _split_sentences(text or "")

    names: list = []
    for sent in sentences:
        for m in NAME_RE.findall(sent):
            cleaned = _clean_name(m)
            if cleaned and cleaned not in names:
                names.append(cleaned)

    speakers = []
    for m in SPEAKER_RE.findall(text or ""):
        name = m[0] if isinstance(m, tuple) else m
        # SPEAKER_RE captures Name with IGNORECASE; enforce capitalised
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            continue
        if name in STOPLIST:
            continue
        if name not in speakers:
            speakers.append(name)

    deaths = []
    for sent in sentences:
        before = []
        for m in NAME_BEFORE_CUE_RE.findall(sent):
            raw = m[0] if isinstance(m, tuple) else m
            cleaned = _clean_name(raw)
            if cleaned and cleaned not in before:
                before.append(cleaned)
        if before:
            for d in before:
                if d not in deaths:
                    deaths.append(d)
            continue
        for m in CUE_BEFORE_NAME_RE.findall(sent):
            raw = m[1] if isinstance(m, tuple) else m
            cleaned = _clean_name(raw)
            if cleaned and cleaned not in deaths:
                deaths.append(cleaned)

    locations = []
    for m in LOCATION_RE.findall(text or ""):
        raw = m[1] if isinstance(m, tuple) else m
        cleaned = _clean_name(raw)
        if cleaned and cleaned not in locations:
            locations.append(cleaned)

    rule_hits = []
    for sent in sentences:
        sent_keys = keywords(sent)
        for rule in rules:
            if not rule:
                continue
            shared = sent_keys & keywords(rule)
            if len(shared) >= 2:
                rule_hits.append({"rule": rule, "sentence": sent})

    for kn in known_names:
        if kn and kn in (text or "") and kn not in names:
            names.append(kn)

    for kl in known_locations:
        if kl and kl in (text or "") and kl not in locations:
            locations.append(kl)

    return {
        "names": names,
        "speakers": speakers,
        "deaths": deaths,
        "locations": locations,
        "rule_hits": rule_hits,
        "sentences": sentences,
    }
