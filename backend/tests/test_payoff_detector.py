from app.services import payoff_detector


def test_single_mention_old_entity_is_gun():
    mentions = [{"entity": "Amulet", "episode": 1}]
    guns = payoff_detector.find_guns(mentions, 4)
    assert len(guns) == 1
    assert guns[0]["entity"] == "Amulet"
    assert guns[0]["first_seen"] == 1


def test_rementioned_entity_is_not_gun():
    mentions = [
        {"entity": "Amulet", "episode": 1},
        {"entity": "Amulet", "episode": 3},
    ]
    guns = payoff_detector.find_guns(mentions, 4)
    assert guns == []


def test_gun_filter_keeps_only_active_threads():
    mentions = [{"entity": "Amulet", "episode": 1}]
    guns = payoff_detector.find_guns(mentions, 4, ["Amulet"])
    assert len(guns) == 1
    assert guns[0]["entity"] == "Amulet"


def test_gun_filter_drops_inactive_entities():
    mentions = [{"entity": "Amulet", "episode": 1}]
    guns = payoff_detector.find_guns(mentions, 4, ["Other Thread"])
    assert guns == []


def test_gun_filter_matches_substring_of_title():
    mentions = [{"entity": "Mara", "episode": 1}]
    guns = payoff_detector.find_guns(mentions, 4, ["Mara's debt"])
    assert len(guns) == 1
    assert guns[0]["entity"] == "Mara"
