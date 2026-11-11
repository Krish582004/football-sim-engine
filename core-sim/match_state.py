from dataclasses import dataclass, field
import hashlib
from typing import List, Dict

@dataclass
class PlayerState:
    player_id: int = 0
    name: str = "Player"
    shirt_number: int = 9
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    vel_z: float = 0.0
    facing_angle_rad: float = 0.0
    stamina: float = 100.0
    stamina_max: float = 100.0
    current_anim_pose_id: int = 0   # 0: Idle, 1: Jog, 2: Sprint, 3: Kick, 4: Tackle, 5: Dive
    anim_phase: float = 0.0
    tactical_role: int = 0          # 0: Blue Team, 1: Red Team
    position_code: str = "ST"       # GK, CB, LB, RB, CDM, CM, CAM, LW, RW, ST
    fc_iq_role: str = "Poacher+"
    has_possession: bool = False
    tackle_cooldown: int = 0

    # --- EAFC 27 / eFootball 2027 Attributes & PlayStyles+ ---
    overall: int = 86
    pace: float = 6.8               # Base speed in m/s
    shot_power: float = 24.0        # Base kick velocity (m/s)
    curve_ability: float = 22.0     # Magnus spin multiplier (rad/s)
    pass_accuracy: float = 88.0     # Passing precision (0-100)
    dribbling: float = 86.0         # Ball control & close touch tightness
    defending: float = 75.0         # Tackle radius & interception reach
    physicality: float = 80.0       # Collision mass & stamina resilience
    playstyle: str = "Standard"     # "Sniper", "Speedster", "Bruiser", "Maestro", "Goalkeeper"
    playstyle_plus: str = "Finesse Shot+"

    # --- Input Control Variables ---
    is_human: bool = False
    input_dx: float = 0.0
    input_dz: float = 0.0
    input_sprint: bool = False
    input_shoot: bool = False
    input_finesse: bool = False     # R1 + Shoot: High Magnus curl shot
    input_power_shot: bool = False  # L1 + Shoot: eFootball Stunning Shot
    input_pass: bool = False        # E: Ground pass
    input_through_pass: bool = False # Q: Through ball into space
    input_lofted_pass: bool = False # F: Lofted cross / lob
    input_tackle: bool = False      # X: Standing / slide tackle
    shot_charge: float = 0.7        # 0.1 to 1.0 normalized charge bar

@dataclass
class BallState:
    pos_x: float = 0.0
    pos_y: float = 0.11
    pos_z: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    vel_z: float = 0.0
    spin_x: float = 0.0
    spin_y: float = 0.0
    spin_z: float = 0.0
    last_touched_by: int = -1
    last_shot_xg: float = 0.0

@dataclass
class MatchTelemetryStats:
    possession_ticks_0: int = 1
    possession_ticks_1: int = 1
    shots_0: int = 0
    shots_1: int = 0
    shots_on_target_0: int = 0
    shots_on_target_1: int = 0
    xg_0: float = 0.0
    xg_1: float = 0.0
    passes_attempted_0: int = 0
    passes_completed_0: int = 0
    passes_attempted_1: int = 0
    passes_completed_1: int = 0
    tackles_won_0: int = 0
    tackles_won_1: int = 0

@dataclass
class MatchFrameState:
    tick_number: int = 0
    match_phase: str = "LIVE"       # LIVE, GOAL_CELEBRATION, KICKOFF, HALFTIME, FULLTIME
    phase_timer: int = 0
    ball: BallState = field(default_factory=BallState)
    players: List[PlayerState] = field(default_factory=lambda: [PlayerState(player_id=i) for i in range(10)])
    state_checksum: str = ""
    score_team_0: int = 0
    score_team_1: int = 0
    team_0_mentality: str = "BALANCED"   # ULTRA_DEFENSIVE, BALANCED, GEGENPRESS, ALL_OUT_ATTACK
    team_1_mentality: str = "BALANCED"
    team_0_playstyle: str = "Quick Counter"
    team_1_playstyle: str = "Possession Game"
    team_0_formation: str = "1-2-1"
    team_1_formation: str = "1-2-1"
    stats: MatchTelemetryStats = field(default_factory=MatchTelemetryStats)
    recent_events: List[Dict] = field(default_factory=list)

    def calculate_checksum(self) -> str:
        ball_tuple = (
            round(self.ball.pos_x, 3), round(self.ball.pos_y, 3), round(self.ball.pos_z, 3),
            round(self.ball.vel_x, 3), round(self.ball.vel_y, 3), round(self.ball.vel_z, 3),
            round(self.ball.spin_y, 3)
        )
        players_tuple = tuple(
            (round(p.pos_x, 3), round(p.pos_z, 3), round(p.vel_x, 3), round(p.vel_z, 3), p.has_possession)
            for p in self.players
        )
        state_repr = f"{self.tick_number}_{self.score_team_0}_{self.score_team_1}_{ball_tuple}_{players_tuple}"
        return hashlib.md5(state_repr.encode("utf-8")).hexdigest()[:8]