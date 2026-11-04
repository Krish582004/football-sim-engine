import math
import random
from match_state import MatchFrameState

class TacticalAI:
    def __init__(self):
        self.team_0_home = [(-40, 0), (-20, -15), (-20, 15), (-5, 0), (10, 0)] 
        self.team_1_home = [(40, 0), (20, -15), (20, 15), (5, 0), (-10, 0)]

    def initialize_match(self, state: MatchFrameState):
        for i in range(5):
            state.players[i].pos_x = self.team_0_home[i][0]
            state.players[i].pos_y = 1.0 
            state.players[i].pos_z = self.team_0_home[i][1]
            state.players[i].tactical_role = 0 

        for i in range(5, 10):
            state.players[i].pos_x = self.team_1_home[i - 5][0]
            state.players[i].pos_y = 1.0
            state.players[i].pos_z = self.team_1_home[i - 5][1]
            state.players[i].tactical_role = 1 

    def update_agents(self, state: MatchFrameState):
        ball = state.ball

        for i, player in enumerate(state.players):
            home_x, home_z = self.team_0_home[i] if i < 5 else self.team_1_home[i - 5]

            dx_ball = ball.pos_x - player.pos_x
            dz_ball = ball.pos_z - player.pos_z
            dist_to_ball = math.hypot(dx_ball, dz_ball)

            # --- NEW: Collision & Kicking Logic ---
            # If the player is within 0.5m of the ball and the ball is on the ground
            if dist_to_ball < 0.5 and ball.pos_y < 1.0:
                player.has_possession = True
                
                # Blue (Team 0) shoots at X = +50 | Red (Team 1) shoots at X = -50
                target_goal_x = 50.0 if player.tactical_role == 0 else -50.0
                
                # Calculate vector to the goal with slight random variance so it feels organic
                kick_dx = target_goal_x - player.pos_x
                kick_dz = (0.0 - player.pos_z) + random.uniform(-5.0, 5.0) 
                
                kick_mag = math.hypot(kick_dx, kick_dz)
                
                # Apply heavy velocity (15 to 25 m/s) and upward chip (2 to 8 m/s)
                ball.vel_x = (kick_dx / kick_mag) * random.uniform(15.0, 25.0)
                ball.vel_y = random.uniform(2.0, 8.0)
                ball.vel_z = (kick_dz / kick_mag) * random.uniform(15.0, 25.0)
                
                # Add random spin so the physics engine makes it curve!
                ball.spin_y = random.uniform(-30.0, 30.0)
            else:
                player.has_possession = False

            # --- Spatial Movement ---
            if dist_to_ball < 15.0:
                target_x, target_z = ball.pos_x, ball.pos_z  
            else:
                target_x = home_x + (ball.pos_x * 0.15)
                target_z = home_z + (ball.pos_z * 0.15)

            dx_target = target_x - player.pos_x
            dz_target = target_z - player.pos_z
            dist_to_target = math.hypot(dx_target, dz_target)

            # Only run if they don't already have the ball
            if dist_to_target > 0.2 and not player.has_possession:  
                speed = 5.0 * (1.0 / 60.0)  
                player.pos_x += (dx_target / dist_to_target) * speed
                player.pos_z += (dz_target / dist_to_target) * speed

            player.facing_angle_rad = math.atan2(dz_ball, dx_ball)