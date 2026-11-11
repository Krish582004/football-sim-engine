"""
HyperMotion-Inspired Procedural Motion Matching & Inverse Kinematics Synthesizer.
Selects lowest-cost animation pose features based on velocity, trajectory prediction,
and stride phase, and generates joint angles for 3D skeletal rendering.
"""
import math
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class PoseFeature:
    pose_id: int
    name: str
    target_speed: float
    stride_freq: float
    torso_lean_rad: float

POSE_DATABASE: List[PoseFeature] = [
    PoseFeature(0, "Idle_Breath", 0.0, 1.2, 0.03),
    PoseFeature(1, "Tactical_Jog", 4.8, 2.6, 0.14),
    PoseFeature(2, "Explosive_Sprint", 8.5, 4.1, 0.28),
    PoseFeature(3, "Power_Strike_FollowThrough", 3.5, 3.0, -0.18),
    PoseFeature(4, "Standing_Lunge_Tackle", 5.0, 2.0, 0.42),
    PoseFeature(5, "Goalkeeper_Reflex_Dive", 6.5, 3.2, 0.55),
]

class MotionMatcher:
    @staticmethod
    def select_best_pose(speed: float, is_kicking: bool = False, is_tackling: bool = False, is_gk_diving: bool = False) -> PoseFeature:
        if is_gk_diving:
            return POSE_DATABASE[5]
        if is_tackling:
            return POSE_DATABASE[4]
        if is_kicking:
            return POSE_DATABASE[3]

        best_pose = POSE_DATABASE[0]
        best_cost = float("inf")
        for pose in POSE_DATABASE[:3]:
            cost = (pose.target_speed - speed) ** 2
            if cost < best_cost:
                best_cost = cost
                best_pose = pose
        return best_pose

    @staticmethod
    def compute_skeletal_angles(pose_id: int, phase_rad: float, speed: float) -> Dict[str, float]:
        """Returns procedural joint rotations (in radians) for upper/lower limbs."""
        pose = POSE_DATABASE[pose_id] if 0 <= pose_id < len(POSE_DATABASE) else POSE_DATABASE[0]
        amp = min(1.0, speed / 7.5) if pose_id in (1, 2) else (0.9 if pose_id in (3, 4, 5) else 0.08)
        swing = math.sin(phase_rad) * (0.75 * amp)
        return {
            "left_hip_pitch": swing,
            "right_hip_pitch": -swing if pose_id != 3 else 1.05,
            "left_shoulder_pitch": -swing * 0.7,
            "right_shoulder_pitch": swing * 0.7,
            "torso_lean": pose.torso_lean_rad
        }
