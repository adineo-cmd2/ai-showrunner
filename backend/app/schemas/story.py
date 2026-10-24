from pydantic import BaseModel


class StoryCreate(BaseModel):
    title: str
    genre: str = ""
    setting: str = ""
    rules: list[str] = []


class CharacterIn(BaseModel):
    name: str
    traits: str = ""
    backstory: str = ""
    status: str = "alive"
    arc: str = ""


class LocationIn(BaseModel):
    name: str
    description: str = ""


class EventIn(BaseModel):
    episode_no: int = 0
    label: str = ""
    detail: str = ""


class ThreadIn(BaseModel):
    title: str
    status: str = "active"
    last_seen: int = 0


class ThreadPatch(BaseModel):
    status: str


class ChangePatch(BaseModel):
    decision: str


class EpisodeIn(BaseModel):
    number: int
    title: str = ""
    text: str = ""


class EpisodeCheckIn(BaseModel):
    text: str = ""


class StoryOut(BaseModel):
    id: int
    title: str
    genre: str = ""
    setting: str = ""
    setting_rules: list[str] = []

    class Config:
        from_attributes = True
