import math
import random
from match_state import MatchFrameState

class TacticalAI:
    def __init__(self):
        self.team_0_home = [(-40, 0), (-20, -15), (-20, 15), (-5, 0), (-48, 0)] # Player 4 is GK
        self.team_1_home = [(40, 0), (20, -15), (20, 15), (5, 0), (48, 0)]      # Player 9 is GK

    def initialize_match(self, state: MatchFrameState):
        for i in range(5):
            p = state.players[i]
            p.pos_x, p.pos_y, p.pos_z = self.team_0_home[i][0], 1.0, self.team_0_home[i][1]
            p.tactical_role = 0 

        for i in range(5, 10):
            p = state.players[i]
            p.pos_x, p.pos_y, p.pos_z = self.team_1_home[i-5][0], 1.0, self.team_1_home[i-5][1]
            p.tactical_role = 1 
            
        # Human Striker (Gold)
        state.players[0].is_human = True; state.players[0].playstyle = "Sniper"
        state.players[0].shot_power = 28.0; state.players[0].curve_ability = 40.0
        
        # Speedsters (Wingers)
        for i in [1, 2, 6, 7]:
            state.players[i].playstyle = "Speedster"
            state.players[i].pace = 7.5
            
        # Bruisers (Defenders)
        state.players[3].playstyle = "Bruiser"; state.players[8].playstyle = "Bruiser"

        # NEW: Goalkeepers
        state.players[4].playstyle = "Goalkeeper"
        state.players[9].playstyle = "Goalkeeper"

    def update_agents(self, state: MatchFrameState):
        ball = state.ball

        for i, player in enumerate(state.players):
            # --- NEW: GOALKEEPER LOGIC ---
            if player.playstyle == "Goalkeeper":
                # Lock to the goal line (X = -48 for Blue, X = 48 for Red)
                target_x = -48.0 if player.tactical_role == 0 else 48.0
                
                # Slide Z to match the ball, but clamp it within the 7.32m goalposts (+/- 3.66)
                target_z = max(-3.66, min(3.66, ball.pos_z))
                
                dx_target = target_x - player.pos_x
                dz_target = target_z - player.pos_z
                dist_to_target = math.hypot(dx_target, dz_target)
                
                if dist_to_target > 0.1:
                    speed = 7.0 * (1.0 / 60.0) # GK lateral dive speed
                    player.pos_x += (dx_target / dist_to_target) * speed
                    player.pos_z += (dz_target / dist_to_target) * speed
                
                player.facing_angle_rad = math.atan2(ball.pos_z - player.pos_z, ball.pos_x - player.pos_x)
                continue # Skip the outfield player logic below

            # --- OUTFIELD PLAYER LOGIC ---
            home_x, home_z = self.team_0_home[i] if i < 5 else self.team_1_home[i - 5]
            dx_ball = ball.pos_x - player.pos_x
            dz_ball = ball.pos_z - player.pos_z
            dist_to_ball = math.hypot(dx_ball, dz_ball)
            tackle_radius = 0.8 if player.playstyle == "Bruiser" else 0.5
            
            if dist_to_ball < tackle_radius and ball.pos_y < 1.0:
                player.has_possession = True
                should_shoot = True if (player.is_human and player.input_shoot) or not player.is_human else False

                if should_shoot:
                    target_goal_x = 50.0 if player.tactical_role == 0 else -50.0
                    kick_dx = target_goal_x - player.pos_x
                    kick_dz = (0.0 - player.pos_z) + random.uniform(-2.0, 2.0) 
                    kick_mag = math.hypot(kick_dx, kick_dz)
                    
                    ball.vel_x = (kick_dx / kick_mag) * player.shot_power
                    ball.vel_y = random.uniform(3.0, 6.0)
                    ball.vel_z = (kick_dz / kick_mag) * player.shot_power
                    ball.spin_y = random.uniform(-player.curve_ability, player.curve_ability)
            else:
                player.has_possession = False

            current_pace = player.pace * 1.5 if (player.is_human and player.input_sprint) else player.pace

            if player.is_human:
                mag = math.hypot(player.input_dx, player.input_dz)
                if mag > 0:
                    speed = current_pace * (1.0 / 60.0)
                    player.pos_x += (player.input_dx / mag) * speed
                    player.pos_z += (player.input_dz / mag) * speed
                    player.facing_angle_rad = math.atan2(player.input_dz, player.input_dx)
            else:
                target_x, target_z = (ball.pos_x, ball.pos_z) if dist_to_ball < 15.0 else (home_x + (ball.pos_x * 0.15), home_z + (ball.pos_z * 0.15))
                dx_target = target_x - player.pos_x
                dz_target = target_z - player.pos_z
                dist_to_target = math.hypot(dx_target, dz_target)

                if dist_to_target > 0.2 and not player.has_possession:  
                    speed = current_pace * (1.0 / 60.0)  
                    player.pos_x += (dx_target / dist_to_target) * speed
                    player.pos_z += (dz_target / dist_to_target) * speed
                player.facing_angle_rad = math.atan2(dz_ball, dx_ball)