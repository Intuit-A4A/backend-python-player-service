import sqlite3

from app_paths import PLAYER_DB


class PlayerService:
    def __init__(self):
        conn = sqlite3.connect(PLAYER_DB)
        self.conn = conn
        self.cursor = conn.cursor()
        self.columns = self.get_columns()

    def get_all_players(self):

        query = "SELECT * FROM players"
        result = self.cursor.execute(query).fetchall()
        players = []
        for row in result:
            dic = self.convert_row_to_dict(row)
            players.append(dic)

        return players

    def search_by_player(self, player_id):

        query = "SELECT * FROM players WHERE playerId='{}'".format(player_id)
        result = self.cursor.execute(query).fetchall()

        for row in result:
            dic = self.convert_row_to_dict(row)
        return dic

    def search_by_country(self, birth_country):

        query = "SELECT * FROM players WHERE birthCountry='{}'".format(birth_country)
        result = self.cursor.execute(query).fetchall()

        return result

    def convert_row_to_dict(self, row):
        dic = {self.columns[i]: row[i] for i in range(len(row))}
        return dic

    def get_columns(self):
        self.cursor.execute("PRAGMA table_info(players)")
        columns = [column[1] for column in self.cursor.fetchall()]
        return columns
