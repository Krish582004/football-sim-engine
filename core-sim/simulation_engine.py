import copy
from match_state import MatchFrameState
from physics_engine import PhysicsEngine

class SimulationEngine:
    RING_BUFFER_SIZE = 60

    def __init__(self):
        self.latest_tick = 0
        self.current_match_state = MatchFrameState()
        self.state_ring_buffer = [None] * self.RING_BUFFER_SIZE
        self.physics = PhysicsEngine()

        # TEST SCENARIO: A heavy finesse shot curving towards the goal
        self.current_match_state.ball.pos_y = 0.11
        self.current_match_state.ball.vel_x = 25.0  # Kicked hard forward
        self.current_match_state.ball.vel_y = 12.0  # Kicked upward
        self.current_match_state.ball.spin_y = 40.0 # Heavy side-spin to cause curl

    def step(self):
        self.current_match_state.tick_number = self.latest_tick

        # Execute 240Hz sub-stepped physics
        self.physics.update_ball(self.current_match_state.ball)

        self.current_match_state.state_checksum = self.current_match_state.calculate_checksum()

        buffer_index = self.latest_tick % self.RING_BUFFER_SIZE
        self.state_ring_buffer[buffer_index] = copy.deepcopy(self.current_match_state)

        self.latest_tick += 1

    def get_current_state(self) -> MatchFrameState:
        return self.current_match_state