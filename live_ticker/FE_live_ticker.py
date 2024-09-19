import time

import streamlit as st
import pandas as pd
from dataflow import DB
from BE_live_ticker import Score, Formation, Server, Blog

LIST_OF_PLAYERS = [
    "Wähle einen Spieler",
    "Ott, Felix (LK2,5, 1991)",
    "Bruns, Nicolas (LK4,6, 1981)",
    "Klawes, Dennis (LK5,7, 1994)",
    "Stüven, Sami (LK3,7, 1977)",
    "Stelljes, Florian (LK6,0, 1977)",
    "Schnürmacher, Michael (LK5,9, 1982)",
    "Schmidt, Timo (LK6,9, 1991)",
    "Hitomi, Julian (LK7,5, 1990)",
    "Kaszubowski, Philipp (LK9,1, 1990)",
    "Dr. Werner, Daniel (LK9,4, 1981)",
    "Kemmerich, Ronny (LK11,7, 1984)",
    "Stiller, Max (LK24,0, 1983)",
    "Pflugmacher, Mathis (LK15,1, 1990)",
    "Carstens, Phillipp (LK15,1, 1992)"
]

LIST_OF_OPPONENTS = [
    "Wähle einen Spieler",
    "Golombek, Stefan (LK4,5, 1988)",
    "Schilke, Tom (LK4,5, 1983)",
    "Vogel, Matthias (LK5,8, 1986)",
    "Dr. Berg, Michael (LK7,0, 1973)",
    "Schmidtchen, Michael (LK7,5, 1984)",
    "Colditz, Patrick (LK7,5, 1977)",
    "Dr. Graf, Holger (LK7,9, 1973)",
    "Troebes, Matthias (LK8,5, 1982)",
    "Siegert, Christopher (LK9,2, 1978)",
    "Deitmaring, Armin (LK9,5, 1991)",
    "Wagner, Gerd (LK11,5, 1964)",
    "Möser, Ede (LK12,1, 1991)",
    "Dr. Escher, Niko (LK12,8, 1978)",
    "Schuster, Jan (LK13,4, 1979)",
    "Faßbender, Sebastian (LK13,6, 1992)",
    "Müller-Berg, Michael (LK13,9, 1981)",
    "Luhde, Ronny (LK14,4, 1977)",
    "Klitsch, Tobias (LK15,6, 1977)",
    "Triller, Jörg (LK15,8, 1975)",
    "Stöckmann, Daniel (LK15,8, 1985)",
    "Dr. Sauter, Simon (LK16,0, 1973)",
    "Krüger, Carsten (LK16,4, 1965)",
    "Dr. Mothes, Henning (LK17,2, 1965)"
]

db = DB()
db_score = Score(db)
db_formation = Formation(db)
db_server = Server(db, db_score)
db_blog = Blog(db)


# Function to print winner statement
def print_set_winner(match_index, player, double=False):
    if double:
        if player == 0:
            player_name = st.session_state.your_doubles[match_index]
        else:
            player_name = st.session_state.opposing_doubles[match_index]
    else:
        if player == 0:
            player_name = st.session_state.your_team[match_index]
        else:
            player_name = st.session_state.opposing_team[match_index]
    st.write(f"{player_name} wins the set!")


