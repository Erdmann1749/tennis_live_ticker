from dataflow import DB
import math


def process_player_to_doubles(players):
    players_only_name = [p.split('(')[0].strip() for p in players]
    return [("/".join(players_only_name[i:i + 2])) for i in range(0, 5, 2)]


def tennis_point_logic(current_points, opponent_points, opponent_scored=False, third_set=False, tie_break=False):
    if opponent_scored:
        current_points, opponent_points = opponent_points, current_points

    if tie_break:
        if int(current_points) > 5 and int(current_points) - int(opponent_points) > 0:
            new_points = "Win"
        else:
            new_points = str(int(current_points) + 1)
    elif third_set:
        if int(current_points) > 8 and int(current_points) - int(opponent_points) > 0:
            new_points = "Win"
        else:
            new_points = str(int(current_points) + 1)
    else:
        if current_points == "Advantage":
            current_points = "50"
        if opponent_points == "Advantage":
            opponent_points = "50"
        if current_points == "0":
            new_points = "15"
        elif current_points == "15":
            new_points = "30"
        elif current_points == "30":
            new_points = "40"
        elif current_points == "40" and int(opponent_points) < 40:
            new_points = "Win"
        elif current_points == "40" and opponent_points == "40":
            new_points = "Advantage"
        elif current_points == "40" and int(opponent_points) > 40:
            new_points = "Duece"
        elif current_points == "50":
            new_points = "Win"
        else:  # For cases where opponent is at Advantage and current player wins point
            new_points = "40"

    if opponent_scored:
        return opponent_points, new_points
    else:
        return new_points, opponent_points


class Score:
    def __init__(self, db: DB):
        self._db = db

    def reset_scores(self, match_number):
        self._db.set_scores(match_number, 0, 0, 0)
        self._db.set_scores(match_number, 1, 0, 0)
        self._db.set_scores(match_number, 2, 0, 0)
        self._db.set_scores(match_number, 3, 0, 0)
        self._db.set_server(match_number, -1)

    def get_scores_specific_match(self, match_index):
        scores = self._db.get_points(match_index)
        set_1 = self._db.get_score_set1(match_index)
        set_2 = self._db.get_score_set2(match_index)
        set_3 = self._db.get_score_set3(match_index)
        return scores, set_1, set_2, set_3

    def get_all_single_scores(self):
        points = [self._db.get_points(match) for match in range(6)]
        first_set = [self._db.get_score_set1(match) for match in range(6)]
        second_set = [self._db.get_score_set2(match) for match in range(6)]
        third_set = [self._db.get_score_set3(match) for match in range(6)]
        all_scores = [points, first_set, second_set, third_set]
        return [list(row) for row in zip(*all_scores)]

    def get_all_double_scores(self):
        points = [self._db.get_points(match) for match in range(6, 9)]
        first_set = [self._db.get_score_set1(match) for match in range(6, 9)]
        second_set = [self._db.get_score_set2(match) for match in range(6, 9)]
        third_set = [self._db.get_score_set3(match) for match in range(6, 9)]
        all_scores = [points, first_set, second_set, third_set]
        return [list(row) for row in zip(*all_scores)]

    def add_opponent_game(self, match_index):
        current_set, _, player_score, opponent_score, _, _ = self._match_specifics(match_index)
        self._db.set_scores(match_index, current_set + 1, player_score, str(int(opponent_score) + 1))
        self._db.set_scores(match_index, 0, 0, 0)

    def add_team_game(self, match_index):
        current_set, _, player_score, opponent_score, _, _ = self._match_specifics(match_index)
        self._db.set_scores(match_index, current_set + 1, str(int(player_score) + 1), opponent_score)
        self._db.set_scores(match_index, 0, 0, 0)

    def add_opponent_point(self, match_index):
        (current_set, is_third_set, player_score, opponent_score, player_points,
         opponent_points) = self._match_specifics(match_index)
        if is_third_set:
            self.add_opponent_game(match_index)
        else:
            is_tie_break = int(player_score) == 6 and int(opponent_score) == 6
            player_points, opponent_points = tennis_point_logic(player_points, opponent_points,
                                                                tie_break=is_tie_break, opponent_scored=True)
            if opponent_points == "Win":
                self.add_opponent_game(match_index)
                self._db.set_scores(match_index, 0, 0, 0)
            elif opponent_points == "Duece":
                self._db.set_scores(match_index, 0, 40, 40)
            else:
                self._db.set_scores(match_index, 0, player_points, opponent_points)

    def add_team_point(self, match_index):
        (current_set, is_third_set, player_score, opponent_score, player_points,
         opponent_points) = self._match_specifics(match_index)
        if is_third_set:
            self.add_team_game(match_index)
        else:
            print(player_score, opponent_score)
            is_tie_break = int(player_score) == 6 and int(opponent_score) == 6
            print("is_tie_break", is_tie_break)
            player_points, opponent_points = tennis_point_logic(
                player_points, opponent_points, tie_break=is_tie_break, opponent_scored=False)
            print(player_points, opponent_points)
            if player_points == "Win":
                self.add_team_game(match_index)
                self._db.set_scores(match_index, 0, 0, 0)
            elif player_points == "Duece":
                self._db.set_scores(match_index, 0, 40, 40)
            else:
                self._db.set_scores(match_index, 0, player_points, opponent_points)

    def _current_set(self, sets_x):
        sets = []
        for s in sets_x:
            sets.append([int(i) for i in s])
        current_set = len([i for i, s in enumerate(sets) if max(s) == 7 or (max(s) == 6 and min(s) < 5)])
        return min(current_set, 2), current_set >= 2

    def _match_specifics(self, match_index):
        scores, set1, set2, set3 = self.get_scores_specific_match(match_index)
        player_points, opponent_points = scores
        sets = [set1, set2, set3]

        # get current set
        current_set, is_third_set = self._current_set(sets)
        player_score, opponent_score = sets[current_set]

        return current_set, is_third_set, int(player_score), int(opponent_score), player_points, opponent_points


