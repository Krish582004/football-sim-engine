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

        # Execute 240Hz sub-stepped physics
        self.physics.update_ball(self.current_match_state.ball)
        
        # Execute Multi-Agent AI
        self.ai.update_agents(self.current_match_state)

        # Generate deterministic hash & save to ring buffer
        self.current_match_state.state_checksum = self.current_match_state.calculate_checksum()
        buffer_index = self.latest_tick % self.RING_BUFFER_SIZE
        self.state_ring_buffer[buffer_index] = copy.deepcopy(self.current_match_state)

        # Reset ball kick for testing loop
        if self.latest_tick % 90 == 0:
            self.current_match_state.ball.pos_x = 0.0
            self.current_match_state.ball.pos_y = 0.11
            self.current_match_state.ball.pos_z = 0.0
            self.current_match_state.ball.vel_x = 25.0
            self.current_match_state.ball.vel_y = 12.0
            self.current_match_state.ball.vel_z = 0.0

        self.latest_tick += 1

    def get_current_state(self) -> MatchFrameState:
        return self.current_match_state