# Function to update player and team names
def update_names():
    col1, col2 = st.columns(2)

    # Your Team Input Fields
    with col1:
        team_name = st.text_input("", db_formation.get_db_team_name(), key="your_team_name")
        st.markdown("---")  # Separation line
        st.markdown("## Einzel Spieler")
        your_team = {}
        for i in range(6):
            your_team[i] = st.selectbox("", [db_formation.get_db_single_team()[i]] + LIST_OF_PLAYERS,
                                        key=f"your_team_{i}")

        st.markdown("---")  # Separation line
        if st.button("Update Einzel Aufstellung", key="update_your_team"):
            db_formation.set_your_singles(team_name, your_team)

        st.markdown("---")  # Separation line
        st.markdown("## Doubles Pairings")
        your_doubles = []
        for i in range(3):
            st.markdown(f"### Double {i + 1}")
            player1 = st.selectbox("", [db_formation.get_db_double_team()[i * 2]] + LIST_OF_PLAYERS,
                                   key=f"your_double_{i}_p1")
            player2 = st.selectbox("", [db_formation.get_db_double_team()[i * 2 + 1]] + LIST_OF_PLAYERS,
                                   key=f"your_double_{i}_p2")
            your_doubles.append((player1, player2))

        st.markdown("---")
        if st.button("Update Doppel Aufstellung", key="update_your_doubles"):
            db_formation.set_your_double(team_name, your_doubles)

    # Opposing Team Input Fields
    with col2:
        opposing_team_name = st.text_input("", db_formation.get_db_opposing_team_name(), key="opposing_team_name")
        st.markdown("---")  # Separation line
        st.markdown("## Singles Players")
        opposing_team = {}
        for i in range(6):
            opposing_team[i] = st.selectbox("", [db_formation.get_db_single_opponent()[i]] + LIST_OF_OPPONENTS,
                                            key=f"opposing_team_{i}")
        st.markdown("---")  # Separation line
        if st.button("Update Einzel Aufstellung", key="update_opposing_team"):
            db_formation.set_opposing_singles(opposing_team_name, opposing_team)

        st.markdown("---")  # Separation line
        st.markdown("## Doubles Pairings")
        opposing_doubles = []
        for i in range(3):
            st.markdown(f"### Double {i + 1}")
            player1 = st.selectbox("", [db_formation.get_db_double_opponent()[i * 2]] + LIST_OF_OPPONENTS,
                                   key=f"opposing_double_{i}_p1")
            player2 = st.selectbox("", [db_formation.get_db_double_opponent()[i * 2 + 1]] + LIST_OF_OPPONENTS,
                                   key=f"opposing_double_{i}_p2")
            opposing_doubles.append((player1, player2))

        st.markdown("---")
        if st.button("Update Doppel Aufstellung", key="update_opposing_doubles"):
            db_formation.set_opposing_double(opposing_team_name, opposing_doubles)


# Prepare data for the table overview
def prepare_table_data():
    single_scores = db_score.get_all_single_scores()
    double_scores = db_score.get_all_double_scores()
    your_team_name = db_formation.get_db_team_name()
    opponent_team_name = db_formation.get_db_opposing_team_name()

    your_team_x = db_formation.get_db_single_team()
    opponent_team_x = db_formation.get_db_single_opponent()

    your_team, opponent_team = db_server.add_server_symbol_to_formation(your_team_x, opponent_team_x)

    singles_data = {
        f"{your_team_name} ": your_team,
        f"{opponent_team_name}": opponent_team,
        "Points": [f"{score[0][0]}/{score[0][1]}" for score in single_scores],
        "1st Set": [f"{score[1][0]}/{score[1][1]}" for score in single_scores],
        "2nd Set": [f"{score[2][0]}/{score[2][1]}" for score in single_scores],
        "3nd Set": [f"{score[3][0]}/{score[3][1]}" for score in single_scores]
    }

    doubles_data = {
        f"{your_team_name}": db_formation.get_processed_doubles_team(),
        f"{opponent_team_name}": db_formation.get_processed_doubles_opponent(),
        "Points": [f"{score[0][0]}/{score[0][1]}" for score in double_scores],
        "1st Set": [f"{score[1][0]}/{score[1][1]}" for score in double_scores],
        "2nd Set": [f"{score[2][0]}/{score[2][1]}" for score in double_scores],
        "3nd Set": [f"{score[3][0]}/{score[3][1]}" for score in double_scores]
    }

    singles_df = pd.DataFrame(singles_data)
    doubles_df = pd.DataFrame(doubles_data)

    return singles_df, doubles_df


