# Connect to SQLite database (creates it if it doesn't exist)
import sqlite3

class DB:
    def __init__(self):
        """
        Initialize the database connection and create the tables if they don't exist.
        The tables are `players`, `teams` and `scores`.
        """
        self.db_name = 'live_ticker.db'
        self._create_tables()

    def _create_tables(self):
        """Create the required tables if they do not exist."""
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    team_id INTEGER
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    double INTEGER,
                    team_name TEXT,
                    team_side TEXT,
                    player1 TEXT,
                    player2 TEXT,
                    player3 TEXT,
                    player4 TEXT,
                    player5 TEXT,
                    player6 TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    match_number INTEGER,
                    score_set INTEGER,
                    score_player TEXT,
                    score_opponent TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    match_number INTEGER,
                    server INTEGER
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    match_number INTEGER,
                    message TEXT
                )
            ''')
            conn.commit()

    def _fetchone(self, query, params=()):
        """Helper function to fetch a single result from the database."""
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

    def _fetchall(self, query, params=()):
        """Helper function to fetch all results from the database."""
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()


    def get_team_name(self, opponents=False):
        """
        Retrieve the team name for the current side (opponents or not)
        """
        team_side = 1 if opponents else 0
        query = "SELECT team_name FROM teams WHERE team_side = ? ORDER BY timestamp DESC LIMIT 1"
        team_name = self._fetchone(query, (team_side,))
        return team_name[0] if team_name else "team name"

    def set_players(self, team_name, players, opponents=False, double=False):
        """Save team information to the database."""
        is_double = int(double)
        team_side = int(opponents)
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            conn.execute('''
                INSERT INTO teams (double, team_side, team_name, player1, player2, player3, player4, player5, player6)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (is_double, team_side, team_name) + tuple(players))
            conn.commit()

    def get_players(self, opponents=False, double=False):
        """Get the players for a team."""
        val_double = int(double)
        team_side = int(opponents)
        players = self._fetchone(
            """SELECT player1, player2, player3, player4, player5, player6
               FROM teams WHERE team_side = ? AND double = ? ORDER BY timestamp DESC""",
            (team_side, val_double)
        )
        return players if players else ["player1", "player2", "player3", "player4", "player5", "player6"]

    def get_player_single(self, player_num):
        """
        Generic function to get entries for single players.
        """
        players = []
        query = f"SELECT player{player_num} FROM teams WHERE double = 0  AND team_side = 0 ORDER BY timestamp DESC"
        players.append(self._fetchone(query))
        query = f"SELECT player{player_num} FROM teams WHERE double = 0 AND team_side = 1 ORDER BY timestamp DESC"
        players.append(self._fetchone(query))
        players = players[:2] if len(players) >= 2 else [f"player{player_num}", f"player{player_num}"]
        return [p[0].split(",")[1].split("(")[0].strip() if "Wähle" not in p[0] else p[0] for p in players]

    def get_player_double(self, pair_num):
        """
        Generic function to get entries for double players.
        """

        start_player = (pair_num - 1) * 2 + 1
        end_player = start_player + 1
        doubles = []
        query = (f"SELECT player{start_player}, player{end_player} FROM teams WHERE double = 1 AND team_side = 0 ORDER "
                 f"BY timestamp DESC")
        doubles.append((self._fetchone(query)))

        query = (f"SELECT player{start_player}, player{end_player} FROM teams WHERE double = 1 AND team_side = 1 ORDER "
                 f"BY timestamp DESC")
        doubles.append((self._fetchone(query)))

        return doubles if len(doubles) == 2 else [
            (f"player{start_player}", f"player{end_player}"), (f"player{start_player}", f"player{end_player}")]

    # Wrapper methods for each single player (for easier access)
    def get_player_single_1(self):
        return self.get_player_single(1)

    def get_player_single_2(self):
        return self.get_player_single(2)

    def get_player_single_3(self):
        return self.get_player_single(3)

    def get_player_single_4(self):
        return self.get_player_single(4)

    def get_player_single_5(self):
        return self.get_player_single(5)

    def get_player_single_6(self):
        return self.get_player_single(6)

    # Wrapper methods for each double pair
    def get_player_double_1(self):
        return self.get_player_double(1)

    def get_player_double_2(self):
        return self.get_player_double(2)

    def get_player_double_3(self):
        return self.get_player_double(3)

    def set_scores(self, match_number, score_set, player_score, opponent_score):
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            conn.execute('''
                INSERT INTO scores (match_number, score_set, score_player, score_opponent)
                VALUES (?, ?, ?, ?)
            ''', (match_number, score_set, player_score, opponent_score))
            conn.commit()


    def set_scores_add_game(self, match_number, score_set, player_score, opponent_score, opponent=False):
        """Add a game to the database for the given match number and set.

        Args:
            match_number (int): The match number.
            score_set (int): The set number.
            player_score (str): The player's current score.
            opponent_score (str): The opponent's current score.
            opponent (bool, optional): Whether to increment the opponent's score. Defaults to False.
        """
        if opponent:
            opponent_score = str(int(opponent_score) + 1)
        else:
            player_score = str(int(player_score) + 1)
        with sqlite3.connect('live_ticker.db', check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scores (match_number, score_set, score_player, score_opponent)
                VALUES (?, ?, ?, ?)
            ''', (match_number, score_set, player_score, opponent_score))
            conn.commit()

    def set_scores_add_point(self, match_number, score_set, score_player, score_opponent):
        with sqlite3.connect('live_ticker.db', check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO scores (match_number, score_set, score_player, score_opponent)
                VALUES (?, ?, ?, ?)
            ''', (match_number, score_set, score_player, score_opponent))
            conn.commit()

    def get_points(self, match_number):
        with sqlite3.connect('live_ticker.db', check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT score_player, score_opponent
                FROM scores
                WHERE match_number = ? AND score_set = 0
                ORDER BY timestamp DESC
            ''', (match_number,))
            score = c.fetchone()
        if score is None:
            return "0", "0"
        return score

    def get_score_set1(self, match_number):
        with sqlite3.connect('live_ticker.db', check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute('''
                    SELECT score_player, score_opponent
                    FROM scores
                    WHERE match_number = ? AND score_set = 1
                    ORDER BY timestamp DESC
                ''', (match_number,))
            score = c.fetchone()
        if score is None:
            return "0", "0"
        return score

    def get_score_set2(self, match_number):
        with sqlite3.connect('live_ticker.db', check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT score_player, score_opponent
                FROM scores
                WHERE match_number = ? AND score_set = 2
                ORDER BY timestamp DESC
            ''', (match_number,))
            score = c.fetchone()
        if score is None:
            return "0", "0"
        return score

    def get_score_set3(self, match_number):
        with sqlite3.connect('live_ticker.db', check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT score_player, score_opponent
                FROM scores
                WHERE match_number = ? AND score_set = 3
                ORDER BY timestamp DESC
            ''', (match_number,))
            score = c.fetchone()
        if score is None:
            return "0", "0"
        return score

    def get_server(self, match_number):
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT server
                FROM servers
                WHERE match_number = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (match_number,))
            server = c.fetchone()
        if server is None:
            return -1
        return server[0]

    def set_server(self, match_number, server):
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO servers (match_number, server)
                VALUES (?, ?)
            ''', (match_number, server))
            conn.commit()

    def get_blog_entries(self):
        query = "SELECT timestamp, message FROM blog ORDER BY timestamp DESC"
        return self._fetchall(query)

    def add_blog_entry(self, match_number, message):
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO blog (match_number, message)
                VALUES (?, ?)
            ''', (match_number, message))
            conn.commit()
