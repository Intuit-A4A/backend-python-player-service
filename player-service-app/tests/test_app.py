"""Tests for Player Service."""
import pytest
import json
from player_service import PlayerService, Base
from sqlalchemy import create_engine


# ==================== SERVICE TESTS ====================

@pytest.fixture
def service():
    """Create a PlayerService instance with in-memory database."""
    svc = PlayerService('sqlite:///:memory:')
    yield svc
    svc.close()


@pytest.fixture
def sample_player():
    """Sample player data."""
    return {
        'playerId': 'test001',
        'birthYear': 1990,
        'birthMonth': 5,
        'birthDay': 15,
        'birthCountry': 'USA',
        'birthState': 'CA',
        'birthCity': 'Los Angeles',
        'nameFirst': 'John',
        'nameLast': 'Doe',
        'nameGiven': 'John Michael Doe',
        'weight': 200,
        'height': 72,
        'bats': 'R',
        'throws': 'R'
    }


# CREATE Tests
def test_create_player(service, sample_player):
    """Test creating a new player."""
    player = service.create_player(sample_player)
    assert player.playerId == 'test001'
    assert player.nameFirst == 'John'


def test_create_player_minimal(service):
    """Test creating a player with minimal data."""
    player = service.create_player({'playerId': 'min001'})
    assert player.playerId == 'min001'


# READ Tests
def test_get_player(service, sample_player):
    """Test retrieving a player by ID."""
    service.create_player(sample_player)
    player = service.get_player('test001')
    assert player is not None
    assert player.nameLast == 'Doe'


def test_get_player_not_found(service):
    """Test retrieving a non-existent player."""
    assert service.get_player('nonexistent') is None


def test_get_all_players(service, sample_player):
    """Test retrieving all players with pagination."""
    service.create_player(sample_player)
    service.create_player({'playerId': 'test002', 'nameFirst': 'Jane'})
    players = service.get_all_players(limit=10)
    assert len(players) == 2


def test_get_all_players_pagination(service):
    """Test pagination works correctly."""
    for i in range(5):
        service.create_player({'playerId': f'page{i}'})
    assert len(service.get_all_players(limit=2, offset=0)) == 2
    assert len(service.get_all_players(limit=2, offset=2)) == 2


# UPDATE Tests
def test_update_player(service, sample_player):
    """Test updating an existing player."""
    service.create_player(sample_player)
    updated = service.update_player('test001', {'nameFirst': 'Johnny', 'weight': 210})
    assert updated.nameFirst == 'Johnny'
    assert updated.weight == 210
    assert updated.nameLast == 'Doe'


def test_update_player_not_found(service):
    """Test updating a non-existent player."""
    assert service.update_player('nonexistent', {'nameFirst': 'Nobody'}) is None


# DELETE Tests
def test_delete_player(service, sample_player):
    """Test deleting a player."""
    service.create_player(sample_player)
    assert service.delete_player('test001') is True
    assert service.get_player('test001') is None


def test_delete_player_not_found(service):
    """Test deleting a non-existent player."""
    assert service.delete_player('nonexistent') is False


# QUERY Tests
def test_search_by_country(service):
    """Test searching players by country."""
    service.create_player({'playerId': 'usa1', 'birthCountry': 'USA'})
    service.create_player({'playerId': 'usa2', 'birthCountry': 'USA'})
    service.create_player({'playerId': 'can1', 'birthCountry': 'Canada'})
    assert len(service.search_by_country('USA')) == 2


def test_search_by_name(service):
    """Test searching players by name."""
    service.create_player({'playerId': 'p1', 'nameFirst': 'Michael', 'nameLast': 'Jordan'})
    service.create_player({'playerId': 'p2', 'nameFirst': 'Mike', 'nameLast': 'Smith'})
    service.create_player({'playerId': 'p3', 'nameFirst': 'John', 'nameLast': 'Michaels'})
    assert len(service.search_by_name('Michael')) == 2


def test_search_by_birth_year(service):
    """Test searching players by birth year."""
    service.create_player({'playerId': 'p1', 'birthYear': 1990})
    service.create_player({'playerId': 'p2', 'birthYear': 1990})
    service.create_player({'playerId': 'p3', 'birthYear': 1985})
    assert len(service.search_by_birth_year(1990)) == 2


def test_search_by_birth_year_range(service):
    """Test searching players by birth year range."""
    service.create_player({'playerId': 'p1', 'birthYear': 1980})
    service.create_player({'playerId': 'p2', 'birthYear': 1985})
    service.create_player({'playerId': 'p3', 'birthYear': 1990})
    service.create_player({'playerId': 'p4', 'birthYear': 1995})
    assert len(service.search_by_birth_year_range(1985, 1990)) == 2


def test_count_players(service):
    """Test counting total players."""
    assert service.count_players() == 0
    service.create_player({'playerId': 'p1'})
    service.create_player({'playerId': 'p2'})
    assert service.count_players() == 2


def test_count_players_by_country(service):
    """Test counting players grouped by country."""
    service.create_player({'playerId': 'p1', 'birthCountry': 'USA'})
    service.create_player({'playerId': 'p2', 'birthCountry': 'USA'})
    service.create_player({'playerId': 'p3', 'birthCountry': 'Canada'})
    results = dict(service.count_players_by_country())
    assert results['USA'] == 2
    assert results['Canada'] == 1


# ==================== API TESTS ====================

@pytest.fixture
def client():
    """Create test client."""
    from app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    """Test health endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert json.loads(response.data)['status'] == 'healthy'


def test_get_players_api(client):
    """Test getting all players."""
    response = client.get('/api/players?limit=5')
    assert response.status_code == 200
    assert isinstance(json.loads(response.data), list)


def test_get_player_not_found_api(client):
    """Test getting non-existent player."""
    response = client.get('/api/players/nonexistent_xyz')
    assert response.status_code == 404


def test_create_player_api(client):
    """Test creating a new player."""
    data = {'playerId': 'apitest001', 'nameFirst': 'Test'}
    response = client.post('/api/players', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 201
    client.delete('/api/players/apitest001')


def test_create_player_missing_id_api(client):
    """Test creating player without ID fails."""
    response = client.post('/api/players', data=json.dumps({'nameFirst': 'NoId'}), content_type='application/json')
    assert response.status_code == 400


def test_update_player_api(client):
    """Test updating a player."""
    client.post('/api/players', data=json.dumps({'playerId': 'upd001'}), content_type='application/json')
    response = client.put('/api/players/upd001', data=json.dumps({'nameFirst': 'Updated'}), content_type='application/json')
    assert response.status_code == 200
    assert json.loads(response.data)['nameFirst'] == 'Updated'
    client.delete('/api/players/upd001')


def test_delete_player_api(client):
    """Test deleting a player."""
    client.post('/api/players', data=json.dumps({'playerId': 'del001'}), content_type='application/json')
    response = client.delete('/api/players/del001')
    assert response.status_code == 200


def test_search_by_country_api(client):
    """Test searching by country."""
    response = client.get('/api/players/search/country/USA')
    assert response.status_code == 200


def test_search_by_name_api(client):
    """Test searching by name."""
    response = client.get('/api/players/search/name/Aaron')
    assert response.status_code == 200


def test_get_count_api(client):
    """Test getting player count."""
    response = client.get('/api/players/stats/count')
    assert response.status_code == 200
    assert 'count' in json.loads(response.data)