class Formation:
    def __init__(self, db: DB):
        self._db = db
        self._db_team_name = db.get_team_name()
        self._db_opposing_team_name = db.get_team_name(opponents=True)
        self._db_single_team = db.get_players(opponents=False, double=False)
        self._db_single_opponent = db.get_players(opponents=True, double=False)
        self._db_double_team = db.get_players(opponents=False, double=True)
        self._db_double_opponent = db.get_players(opponents=True, double=True)

    def get_db_team_name(self):
        return self._db_team_name

    def get_db_opposing_team_name(self):
        return self._db_opposing_team_name

    def get_db_single_team(self, short=True):
        if short:
            return [
                player.split(",")[1].split("(")[0].strip() if "," in player else player
                for player in self._db_single_team
            ]
        return self._db_single_team

    def get_db_single_opponent(self, short=True):
        if short:
            return [
                player.split(",")[1].split("(")[0].strip() if "," in player else player
                for player in self._db_single_opponent
            ]
        return self._db_single_opponent

    def get_db_double_team(self):
        return self._db_double_team

    def get_db_double_opponent(self):
        return self._db_double_opponent

    def set_opposing_double(self, team_name, doubles):
        self._db.set_players(team_name=team_name,
                             players=[player for double in doubles for player in double],
                             opponents=True, double=True)

    def set_your_double(self, team_name, doubles):
        self._db.set_players(team_name=team_name,
                             players=[player for double in doubles for player in double],
                             opponents=False, double=True)

    def set_opposing_singles(self, team_name, players):
        if type(players) is dict:
            players = list(players.values())
        self._db.set_players(team_name=team_name, players=players,
                             opponents=True, double=False)

    def set_your_singles(self, team_name, players):
        if type(players) is dict:
            players = list(players.values())
        self._db.set_players(team_name=team_name, players=players,
                             opponents=False, double=False)

    def get_processed_doubles_team(self):
        players_only_name = [p.split(",")[1].split('(')[0].strip() if "," in p else p for p in self._db_double_team]
        return [("/".join(players_only_name[i:i + 2])) for i in range(0, 5, 2)]

    def get_processed_doubles_opponent(self):
        players_only_name = [p.split(",")[1].split('(')[0].strip() if "," in p else p for p in self._db_double_opponent]
        return [("/".join(players_only_name[i:i + 2])) for i in range(0, 5, 2)]

    def get_player_specific_match(self, match_index):
        if match_index == 0:
            players = self._db.get_player_single_1()
        elif match_index == 1:
            players = self._db.get_player_single_2()
        elif match_index == 2:
            players = self._db.get_player_single_3()
        elif match_index == 3:
            players = self._db.get_player_single_4()
        elif match_index == 4:
            players = self._db.get_player_single_5()
        elif match_index == 5:
            players = self._db.get_player_single_6()
        elif match_index >= 6:
            players = [self.get_processed_doubles_team()[match_index - 6],
                       self.get_processed_doubles_opponent()[match_index - 6]]
        else:
            return "Match Index out ouf bounds"
        return players


