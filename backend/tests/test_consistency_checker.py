from app.services import consistency_checker


def test_dead_alive_critical():
    bible = {"deaths": ["Kael"], "rules": [], "facts": []}
    issues = consistency_checker.check('Kael said "I am back."', 2, bible)
    assert len(issues) == 1
    assert issues[0]["severity"] == "CRITICAL"
    assert issues[0]["kind"] == "DEAD_ALIVE"
    assert "Kael" in issues[0]["detail"]


def test_clean_text_no_issues():
    bible = {"deaths": ["Kael"], "rules": ["Magic always has a cost"], "facts": []}
    issues = consistency_checker.check("Mara walked to the harbor.", 2, bible)
    assert issues == []
