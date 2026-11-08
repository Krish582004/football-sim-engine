from dataclasses import dataclass, field
import hashlib

@dataclass
class PlayerState:
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    vel_z: float = 0.0
    tactical_role: int = 0  
    has_possession: bool = False
    
    # --- PHASE 7: EAFC Attributes & PlayStyles ---
    pace: float = 5.0          # Base speed in m/s
    shot_power: float = 20.0   # Base kick velocity
    curve_ability: float = 15.0 # Magnus spin multiplier
    playstyle: str = "Standard" # "Speedster", "Sniper", or "Bruiser"
    
    # --- Input Control Variables ---
    is_human: bool = False
    input_dx: float = 0.0
    input_dz: float = 0.0
    input_sprint: bool = False # Shift key
    input_shoot: bool = False  # Spacebar

@dataclass
class BallState:
    pos_x: float = 0.0; pos_y: float = 0.0; pos_z: float = 0.0
    vel_x: float = 0.0; vel_y: float = 0.0; vel_z: float = 0.0
    spin_x: float = 0.0; spin_y: float = 0.0; spin_z: float = 0.0

@dataclass
class MatchFrameState:
    tick_number: int = 0
    ball: BallState = field(default_factory=BallState)
    players: list = field(default_factory=lambda: [PlayerState() for _ in range(10)])
    state_checksum: str = ""
    score_team_0: int = 0  
    score_team_1: int = 0  

    def calculate_checksum(self) -> str:
        state_repr = f"{self.tick_number}_{self.score_team_0}_{self.score_team_1}_{self.ball}_{self.players}"
        return hashlib.md5(state_repr.encode('utf-8')).hexdigest()[:8]