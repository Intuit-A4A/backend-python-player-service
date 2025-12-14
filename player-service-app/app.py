"""Flask API for Player Service."""
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from player_service import PlayerService, Base
import pandas as pd

app = Flask(__name__)

# Database setup
engine = create_engine('sqlite:///player.db', echo=False)
Base.metadata.create_all(engine)


def get_service():
    """Get a new service instance."""
    return PlayerService()


def load_csv_data():
    """Load initial data from CSV if database is empty."""
    service = get_service()
    if service.count_players() == 0:
        df = pd.read_csv('Player.csv')
        columns = ['playerId', 'birthYear', 'birthMonth', 'birthDay', 'birthCountry',
                   'birthState', 'birthCity', 'nameFirst', 'nameLast', 'nameGiven',
                   'weight', 'height', 'bats', 'throws']
        df = df[columns]
        df.to_sql('players', con=engine, if_exists='replace', index=False)
    service.close()


# ==================== CRUD ENDPOINTS ====================

@app.route('/api/players', methods=['GET'])
def get_players():
    """Get all players with optional pagination."""
    service = get_service()
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        players = service.get_all_players(limit=limit, offset=offset)
        return jsonify([p.to_dict() for p in players])
    finally:
        service.close()


@app.route('/api/players/<player_id>', methods=['GET'])
def get_player(player_id):
    """Get a single player by ID."""
    service = get_service()
    try:
        player = service.get_player(player_id)
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        return jsonify(player.to_dict())
    finally:
        service.close()


@app.route('/api/players', methods=['POST'])
def create_player():
    """Create a new player."""
    service = get_service()
    try:
        data = request.get_json()
        if not data or 'playerId' not in data:
            return jsonify({'error': 'playerId is required'}), 400
        if service.get_player(data['playerId']):
            return jsonify({'error': 'Player already exists'}), 409
        player = service.create_player(data)
        return jsonify(player.to_dict()), 201
    finally:
        service.close()


@app.route('/api/players/<player_id>', methods=['PUT'])
def update_player(player_id):
    """Update an existing player."""
    service = get_service()
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        player = service.update_player(player_id, data)
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        return jsonify(player.to_dict())
    finally:
        service.close()


@app.route('/api/players/<player_id>', methods=['DELETE'])
def delete_player(player_id):
    """Delete a player."""
    service = get_service()
    try:
        if service.delete_player(player_id):
            return jsonify({'message': 'Player deleted'}), 200
        return jsonify({'error': 'Player not found'}), 404
    finally:
        service.close()


# ==================== QUERY ENDPOINTS ====================

@app.route('/api/players/search/country/<country>', methods=['GET'])
def search_by_country(country):
    """Find players by birth country."""
    service = get_service()
    try:
        players = service.search_by_country(country)
        return jsonify([p.to_dict() for p in players])
    finally:
        service.close()


@app.route('/api/players/search/name/<name>', methods=['GET'])
def search_by_name(name):
    """Find players by name (partial match)."""
    service = get_service()
    try:
        players = service.search_by_name(name)
        return jsonify([p.to_dict() for p in players])
    finally:
        service.close()


@app.route('/api/players/search/year/<int:year>', methods=['GET'])
def search_by_year(year):
    """Find players born in a specific year."""
    service = get_service()
    try:
        players = service.search_by_birth_year(year)
        return jsonify([p.to_dict() for p in players])
    finally:
        service.close()


@app.route('/api/players/search/year-range', methods=['GET'])
def search_by_year_range():
    """Find players born between two years."""
    service = get_service()
    try:
        start = request.args.get('start', type=int)
        end = request.args.get('end', type=int)
        if not start or not end:
            return jsonify({'error': 'start and end query params required'}), 400
        players = service.search_by_birth_year_range(start, end)
        return jsonify([p.to_dict() for p in players])
    finally:
        service.close()


@app.route('/api/players/stats/count', methods=['GET'])
def get_count():
    """Get total player count."""
    service = get_service()
    try:
        return jsonify({'count': service.count_players()})
    finally:
        service.close()


@app.route('/api/players/stats/by-country', methods=['GET'])
def get_count_by_country():
    """Get player count by country."""
    service = get_service()
    try:
        results = service.count_players_by_country()
        return jsonify([{'country': r[0], 'count': r[1]} for r in results])
    finally:
        service.close()


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    load_csv_data()
    app.run(host='0.0.0.0', port=8000, debug=True)
