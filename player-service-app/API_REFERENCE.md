# Player Service API Reference

## Quick Start

```bash
# Activate virtual environment
source env/bin/activate

# Run the service
python app_clean.py

# Run tests
python -m pytest tests/ -v
```

## Endpoints

### CRUD Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/players` | Get all players (supports `?limit=N&offset=N`) |
| GET | `/api/players/<player_id>` | Get player by ID |
| POST | `/api/players` | Create new player |
| PUT | `/api/players/<player_id>` | Update player |
| DELETE | `/api/players/<player_id>` | Delete player |

### Search/Query Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/players/search/country/<country>` | Find by birth country |
| GET | `/api/players/search/name/<name>` | Find by name (partial match) |
| GET | `/api/players/search/year/<year>` | Find by birth year |
| GET | `/api/players/search/year-range?start=X&end=Y` | Find by birth year range |

### Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/players/stats/count` | Total player count |
| GET | `/api/players/stats/by-country` | Count grouped by country |
| GET | `/api/health` | Health check |

## Example Requests

```bash
# Get all players (paginated)
curl 'http://localhost:8000/api/players?limit=10&offset=0'

# Get single player
curl 'http://localhost:8000/api/players/aaronha01'

# Create player
curl -X POST 'http://localhost:8000/api/players' \
  -H 'Content-Type: application/json' \
  -d '{"playerId":"new001","nameFirst":"John","nameLast":"Doe"}'

# Update player
curl -X PUT 'http://localhost:8000/api/players/new001' \
  -H 'Content-Type: application/json' \
  -d '{"nameFirst":"Johnny"}'

# Delete player
curl -X DELETE 'http://localhost:8000/api/players/new001'

# Search by name
curl 'http://localhost:8000/api/players/search/name/Aaron'

# Search by year range
curl 'http://localhost:8000/api/players/search/year-range?start=1980&end=1990'
```

## Architecture

```
player-service-app/
├── models.py       # SQLAlchemy ORM models
├── service.py      # Business logic (CRUD + queries)
├── app_clean.py    # Flask REST API endpoints
└── tests/
    ├── test_service.py  # Unit tests for service layer
    └── test_api.py      # Integration tests for API
```

## Key SQLAlchemy Features Used

- **ORM Mapping**: `Player` class maps to `players` table
- **Session Management**: Proper session handling with cleanup
- **Query Methods**: 
  - `filter()` - WHERE clause
  - `ilike()` - Case-insensitive LIKE
  - `offset()` / `limit()` - Pagination
  - `func.count()` - Aggregation
  - `group_by()` - Grouping