class Server:
    def __init__(self, db: DB, score: Score):
        self._db = db
        self._score = score

    def get_current_server(self, match_index):
        starter = self._db.get_server(match_number=match_index)
        if starter == -1:
            return -1
        scores, set1, set2, set3 = self._score.get_scores_specific_match(match_index)
        (current_set, is_third_set, player_score, opponent_score, player_points,
         opponent_points) = self._score._match_specifics(match_index)
        sum_games = sum(map(int, set1)) + sum(map(int, set2))
        server = sum_games % 2 + starter
        if is_third_set:
            third_set_points = sum(map(int, set3))
            server = math.ceil(third_set_points / 2) % 2 + server
        elif int(player_score) == 6 and int(opponent_score) == 6:
            tiebreak_points = int(player_points) + int(opponent_points)
            server = math.ceil(tiebreak_points / 2) % 2 + server
        return server % 2

    def set_server_opponent(self, match_index, server):
        self._db.set_server(match_index, 1)

    def set_server_team(self, match_index):
        self._db.set_server(match_index, 0)

    def add_server_symbol_to_formation(self, your_team_x, opponent_team_x):
        your_team = []
        opponent_team = []
        for i in range(len(your_team_x)):
            player, opponent = self.add_server_symbol_to_player(i, your_team_x[i], opponent_team_x[i])
            your_team.append(player)
            opponent_team.append(opponent)
        return your_team, opponent_team

    def add_server_symbol_to_player(self, match_index, player, opponent):
        cs = self.get_current_server(match_index)
        player = player + "   🎾" if cs == 0 else player
        opponent = opponent + "   🎾" if cs == 1 else opponent
        return player, opponent


