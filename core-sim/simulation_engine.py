import copy
from typing import Optional
from match_state import MatchFrameState
from physics_engine import PhysicsEngine
from tactical_ai import TacticalAI

class SimulationEngine:
    RING_BUFFER_SIZE = 300  # 5 seconds of 60Hz state history for Rollback Netcode & Instant Replay

    def __init__(self):
        self.latest_tick = 0
        self.current_match_state = MatchFrameState()
        self.state_ring_buffer = [None] * self.RING_BUFFER_SIZE

        self.physics = PhysicsEngine()
        self.ai = TacticalAI()

        # Spawn players on start
        self.ai.initialize_match(self.current_match_state)

    def step(self):
        self.current_match_state.tick_number = self.latest_tick

        # 1. Update Physics & AI
        self.physics.update_ball(self.current_match_state.ball)
        self.ai.update_agents(self.current_match_state)

        # 2. Resolve all physical collisions
        self.physics.resolve_player_collisions(self.current_match_state.players)
        self.physics.resolve_ball_collisions(self.current_match_state.ball, self.current_match_state.players)

        # 3. Network Checksum & Ring Buffer Save
        self.current_match_state.state_checksum = self.current_match_state.calculate_checksum()
        buffer_index = self.latest_tick % self.RING_BUFFER_SIZE
        self.state_ring_buffer[buffer_index] = copy.deepcopy(self.current_match_state)

        # 4. Referee Boundaries & Score Logic
        if abs(self.current_match_state.ball.pos_x) > 50.0:
            if abs(self.current_match_state.ball.pos_z) < 3.66 and self.current_match_state.ball.pos_y < 2.44:
                scorer_idx = self.current_match_state.ball.last_touched_by
                scorer_name = (
                    self.current_match_state.players[scorer_idx].name
                    if 0 <= scorer_idx < len(self.current_match_state.players)
                    else "Striker"
                )
                if self.current_match_state.ball.pos_x > 50.0:
                    self.current_match_state.score_team_0 += 1
                    team_str = "BLUE"
                else:
                    self.current_match_state.score_team_1 += 1
                    team_str = "RED"

                self.current_match_state.recent_events.append({
                    "tick": self.latest_tick,
                    "type": "GOAL",
                    "team": team_str,
                    "scorer": scorer_name,
                    "xg": self.current_match_state.ball.last_shot_xg,
                    "score": f"{self.current_match_state.score_team_0}-{self.current_match_state.score_team_1}"
                })
                if len(self.current_match_state.recent_events) > 15:
                    self.current_match_state.recent_events.pop(0)

            self.reset_ball()

        elif abs(self.current_match_state.ball.pos_z) > 34.0:
            self.reset_ball()

        self.latest_tick += 1

    def rollback_and_resimulate(self, target_tick: int, corrected_input: Optional[dict] = None) -> dict:
        """
        GGPO-style Rollback Netcode: Rewinds simulation to `target_tick` from the ring buffer,
        applies a late/corrected network input packet, and fast-forwards back to `latest_tick`.
        """
        ticks_to_rewind = self.latest_tick - target_tick
        if ticks_to_rewind <= 0 or ticks_to_rewind >= self.RING_BUFFER_SIZE:
            return {"status": "OUT_OF_WINDOW", "rewound_ticks": 0}

        buffer_index = target_tick % self.RING_BUFFER_SIZE
        snapshot = self.state_ring_buffer[buffer_index]
        if snapshot is None:
            return {"status": "MISSING_SNAPSHOT", "rewound_ticks": 0}

        old_hash = self.current_match_state.state_checksum
        self.current_match_state = copy.deepcopy(snapshot)
        self.latest_tick = target_tick

        if corrected_input:
            p0 = self.current_match_state.players[0]
            p0.input_dx = corrected_input.get("dx", p0.input_dx)
            p0.input_dz = corrected_input.get("dz", p0.input_dz)
            p0.input_sprint = corrected_input.get("sprint", p0.input_sprint)
            p0.input_shoot = corrected_input.get("shoot", p0.input_shoot)

        for _ in range(ticks_to_rewind):
            self.step()

        return {
            "status": "RESIMULATED",
            "rewound_ticks": ticks_to_rewind,
            "old_hash": old_hash,
            "new_hash": self.current_match_state.state_checksum
        }

    def reset_ball(self):
        self.current_match_state.ball.pos_x = 0.0
        self.current_match_state.ball.pos_y = 6.0
        self.current_match_state.ball.pos_z = 0.0
        self.current_match_state.ball.vel_x = 0.0
        self.current_match_state.ball.vel_y = -2.0
        self.current_match_state.ball.vel_z = 0.0
        self.current_match_state.ball.spin_y = 0.0

    def get_current_state(self) -> MatchFrameState:
        return self.current_match_state