import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core-sim")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-locomotion")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "match-microservice")))

from match_state import BallState, PlayerState, MatchFrameState
from physics_engine import PhysicsEngine
from simulation_engine import SimulationEngine
from motion_matching import MotionMatcher
from matchmaker import ClubStanding, MatchmakerService

class TestVectorPitchEngine(unittest.TestCase):
    def test_magnus_effect_curls_ball_laterally(self):
        physics = PhysicsEngine()
        ball = BallState(pos_x=0.0, pos_y=2.0, pos_z=0.0, vel_x=25.0, vel_y=4.0, vel_z=0.0, spin_y=35.0)
        for _ in range(30):
            physics.update_ball(ball)
        # Positive spin_y with positive vel_x produces lateral curl in Z
        self.assertNotEqual(round(ball.pos_z, 3), 0.0)
        self.assertGreater(ball.pos_x, 5.0)

    def test_xg_monotonicity_with_distance(self):
        close_xg = PhysicsEngine.calculate_shot_xg(42.0, 0.0, 50.0, is_finesse=True)
        far_xg = PhysicsEngine.calculate_shot_xg(20.0, 15.0, 50.0, is_finesse=False)
        self.assertGreater(close_xg, far_xg)
        self.assertGreater(close_xg, 0.35)

    def test_rollback_and_resimulate_determinism(self):
        sim = SimulationEngine()
        for _ in range(40):
            sim.step()
        current_tick = sim.latest_tick
        result = sim.rollback_and_resimulate(target_tick=25, corrected_input={"dx": 1.0, "dz": 0.0, "sprint": True})
        self.assertEqual(result["status"], "RESIMULATED")
        self.assertEqual(result["rewound_ticks"], 15)
        self.assertEqual(sim.latest_tick, current_tick)
        self.assertNotEqual(result["old_hash"], result["new_hash"])

    def test_motion_matcher_and_matchmaker(self):
        pose = MotionMatcher.select_best_pose(speed=8.2)
        self.assertEqual(pose.pose_id, 2)
        angles = MotionMatcher.compute_skeletal_angles(pose.pose_id, 1.2, 8.2)
        self.assertIn("left_hip_pitch", angles)

        c1 = ClubStanding("MCI", "Manchester Blue", "MCB", 90)
        c2 = ClubStanding("RMA", "Madrid White", "MDW", 89)
        res = MatchmakerService.simulate_fixture(c1, c2, seed=7)
        self.assertEqual(c1.played, 1)
        self.assertEqual(c2.played, 1)
        self.assertIn("home_xg", res)

if __name__ == "__main__":
    unittest.main()
