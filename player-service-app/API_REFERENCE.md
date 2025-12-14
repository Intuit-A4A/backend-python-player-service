# Player Service API

```bash
python app.py                   # Run on port 8000
python -m pytest tests/ -v      # Run tests (21 tests)
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/players?limit=N&offset=N` | List players |
| GET | `/api/players/<id>` | Get player |
| POST | `/api/players` | Create player |
| PUT | `/api/players/<id>` | Update player |
| DELETE | `/api/players/<id>` | Delete player |
| GET | `/api/players/search/country/<country>` | By country |
| GET | `/api/players/search/name/<name>` | By name |
| GET | `/api/players/search/year/<year>` | By year |
| GET | `/api/players/search/year-range?start=X&end=Y` | By year range |
| GET | `/api/players/stats/count` | Total count |
| GET | `/api/players/stats/by-country` | Count by country |

## Files

- `app.py` - Flask API
- `player_service.py` - SQLAlchemy model + service
- `tests/test_app.py` - Tests
