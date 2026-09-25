import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_get_players_returns_data(client):
    response = client.get("/v1/players")
    assert response.status_code == 200
    players = response.get_json()
    assert isinstance(players, list)
    assert len(players) > 0
    assert "playerId" in players[0]
