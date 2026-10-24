# AI Showrunner for Serialized Fiction — backend

Run from `backend/`:

```bash
pip install -r requirements.txt
cp .env.example .env   # optional; works with no keys (rule-based engine)
python3 -m uvicorn app.main:app --port 8005
```

Tests: `python3 -m pytest tests/ -v` (11 tests).