# Main page: Overview and summary
def main_page():
    st.title(f"{db.get_team_name()} vs {db.get_team_name(opponents=True)} - Live Ticker")

    # Display overview of scores as tables
    st.header("Einzel")
    singles_df, doubles_df = prepare_table_data()
    st.dataframe(singles_df, hide_index=True)

    st.header("Doppel")
    st.dataframe(doubles_df, hide_index=True)

    st.header("Live Blog")

    blog = db_blog.get_blog_entries()
    for timestamp, message in blog:
        t = timestamp.split(' ')[1].split(':')[0:2]
        m_time = f"{int(t[0]) + 2}:{t[1]}"
        st.markdown(f"{m_time}: {message}")

    time.sleep(2)
    st.rerun()


# Function to set the server
def set_server(match_type, match_index, server):
    if match_type == 'singles':
        st.session_state.singles_serve[match_index] = server
    else:
        st.session_state.doubles_serve[match_index] = server


# Tabs for each match to update scores
def display_match(match_index):
    player, opponent = db_formation.get_player_specific_match(match_index)
    scores = db_score.get_scores_specific_match(match_index)
    points, set_1, set_2, set_3 = scores

    st.write(f"### {player} vs {opponent}")

    # Create a dataframe to display the scores in a table format
    data = {
        "Points": [points[0], points[1]],
        "Set 1": [set_1[0], set_1[1]],
        "Set 2": [set_2[0], set_2[1]],
        "Set 3": [set_3[0], set_3[1]]
    }
    player_ws, opponent_ws = db_server.add_server_symbol_to_player(match_index, player, opponent)
    df = pd.DataFrame(data, index=[player_ws, opponent_ws])

    # Display the dataframe as a table
    st.table(df)

    # Controls for updating the scores
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"{player}")
        if st.button("Add Point", key=f"add_point_p1_{match_index}"):
            db_score.add_team_point(match_index)
            st.rerun()
        if st.button("Add Game", key=f"add_game_p1_{match_index}"):
            db_score.add_team_game(match_index)
            st.rerun()

    with col2:
        st.write(f"{opponent}")
        if st.button("Add Point", key=f"add_point_p2_{match_index}"):
            db_score.add_opponent_point(match_index)
            st.rerun()
        if st.button("Add Game", key=f"add_game_p2_{match_index}"):
            db_score.add_opponent_game(match_index)
            st.rerun()

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("Wer hat mit Aufschlag angefangen?")

    with col2:
        if st.button(f"{player}", key=f"set_server_player_{match_index}"):
            db_server.set_server_team(match_index)
            st.rerun()

    with col3:
        if st.button(f"{opponent}", key=f"set_server_opponent_{match_index}"):
            db_server.set_server_opponent(match_index, 1)
            st.rerun()

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(db_blog.get_button_on_fire(player), key=f"is_on_fire_{match_index}"):
            db_blog.add_on_fire_blog_entry(player, match_index)
            st.rerun()

    with col2:
        if st.button(db_blog.get_button_ace(player), key=f"ace_{match_index}"):
            db_blog.add_ace_blog_entry(player, match_index)
            st.rerun()

    with col3:
        if st.button(db_blog.get_button_winner(player), key=f"winner_{match_index}"):
            db_blog.add_winner_blog_entry(player, match_index)
            st.rerun()

    st.markdown("---")

    if st.button("Reset Scores", key=f"reset_scores_{match_index}"):
        db_score.reset_scores(match_index)
        st.rerun()

    match_specifics = db_score._match_specifics(match_index)
    db_blog.add_blog_auto_entry(match_specifics, scores, match_index, player)


# Player and team name input page
def settings_page():
    st.title("Aufstellung")
    update_names()


# Main navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to",
                        ["Aufstellung", "Overview", "Match 1", "Match 2", "Match 3", "Match 4", "Match 5", "Match 6",
                         "Doubles 1", "Doubles 2", "Doubles 3"])

if page == "Overview":
    main_page()
elif page.startswith("Match"):
    match_num = int(page.split(" ")[1]) - 1
    display_match(match_num)
elif page.startswith("Doubles"):
    match_num = int(page.split(" ")[1]) - 1
    display_match(match_num + 6)
elif page == "Aufstellung":
    settings_page()
