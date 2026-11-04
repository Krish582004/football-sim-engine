import copy
from match_state import MatchFrameState

class SimulationEngine:
    RING_BUFFER_SIZE = 60

    def __init__(self):
        self.latest_tick = 0
        self.current_match_state = MatchFrameState()
        self.state_ring_buffer = [None] * self.RING_BUFFER_SIZE

    def step(self):
        # 1. Update tick
        self.current_match_state.tick_number = self.latest_tick

        # 2. Placeholder for upcoming physics & AI updates
        # self.physics.update_ball()
        # self.ai.update_agents()

        # 3. Generate deterministic hash for this frame
        self.current_match_state.state_checksum = self.current_match_state.calculate_checksum()

        # 4. Save a deepcopy to the ring buffer
        buffer_index = self.latest_tick % self.RING_BUFFER_SIZE
        self.state_ring_buffer[buffer_index] = copy.deepcopy(self.current_match_state)

        self.latest_tick += 1

    def get_current_state(self) -> MatchFrameState:
        return self.current_match_state