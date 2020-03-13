import datetime
import pytz
import requests
import urllib


class ScoreParser:
    url_map = {
        "mlb": "http://www.espn.com/mlb/bottomline/scores",
        "nba": "http://www.espn.com/nba/bottomline/scores",
    }

    def __init__(self, sport_string):
        self.url = self.url_map.get(sport_string)
        self.sport = sport_string
        self.score_time = None
        self.score_data = {}

    def get_current_scores(self):
        # Request the score data from url
        response = requests.get(self.url)

        data_rows = []
        if response.ok:
            text_encoded = response.text
            # Remove encoding from text
            text = urllib.parse.unquote(text_encoded)
            # Split data in to rows
            data_rows = [x for x in text.split("&") if x]

        score_data = {}
        # Extract key-value pairs in data
        for row in data_rows:
            key, value = row.split("=", 1)
            score_data[key] = value

        clean_score_data = self.clean_scores(score_data)
        self.score_data = clean_score_data
        self.score_time = clean_score_data["score_timestamp"]
        return self.score_data

    def clean_scores(self, s_data):

        clean_data = {}
        # Extract basic data
        clean_data["score_loaded"] = s_data["mlb_s_loaded"]
        clean_data["score_delay"] = s_data["mlb_s_delay"]
        clean_data["score_timestamp"] = self.clean_time_stamp(s_data["mlb_s_stamp"])
        clean_data["score_count"] = int(s_data["mlb_s_count"])

        clean_data["games"] = []
        for idx in range(1, clean_data["score_count"] + 1):
            match_up = s_data[f"{self.sport}_s_left{idx}"].replace("^", "")
            score = match_up.split("(")[0]
            status = match_up.split("(")[1].replace(")", "")
            # Get info for games not started yet
            if " at " in score:
                teams = score.strip().split(" at ")
                home_team = teams[1].strip()
                home_score = None
                away_team = teams[0].strip()
                away_score = None
            else:
                team_strings = score.strip().split("   ")
                away_team, away_score = self.parse_score(team_strings[0])
                home_team, home_score = self.parse_score(team_strings[1])
            clean_game = {
                "home-team": home_team,
                "home-score": home_score,
                "away-team": away_team,
                "away-score": away_score,
                "game-status": status,
            }
            clean_data["games"].append(clean_game)
        return clean_data

    def clean_time_stamp(self, ts_string):
        ts = datetime.datetime.strptime(ts_string, "%m%d%H%M%S")
        ts = ts.replace(year=datetime.datetime.now().year)
        tz = pytz.timezone("America/Los_Angeles")
        ts = tz.localize(ts)
        return ts

    def parse_score(self, team_string):
        name, score = team_string.rsplit(" ", 1)
        return name, int(score)

    def get_team_score(self, team_name):
        game_data = {}
        if self.score_data:
            for sd in self.score_data["games"]:
                if team_name in [sd["home-team"], sd["away-team"]]:
                    game_data = sd
        return game_data
