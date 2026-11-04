import math
from match_state import MatchFrameState

class TacticalAI:
    def __init__(self):
        # Base 5v5 Formation coordinates (X, Z)
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
        ball_x = state.ball.pos_x
        ball_z = state.ball.pos_z

        for i, player in enumerate(state.players):
            # 1. Identify the player's anchor position
            home_x, home_z = self.team_0_home[i] if i < 5 else self.team_1_home[i - 5]

            # 2. Vector mechanics: Calculate distance vector to the ball
            dx_ball = ball_x - player.pos_x
            dz_ball = ball_z - player.pos_z
            dist_to_ball = math.hypot(dx_ball, dz_ball)

            # 3. Spatial Decision Making
            if dist_to_ball < 15.0:
                # If the ball enters their zone (15m radius), swarm it
                target_x, target_z = ball_x, ball_z  
            else:
                # Otherwise, maintain formation, but shift the defensive line based on ball position
                target_x = home_x + (ball_x * 0.15)
                target_z = home_z + (ball_z * 0.15)

            # 4. Integrate velocity into position (Max sprint speed: 5 m/s)
            dx_target = target_x - player.pos_x
            dz_target = target_z - player.pos_z
            dist_to_target = math.hypot(dx_target, dz_target)

            if dist_to_target > 0.2:  # Prevent jittering when they reach the target
                speed = 5.0 * (1.0 / 60.0)  # Distance covered per 16.66ms tick
                
                # Normalize the vector and apply velocity
                player.pos_x += (dx_target / dist_to_target) * speed
                player.pos_z += (dz_target / dist_to_target) * speed

            # 5. Always rotate their body to face the ball
            player.facing_angle_rad = math.atan2(dz_ball, dx_ball)