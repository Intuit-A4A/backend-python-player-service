"""Tests for Player Service."""
import pytest
import json
from player_service import PlayerService


@pytest.fixture
def service():
    svc = PlayerService('sqlite:///:memory:', create_tables=True)
    yield svc
    svc.close()


@pytest.fixture
def sample_player():
    return {'playerId': 'test001', 'nameFirst': 'John', 'nameLast': 'Doe', 'birthYear': 1990, 'birthCountry': 'USA'}


# CREATE
def test_create_player(service, sample_player):
    player = service.create_player(sample_player)
    assert player.playerId == 'test001'
    assert player.nameFirst == 'John'


# READ
def test_get_player(service, sample_player):
    service.create_player(sample_player)
    player = service.get_player('test001')
    assert player.nameLast == 'Doe'


def test_get_player_not_found(service):
    assert service.get_player('xxx') is None


def test_get_all_players(service, sample_player):
    service.create_player(sample_player)
    service.create_player({'playerId': 'test002'})
    assert len(service.get_all_players()) == 2


def test_pagination(service):
    for i in range(5):
        service.create_player({'playerId': f'p{i}'})
    assert len(service.get_all_players(limit=2)) == 2
    assert len(service.get_all_players(limit=2, offset=3)) == 2


# UPDATE
def test_update_player(service, sample_player):
    service.create_player(sample_player)
    updated = service.update_player('test001', {'nameFirst': 'Johnny'})
    assert updated.nameFirst == 'Johnny'
    assert updated.nameLast == 'Doe'


def test_update_not_found(service):
    assert service.update_player('xxx', {'nameFirst': 'X'}) is None


# DELETE
def test_delete_player(service, sample_player):
    service.create_player(sample_player)
    assert service.delete_player('test001') is True
    assert service.get_player('test001') is None


def test_delete_not_found(service):
    assert service.delete_player('xxx') is False


# QUERIES
def test_search_by_country(service):
    service.create_player({'playerId': 'p1', 'birthCountry': 'USA'})
    service.create_player({'playerId': 'p2', 'birthCountry': 'USA'})
    service.create_player({'playerId': 'p3', 'birthCountry': 'Canada'})
    assert len(service.search_by_country('USA')) == 2


def test_search_by_name(service):
    service.create_player({'playerId': 'p1', 'nameFirst': 'Michael'})
    service.create_player({'playerId': 'p2', 'nameLast': 'Michaels'})
    assert len(service.search_by_name('Michael')) == 2


def test_search_by_year(service):
    service.create_player({'playerId': 'p1', 'birthYear': 1990})
    service.create_player({'playerId': 'p2', 'birthYear': 1990})
    assert len(service.search_by_birth_year(1990)) == 2


def test_search_by_year_range(service):
    service.create_player({'playerId': 'p1', 'birthYear': 1985})
    service.create_player({'playerId': 'p2', 'birthYear': 1990})
    service.create_player({'playerId': 'p3', 'birthYear': 1995})
    assert len(service.search_by_birth_year_range(1985, 1990)) == 2


def test_count(service):
    assert service.count_players() == 0
    service.create_player({'playerId': 'p1'})
    assert service.count_players() == 1


def test_count_by_country(service):
    service.create_player({'playerId': 'p1', 'birthCountry': 'USA'})
    service.create_player({'playerId': 'p2', 'birthCountry': 'USA'})
    results = dict(service.count_by_country())
    assert results['USA'] == 2


# API TESTS
@pytest.fixture
def client():
    from app import app
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    r = client.get('/api/health')
    assert r.status_code == 200


def test_get_players_api(client):
    r = client.get('/api/players?limit=5')
    assert r.status_code == 200


def test_crud_api(client):
    # Create
    r = client.post('/api/players', json={'playerId': 'api001', 'nameFirst': 'Test'})
    assert r.status_code == 201
    # Read
    r = client.get('/api/players/api001')
    assert r.status_code == 200
    # Update
    r = client.put('/api/players/api001', json={'nameFirst': 'Updated'})
    assert r.status_code == 200
    assert json.loads(r.data)['nameFirst'] == 'Updated'
    # Delete
    r = client.delete('/api/players/api001')
    assert r.status_code == 200


def test_not_found_api(client):
    assert client.get('/api/players/xxx').status_code == 404
    assert client.put('/api/players/xxx', json={'x': 1}).status_code == 404
    assert client.delete('/api/players/xxx').status_code == 404


def test_search_api(client):
    assert client.get('/api/players/search/country/USA').status_code == 200
    assert client.get('/api/players/search/name/Aaron').status_code == 200
    assert client.get('/api/players/search/year/1990').status_code == 200
    assert client.get('/api/players/search/year-range?start=1980&end=1990').status_code == 200


def test_stats_api(client):
    assert client.get('/api/players/stats/count').status_code == 200
    assert client.get('/api/players/stats/by-country').status_code == 200
