"""
Matchmaking & Season Simulation Microservice.
Handles ELO/Division Rivals skill rating updates, Monte Carlo fixture simulations,
and match telemetry export.
"""
import math
import random
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ClubStanding:
    club_id: str
    name: str
    short_code: str
    rating: int
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    @property
    def goal_diff(self) -> int:
        return self.goals_for - self.goals_against

class MatchmakerService:
    @staticmethod
    def calculate_elo_delta(rating_a: float, rating_b: float, score_a: int, score_b: int, k_factor: float = 32.0) -> float:
        expected_a = 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))
        actual_a = 1.0 if score_a > score_b else (0.5 if score_a == score_b else 0.0)
        return round(k_factor * (actual_a - expected_a), 2)

    @staticmethod
    def simulate_fixture(home: ClubStanding, away: ClubStanding, seed: int = 42) -> Dict:
        rng = random.Random(seed)
        rating_diff = (home.rating - away.rating) + 2.5  # Home advantage
        lambda_home = max(0.4, 1.45 + rating_diff * 0.08)
        lambda_away = max(0.3, 1.15 - rating_diff * 0.06)

        # Sample Poisson-like goals
        home_goals = sum(1 for _ in range(5) if rng.random() < (lambda_home / 5.0))
        away_goals = sum(1 for _ in range(5) if rng.random() < (lambda_away / 5.0))

        home.played += 1
        away.played += 1
        home.goals_for += home_goals
        home.goals_against += away_goals
        away.goals_for += away_goals
        away.goals_against += home_goals

        if home_goals > away_goals:
            home.won += 1
            home.points += 3
            away.lost += 1
        elif home_goals < away_goals:
            away.won += 1
            away.points += 3
            home.lost += 1
        else:
            home.drawn += 1
            away.drawn += 1
            home.points += 1
            away.points += 1

        return {
            "home": home.name,
            "away": away.name,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "home_xg": round(lambda_home, 2),
            "away_xg": round(lambda_away, 2)
        }
