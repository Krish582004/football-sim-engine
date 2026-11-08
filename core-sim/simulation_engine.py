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
        
        # --- NEW: Resolve all physical collisions ---
        self.physics.resolve_player_collisions(self.current_match_state.players)
        self.physics.resolve_ball_collisions(self.current_match_state.ball, self.current_match_state.players)

        # 2. Network Checksum & Ring Buffer Save
        self.current_match_state.state_checksum = self.current_match_state.calculate_checksum()
        buffer_index = self.latest_tick % self.RING_BUFFER_SIZE
        self.state_ring_buffer[buffer_index] = copy.deepcopy(self.current_match_state)

        # 3. REFEREE BOUNDARIES & SCORE LOGIC
        # X boundary is the goal line (50.0). Z boundary is the touchline (34.0).
        if abs(self.current_match_state.ball.pos_x) > 50.0:
            # Check if it went INSIDE the 7.32m wide posts (Z between -3.66 and +3.66) and below the 2.44m crossbar
            if abs(self.current_match_state.ball.pos_z) < 3.66 and self.current_match_state.ball.pos_y < 2.44:
                if self.current_match_state.ball.pos_x > 50.0:
                    self.current_match_state.score_team_0 += 1  # Blue scored on the Right
                else:
                    self.current_match_state.score_team_1 += 1  # Red scored on the Left
                print(f"GOAL! Current Score: Blue {self.current_match_state.score_team_0} - {self.current_match_state.score_team_1} Red")
            
            # Reset ball to midfield for kickoff
            self.reset_ball()
            
        elif abs(self.current_match_state.ball.pos_z) > 34.0:
            # Out of bounds on the sides (Throw-in placeholder)
            self.reset_ball()

        self.latest_tick += 1

    # Add this helper function at the bottom of the SimulationEngine class
    def reset_ball(self):
        self.current_match_state.ball.pos_x = 0.0
        self.current_match_state.ball.pos_y = 10.0
        self.current_match_state.ball.pos_z = 0.0
        self.current_match_state.ball.vel_x = 0.0
        self.current_match_state.ball.vel_y = -2.0
        self.current_match_state.ball.vel_z = 0.0
        self.current_match_state.ball.spin_y = 0.0

        self.latest_tick += 1

    def get_current_state(self) -> MatchFrameState:
        return self.current_match_state