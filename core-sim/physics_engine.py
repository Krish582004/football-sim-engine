import math
from match_state import BallState

class PhysicsEngine:
    def __init__(self):
        # Real-world football physics constants
        self.mass = 0.43  # kg (FIFA standard)
        self.radius = 0.11  # meters
        self.gravity = -9.81
        self.air_density = 1.225
        self.drag_coeff = 0.25
        self.magnus_coeff = 0.005 
        
        # Sub-stepping: Run physics math at 240Hz (4x the 60Hz tick) for accuracy
        self.sub_steps = 4  
        self.dt = (1.0 / 60.0) / self.sub_steps

    def update_ball(self, ball: BallState):
        for _ in range(self.sub_steps):
            speed = math.sqrt(ball.vel_x**2 + ball.vel_y**2 + ball.vel_z**2)
            if speed == 0:
                continue

            # 1. Quadratic Air Drag (slows the ball down)
            drag_force = 0.5 * self.air_density * (math.pi * self.radius**2) * self.drag_coeff * (speed**2)
            drag_accel = drag_force / self.mass
            
            ax = -(drag_accel * (ball.vel_x / speed))
            ay = -(drag_accel * (ball.vel_y / speed)) + self.gravity
            az = -(drag_accel * (ball.vel_z / speed))

            # 2. Magnus Effect (Spin cross Velocity for curl/dip)
            magnus_accel = self.magnus_coeff / self.mass
            curl_x = (ball.spin_y * ball.vel_z - ball.spin_z * ball.vel_y) * magnus_accel
            curl_y = (ball.spin_z * ball.vel_x - ball.spin_x * ball.vel_z) * magnus_accel
            curl_z = (ball.spin_x * ball.vel_y - ball.spin_y * ball.vel_x) * magnus_accel

            # 3. Integrate Velocity
            ball.vel_x += (ax + curl_x) * self.dt
            ball.vel_y += (ay + curl_y) * self.dt
            ball.vel_z += (az + curl_z) * self.dt

            # 4. Integrate Position
            ball.pos_x += ball.vel_x * self.dt
            ball.pos_y += ball.vel_y * self.dt
            ball.pos_z += ball.vel_z * self.dt

            # 5. Turf Collision (Ground Bounce & Friction)
            if ball.pos_y <= self.radius:
                ball.pos_y = self.radius
                ball.vel_y = abs(ball.vel_y) * 0.6  # 40% energy loss on vertical bounce
                ball.vel_x *= 0.85                  # Grass friction slows horizontal speed
                ball.vel_z *= 0.85