class Blog:
    def __init__(self, db: DB):
        self._db = db
        self._message_map = {
            # auto/manual, player/opponent, urgency, counter
            1000: "🚨 #Spieler hat den ersten Satz gewonen",
            1100: "🚨 #Spieler hat den ersten Satz verloren",
            1001: "🚨 #Spieler hat den zweiten Satz gewonnen",
            1101: "🚨 #Spieler hat den zweiten Satz verloren",
            1002: "🚨 #Spieler hat das Match gewonnen",
            1102: "🚨 #Spieler hat das Match verloren",
            1011: "🔥 #Spieler Tie-break hat begonnen",
            1013: "🔥 #Spieler Match Tie-break hat begonnen",
            1020: "🎾 #Spieler serviert zum Satz",
            1120: "🎾 Gegner von #Spieler serviert zum Satz",
            1023: "🎾 #Spieler serviert zum Match",
            1123: "🎾 Gegner von #Spieler serviert zum Match",
            10290: "🎾 #Spieler hat Breakball",
            11290: "🎾 Gegner von #Spieler hat Breakball",
            10291: "🎾 #Spieler hat Satzball",
            11021: "🎾 Gegner von #Spieler hat Satztball",
            10292: "🎾 #Spieler hat Matchball",
            11292: "🎾 Gegner von #Spieler hat Matchball",
            2131: "#Spieler 🔥 ist on fire",
            2132: "#Spieler ⚡ Aceeeeee",
            2133: "#Spieler 💥 Winner"
        }

    def get_blog_entries(self):
        entries = self._db.get_blog_entries()
        return entries

    def add_blog_auto_entry(self, match_specifics, scores, match_number, player_name):
        messages = self._generate_auto_blog_entry(match_specifics, scores, player_name)
        for message in messages:
            self._db.add_blog_entry(match_number, message)

    def _generate_auto_blog_entry(self, match_specifics, scores, player_name):
        """Generate blog entries from scores."""
        entries = []

        # Check for set win
        set_win_entry = self._check_for_set_win(match_specifics, scores)
        print(set_win_entry)
        if set_win_entry > -1:
            entries.append(set_win_entry)

        # Check for tiebreak start
        tiebreak_start_entry = self._check_for_tiebreak_start(scores)
        if tiebreak_start_entry > -1:
            entries.append(tiebreak_start_entry)

        # Check for serving for
        serving_for_entry = self._check_for_serving_for(scores)
        if serving_for_entry > -1:
            entries.append(serving_for_entry)

        # Check for break point
        break_point_entry = self._check_for_break_point(scores)
        if break_point_entry > -1:
            entries.append(break_point_entry)

        # Check for set point
        set_point_entry = self._check_for_set_point(scores)
        if set_point_entry > -1:
            entries.append(set_point_entry)

        # Check for match point
        match_point_entry = self._check_for_match_point(scores)
        if match_point_entry > -1:
            entries.append(match_point_entry)
            
        entries = list(set(entries))
        # Return the entries
        return [self._message_map[entry].replace("#Spieler", player_name) for entry in entries]

    def is_set_won(self, player_score, opponent_score, is_third_set):
        player_score = int(player_score)
        opponent_score = int(opponent_score)
        if is_third_set:
            if player_score >= 10 and (player_score - opponent_score) >= 2:
                return 0
            if opponent_score >= 10 and (opponent_score - player_score) >= 2:
                return 1
            return -1
        # Regular set win
        if player_score >= 6 and (player_score - opponent_score) >= 2:
            return 0
        if opponent_score >= 6 and (opponent_score - player_score) >= 2:
            return 1
        # Tiebreak condition (player wins at 7 in case of tiebreak)
        if player_score == 7 and opponent_score == 6:
            return 0
        if opponent_score == 7 and player_score == 6:
            return 1
        return -1

    def _check_for_set_win(self, match_specifics, scores):
        """Check if the player has won the set."""
        current_set, is_third_set, _, _, player_points, opponent_points = match_specifics

        if player_points != "0" or opponent_points != "0":
            return -1
        possible_messages = []
        for set_number, (player_score, opponent_score) in enumerate(scores[1:], start=1):
            possible_messages.append(self.is_set_won(player_score, opponent_score, set_number == 3))

        nb_finished_sets = possible_messages.count(1) + possible_messages.count(0)

        if nb_finished_sets == 0:
            return -1
        if not is_third_set:
            if scores[nb_finished_sets + 1][0] != "0" or scores[nb_finished_sets + 1][1] != "0":
                return -1

        if nb_finished_sets == 1:
            return 1000 if possible_messages[0] == 0 else 1100

        if nb_finished_sets == 2:
            if possible_messages[0] == 0 and possible_messages[1] == 0:
                return 1002
            elif possible_messages[0] == 1 and possible_messages[1] == 1:
                return 1102
            elif possible_messages[0] == 0 and possible_messages[1] == 1:
                return 1101
            elif possible_messages[0] == 1 and possible_messages[1] == 0:
                return 1001
        if nb_finished_sets == 3:
            if possible_messages[-1] == 0:
                return 1002
            elif possible_messages[-1] == 1:
                return 1102
        return -1

    def _check_for_tiebreak_start(self, scores):
        """Check if the set has gone into a tiebreak."""
        return -1

    def _check_for_serving_for(self, scores):
        """Check if the player is serving for the set or match."""
        return -1

    def _check_for_break_point(self, scores):
        """Check if the player has a break point."""
        return -1

    def _check_for_set_point(self, scores):
        """Check if the player has a set point."""
        return -1

    def _check_for_match_point(self, scores):
        """Check if the player has a match point."""
        return -1

    def add_on_fire_blog_entry(self, player_name, match_number):
        self._db.add_blog_entry(match_number, self._message_map[2131].replace("#Spieler", player_name))

    def add_ace_blog_entry(self, player_name, match_number):
        self._db.add_blog_entry(match_number, self._message_map[2132].replace("#Spieler", player_name))

    def add_winner_blog_entry(self, player_name, match_number):
        self._db.add_blog_entry(match_number, self._message_map[2133].replace("#Spieler", player_name))

    def get_button_on_fire(self, player):
        return self._message_map[2131].replace("#Spieler", player)

    def get_button_ace(self, player):
        return self._message_map[2132].replace("#Spieler", player)

    def get_button_winner(self, player):
        return self._message_map[2133].replace("#Spieler", player)
