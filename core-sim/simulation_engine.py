import copy
from match_state import MatchFrameState
from physics_engine import PhysicsEngine
from tactical_ai import TacticalAI  # <-- Import the AI

class SimulationEngine:
    RING_BUFFER_SIZE = 60

    def __init__(self):
        self.latest_tick = 0
        self.current_match_state = MatchFrameState()
        self.state_ring_buffer = [None] * self.RING_BUFFER_SIZE
        
        self.physics = PhysicsEngine()
        self.ai = TacticalAI() # <-- Initialize AI
        
        # Spawn players on start
        self.ai.initialize_match(self.current_match_state)

    def step(self):
        self.current_match_state.tick_number = self.latest_tick

        # 1. Update Physics & AI
        self.physics.update_ball(self.current_match_state.ball)
        self.ai.update_agents(self.current_match_state)

        # 2. Network Checksum & Ring Buffer Save
        self.current_match_state.state_checksum = self.current_match_state.calculate_checksum()
        buffer_index = self.latest_tick % self.RING_BUFFER_SIZE
        self.state_ring_buffer[buffer_index] = copy.deepcopy(self.current_match_state)

        # 3. REFEREE BOUNDARIES: Out of Bounds or Goal Scored
        # Pitch is 105x68. Center is 0,0. X bounds = +/- 52.5. Z bounds = +/- 34.0.
        if abs(self.current_match_state.ball.pos_x) > 52.5 or abs(self.current_match_state.ball.pos_z) > 34.0:
            # Reset ball to midfield and drop it from the sky
            self.current_match_state.ball.pos_x = 0.0
            self.current_match_state.ball.pos_y = 10.0 # Drop from 10 meters high
            self.current_match_state.ball.pos_z = 0.0
            self.current_match_state.ball.vel_x = 0.0
            self.current_match_state.ball.vel_y = -2.0 # Dropping velocity
            self.current_match_state.ball.vel_z = 0.0
            self.current_match_state.ball.spin_y = 0.0

        self.latest_tick += 1

    def get_current_state(self) -> MatchFrameState:
        return self.current_match_state