"""Flask API for Player Service."""
from flask import Flask, request, jsonify
from player_service import PlayerService

app = Flask(__name__)


def get_service():
    return PlayerService()


# CRUD
@app.route('/api/players', methods=['GET'])
def get_players():
    service = get_service()
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        players = service.get_all_players(limit, offset)
        return jsonify([p.to_dict() for p in players])
    finally:
        service.close()


@app.route('/api/players/<player_id>', methods=['GET'])
def get_player(player_id):
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
    service = get_service()
    try:
        data = request.get_json()
        if not data or 'playerId' not in data:
            return jsonify({'error': 'playerId required'}), 400
        if service.get_player(data['playerId']):
            return jsonify({'error': 'Player exists'}), 409
        player = service.create_player(data)
        return jsonify(player.to_dict()), 201
    finally:
        service.close()


@app.route('/api/players/<player_id>', methods=['PUT'])
def update_player(player_id):
    service = get_service()
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Body required'}), 400
        player = service.update_player(player_id, data)
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        return jsonify(player.to_dict())
    finally:
        service.close()


@app.route('/api/players/<player_id>', methods=['DELETE'])
def delete_player(player_id):
    service = get_service()
    try:
        if service.delete_player(player_id):
            return jsonify({'message': 'Deleted'}), 200
        return jsonify({'error': 'Player not found'}), 404
    finally:
        service.close()


# QUERIES
@app.route('/api/players/search/country/<country>')
def search_by_country(country):
    service = get_service()
    try:
        return jsonify([p.to_dict() for p in service.search_by_country(country)])
    finally:
        service.close()


@app.route('/api/players/search/name/<name>')
def search_by_name(name):
    service = get_service()
    try:
        return jsonify([p.to_dict() for p in service.search_by_name(name)])
    finally:
        service.close()


@app.route('/api/players/search/year/<int:year>')
def search_by_year(year):
    service = get_service()
    try:
        return jsonify([p.to_dict() for p in service.search_by_birth_year(year)])
    finally:
        service.close()


@app.route('/api/players/search/year-range')
def search_by_year_range():
    service = get_service()
    try:
        start = request.args.get('start', type=int)
        end = request.args.get('end', type=int)
        if not start or not end:
            return jsonify({'error': 'start and end required'}), 400
        return jsonify([p.to_dict() for p in service.search_by_birth_year_range(start, end)])
    finally:
        service.close()


@app.route('/api/players/stats/count')
def get_count():
    service = get_service()
    try:
        return jsonify({'count': service.count_players()})
    finally:
        service.close()


@app.route('/api/players/stats/by-country')
def get_count_by_country():
    service = get_service()
    try:
        results = service.count_by_country()
        return jsonify([{'country': r[0], 'count': r[1]} for r in results])
    finally:
        service.close()


@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
