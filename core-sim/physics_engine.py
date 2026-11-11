import math
from typing import List, Tuple
from match_state import BallState, PlayerState

class PhysicsEngine:
    """
    Deterministic 240Hz Sub-Stepped Football Physics Engine.
    Models:
      - Quadratic aerodynamic drag: F_d = -0.5 * rho * A * C_d * |v| * v
      - Magnus lift/curl effect:    F_m = S_0 * (omega x v)
      - Anisotropic turf restitution & rolling friction
      - Rigid-body cylinder player collisions & tackle impulse transfer
      - Expected Goals (xG) logistic spatial evaluation
    """
    def __init__(self):
        # FIFA Quality Pro regulation ball constants
        self.mass = 0.43          # kg
        self.radius = 0.11        # meters
        self.gravity = -9.81      # m/s^2
        self.air_density = 1.225  # kg/m^3 at sea level
        self.drag_coeff = 0.25    # aerodynamic drag coefficient
        self.magnus_coeff = 0.005 # lift coefficient for spin-induced curl/dip

        # Sub-stepping: Run physics math at 240Hz (4x the 60Hz tick)
        self.sub_steps = 4
        self.dt = (1.0 / 60.0) / self.sub_steps

    def update_ball(self, ball: BallState):
        for _ in range(self.sub_steps):
            speed = math.sqrt(ball.vel_x**2 + ball.vel_y**2 + ball.vel_z**2)
            if speed < 0.01 and ball.pos_y <= self.radius + 0.005:
                ball.vel_x = 0.0
                ball.vel_y = 0.0
                ball.vel_z = 0.0
                ball.pos_y = self.radius
                continue

            if speed > 0:
                # 1. Quadratic Air Drag
                area = math.pi * (self.radius ** 2)
                drag_force = 0.5 * self.air_density * area * self.drag_coeff * (speed ** 2)
                drag_accel = drag_force / self.mass

                ax = -(drag_accel * (ball.vel_x / speed))
                ay = -(drag_accel * (ball.vel_y / speed)) + self.gravity
                az = -(drag_accel * (ball.vel_z / speed))
            else:
                ax, ay, az = 0.0, self.gravity, 0.0

            # 2. Magnus Effect (Spin cross Velocity for curl & dip)
            magnus_accel = self.magnus_coeff / self.mass
            curl_x = (ball.spin_y * ball.vel_z - ball.spin_z * ball.vel_y) * magnus_accel
            curl_y = (ball.spin_z * ball.vel_x - ball.spin_x * ball.vel_z) * magnus_accel
            curl_z = (ball.spin_x * ball.vel_y - ball.spin_y * ball.vel_x) * magnus_accel

            # 3. Semi-Implicit Euler Velocity Integration
            ball.vel_x += (ax + curl_x) * self.dt
            ball.vel_y += (ay + curl_y) * self.dt
            ball.vel_z += (az + curl_z) * self.dt

            # 4. Position Integration
            ball.pos_x += ball.vel_x * self.dt
            ball.pos_y += ball.vel_y * self.dt
            ball.pos_z += ball.vel_z * self.dt

            # 5. Turf Collision (Ground Bounce, Rolling Friction & Spin Decay)
            if ball.pos_y <= self.radius:
                ball.pos_y = self.radius
                if ball.vel_y < -0.4:
                    ball.vel_y = abs(ball.vel_y) * 0.60  # 40% vertical energy absorption
                else:
                    ball.vel_y = 0.0
                # Apply sub-stepped turf friction equivalent to ~0.85 per 60Hz tick
                sub_friction = 0.85 ** (1.0 / self.sub_steps)
                ball.vel_x *= sub_friction
                ball.vel_z *= sub_friction
                ball.spin_x *= 0.98
                ball.spin_y *= 0.98
                ball.spin_z *= 0.98

            # 6. Goalpost Cylinder Collisions (X = +/-50.0, Z = +/-3.66, Y <= 2.44)
            for gx in (-50.0, 50.0):
                for gz in (-3.66, 3.66):
                    dx = ball.pos_x - gx
                    dz = ball.pos_z - gz
                    dist = math.hypot(dx, dz)
                    post_min = self.radius + 0.12
                    if 0 < dist < post_min and ball.pos_y <= 2.55:
                        nx, nz = dx / dist, dz / dist
                        dot = ball.vel_x * nx + ball.vel_z * nz
                        if dot < 0:
                            ball.vel_x = (ball.vel_x - 2 * dot * nx) * 0.75
                            ball.vel_z = (ball.vel_z - 2 * dot * nz) * 0.75
                            ball.pos_x += nx * (post_min - dist)
                            ball.pos_z += nz * (post_min - dist)

    def predict_trajectory(self, ball: BallState, steps: int = 45) -> List[Tuple[float, float, float]]:
        """Predicts future 3D coordinates of the ball without mutating live state."""
        sim_ball = BallState(
            pos_x=ball.pos_x, pos_y=ball.pos_y, pos_z=ball.pos_z,
            vel_x=ball.vel_x, vel_y=ball.vel_y, vel_z=ball.vel_z,
            spin_x=ball.spin_x, spin_y=ball.spin_y, spin_z=ball.spin_z
        )
        points = []
        for _ in range(steps):
            self.update_ball(sim_ball)
            points.append((round(sim_ball.pos_x, 2), round(sim_ball.pos_y, 2), round(sim_ball.pos_z, 2)))
        return points

    @staticmethod
    def calculate_shot_xg(pos_x: float, pos_z: float, target_goal_x: float, is_finesse: bool = False, is_power: bool = False) -> float:
        """Calculates Expected Goals (xG) from shot distance, visible goal angle, and PlayStyle+ modifiers."""
        dx = abs(target_goal_x - pos_x)
        dz = abs(pos_z)
        distance = math.hypot(dx, dz)
        # Angle subtended by the 7.32m goal frame
        goal_half = 3.66
        angle_left = math.atan2(pos_z + goal_half, max(0.5, dx))
        angle_right = math.atan2(pos_z - goal_half, max(0.5, dx))
        visible_angle = abs(angle_left - angle_right)

        # Calibrated logistic xG model
        logit = -1.65 + (2.35 * visible_angle) - (0.095 * distance)
        if is_finesse:
            logit += 0.22
        if is_power:
            logit += 0.18
        xg = 1.0 / (1.0 + math.exp(-logit))
        return round(max(0.01, min(0.97, xg)), 3)

    def resolve_player_collisions(self, players: List[PlayerState]):
        min_dist = 0.8  # 0.4m radius per player cylinder
        for i in range(len(players)):
            for j in range(i + 1, len(players)):
                p1 = players[i]
                p2 = players[j]
                dx = p2.pos_x - p1.pos_x
                dz = p2.pos_z - p1.pos_z
                dist = math.hypot(dx, dz)

                if 0 < dist < min_dist:
                    overlap = min_dist - dist
                    nx = dx / dist
                    nz = dz / dist

                    # Weight pushback by physicality attribute
                    total_phys = max(1.0, p1.physicality + p2.physicality)
                    ratio_1 = p2.physicality / total_phys
                    ratio_2 = p1.physicality / total_phys

                    p1.pos_x -= nx * (overlap * ratio_1)
                    p1.pos_z -= nz * (overlap * ratio_1)
                    p2.pos_x += nx * (overlap * ratio_2)
                    p2.pos_z += nz * (overlap * ratio_2)

                    # Tackling Mechanic: Physical collision strips possession
                    if p1.has_possession or p2.has_possession:
                        p1.has_possession = False
                        p2.has_possession = False

    def resolve_ball_collisions(self, ball: BallState, players: List[PlayerState]):
        min_dist = 0.6  # Ball radius (0.2) + Player cylinder radius (0.4)
        for idx, p in enumerate(players):
            dx = ball.pos_x - p.pos_x
            dz = ball.pos_z - p.pos_z
            dist = math.hypot(dx, dz)

            if 0 < dist < min_dist and ball.pos_y < 1.8:
                nx = dx / dist
                nz = dz / dist
                dot_product = (ball.vel_x * nx) + (ball.vel_z * nz)

                if dot_product < 0:
                    restitution = 0.45 if p.playstyle == "Goalkeeper" else 0.50
                    ball.vel_x = (ball.vel_x - 2 * dot_product * nx) * restitution
                    ball.vel_z = (ball.vel_z - 2 * dot_product * nz) * restitution

                    overlap = min_dist - dist
                    ball.pos_x += nx * overlap
                    ball.pos_z += nz * overlap
                    ball.last_touched_by = idx