import math
import random
from match_state import MatchFrameState
from physics_engine import PhysicsEngine

FORMATIONS_5V5 = {
    "1-2-1": {
        0: [(-5, 0), (-20, -15), (-20, 15), (-35, 0), (-48, 0)],
        1: [(5, 0), (20, -15), (20, 15), (35, 0), (48, 0)],
    },
    "2-1-1": {
        0: [(-6, 0), (-18, 0), (-32, -12), (-32, 12), (-48, 0)],
        1: [(6, 0), (18, 0), (32, -12), (32, 12), (48, 0)],
    },
    "1-1-2": {
        0: [(-6, -10), (-6, 10), (-22, 0), (-36, 0), (-48, 0)],
        1: [(6, -10), (6, 10), (22, 0), (36, 0), (48, 0)],
    }
}

MENTALITY_SHIFT = {
    "ULTRA_DEFENSIVE": -10.0,
    "BALANCED": 0.0,
    "GEGENPRESS": 6.5,
    "ALL_OUT_ATTACK": 12.0,
}

class TacticalAI:
    def __init__(self):
        self.team_0_home = [(-5, 0), (-20, -15), (-20, 15), (-35, 0), (-48, 0)]
        self.team_1_home = [(5, 0), (20, -15), (20, 15), (35, 0), (48, 0)]

    def initialize_match(self, state: MatchFrameState):
        blue_roster = [
            ("K. Mbappe-Sim", 9, "ST", "Poacher+", "Sniper", "Finesse Shot+", 91, 8.2, 28.0, 40.0),
            ("V. Junior-Sim", 7, "LW", "Inside Forward++", "Speedster", "Rapid+", 90, 8.4, 24.0, 32.0),
            ("L. Yamal-Sim", 19, "RW", "Winger+", "Speedster", "Technical+", 88, 7.9, 22.0, 35.0),
            ("R. Dias-Sim", 3, "CB", "Stopper+", "Bruiser", "Bruiser+", 89, 6.5, 20.0, 14.0),
            ("T. Courtois-Sim", 1, "GK", "Sweeper Keeper+", "Goalkeeper", "Acrobatic GK+", 90, 7.0, 22.0, 10.0),
        ]
        red_roster = [
            ("E. Haaland-Sim", 9, "ST", "Poacher+", "Sniper", "Power Shot+", 91, 8.0, 30.0, 24.0),
            ("J. Bellingham-Sim", 5, "LW", "Shadow Striker+", "Speedster", "Relentless+", 90, 7.6, 25.0, 28.0),
            ("P. Foden-Sim", 47, "RW", "Playmaker+", "Speedster", "Finesse Shot+", 88, 7.7, 23.0, 34.0),
            ("V. van Dijk-Sim", 4, "CB", "Ball-Playing CB+", "Bruiser", "Aerial+", 90, 6.8, 21.0, 15.0),
            ("Alisson-Sim", 1, "GK", "Goalkeeper+", "Goalkeeper", "Rush Out+", 89, 7.0, 22.0, 10.0),
        ]

        for i in range(5):
            p = state.players[i]
            name, num, pos, role, pstyle, pplus, ovr, pace, spow, curve = blue_roster[i]
            p.player_id = i
            p.name = name
            p.shirt_number = num
            p.position_code = pos
            p.fc_iq_role = role
            p.playstyle = pstyle
            p.playstyle_plus = pplus
            p.overall = ovr
            p.pace = pace
            p.shot_power = spow
            p.curve_ability = curve
            p.pos_x, p.pos_y, p.pos_z = self.team_0_home[i][0], 1.0, self.team_0_home[i][1]
            p.tactical_role = 0
            p.stamina = 100.0
            p.is_human = (i == 0)

        for i in range(5, 10):
            p = state.players[i]
            name, num, pos, role, pstyle, pplus, ovr, pace, spow, curve = red_roster[i - 5]
            p.player_id = i
            p.name = name
            p.shirt_number = num
            p.position_code = pos
            p.fc_iq_role = role
            p.playstyle = pstyle
            p.playstyle_plus = pplus
            p.overall = ovr
            p.pace = pace
            p.shot_power = spow
            p.curve_ability = curve
            p.pos_x, p.pos_y, p.pos_z = self.team_1_home[i - 5][0], 1.0, self.team_1_home[i - 5][1]
            p.tactical_role = 1
            p.stamina = 100.0
            p.is_human = False

    def switch_human_to_nearest(self, state: MatchFrameState, team: int = 0) -> int:
        """Switches human indicator to the outfield teammate closest to the ball."""
        ball = state.ball
        best_idx = 0
        best_dist = float("inf")
        start = 0 if team == 0 else 5
        for idx in range(start, start + 4):  # exclude GK at +4
            p = state.players[idx]
            d = math.hypot(ball.pos_x - p.pos_x, ball.pos_z - p.pos_z)
            if d < best_dist:
                best_dist = d
                best_idx = idx
        for idx in range(start, start + 5):
            state.players[idx].is_human = (idx == best_idx)
        return best_idx

    def update_agents(self, state: MatchFrameState):
        ball = state.ball
        formation_0 = FORMATIONS_5V5.get(state.team_0_formation, FORMATIONS_5V5["1-2-1"])[0]
        formation_1 = FORMATIONS_5V5.get(state.team_1_formation, FORMATIONS_5V5["1-2-1"])[1]

        for i, player in enumerate(state.players):
            if player.tackle_cooldown > 0:
                player.tackle_cooldown -= 1

            # --- 1. GOALKEEPER LOGIC ---
            if player.playstyle == "Goalkeeper":
                target_x = -48.0 if player.tactical_role == 0 else 48.0
                target_z = max(-3.66, min(3.66, ball.pos_z))

                dx_target = target_x - player.pos_x
                dz_target = target_z - player.pos_z
                dist_to_target = math.hypot(dx_target, dz_target)

                if dist_to_target > 0.1:
                    speed = 7.2 * (1.0 / 60.0)
                    player.pos_x += (dx_target / dist_to_target) * speed
                    player.pos_z += (dz_target / dist_to_target) * speed
                    player.current_anim_pose_id = 5 if dist_to_target > 1.2 else 1
                else:
                    player.current_anim_pose_id = 0

                # Goalkeeper clearance when ball is close in box
                dist_ball_gk = math.hypot(ball.pos_x - player.pos_x, ball.pos_z - player.pos_z)
                if dist_ball_gk < 0.9 and ball.pos_y < 2.2:
                    clear_dir = 1.0 if player.tactical_role == 0 else -1.0
                    ball.vel_x = clear_dir * 22.0
                    ball.vel_y = 7.5
                    ball.vel_z = random.uniform(-8.0, 8.0)
                    ball.last_touched_by = i

                player.facing_angle_rad = math.atan2(ball.pos_z - player.pos_z, ball.pos_x - player.pos_x)
                continue

            # --- 2. OUTFIELD PLAYER LOGIC ---
            base_home = formation_0[i] if i < 5 else formation_1[i - 5]
            mentality = state.team_0_mentality if i < 5 else state.team_1_mentality
            shift_dir = 1.0 if i < 5 else -1.0
            home_x = max(-45.0, min(45.0, base_home[0] + shift_dir * MENTALITY_SHIFT.get(mentality, 0.0)))
            home_z = base_home[1]

            dx_ball = ball.pos_x - player.pos_x
            dz_ball = ball.pos_z - player.pos_z
            dist_to_ball = math.hypot(dx_ball, dz_ball)
            tackle_radius = 0.85 if player.playstyle == "Bruiser" else 0.55

            if dist_to_ball < tackle_radius and ball.pos_y < 1.15:
                player.has_possession = True
                ball.last_touched_by = i
                if player.tactical_role == 0:
                    state.stats.possession_ticks_0 += 1
                else:
                    state.stats.possession_ticks_1 += 1

                # A. Human Passing Logic (E: Ground Pass, Q: Through Ball, F: Lofted Pass)
                if player.is_human and (player.input_pass or player.input_through_pass or player.input_lofted_pass):
                    team_start = 0 if player.tactical_role == 0 else 5
                    target_mate = None
                    if player.input_lofted_pass:
                        max_dist = -1.0
                        for j in range(team_start, team_start + 5):
                            if j == i:
                                continue
                            mate = state.players[j]
                            d = math.hypot(mate.pos_x - player.pos_x, mate.pos_z - player.pos_z)
                            if d > max_dist:
                                max_dist = d
                                target_mate = mate
                    else:
                        min_dist = float("inf")
                        for j in range(team_start, team_start + 5):
                            if j == i:
                                continue
                            mate = state.players[j]
                            d = math.hypot(mate.pos_x - player.pos_x, mate.pos_z - player.pos_z)
                            if d < min_dist:
                                min_dist = d
                                target_mate = mate

                    if target_mate:
                        lead_x = 6.0 if (player.input_through_pass and player.tactical_role == 0) else (-6.0 if player.input_through_pass else 0.0)
                        pass_dx = (target_mate.pos_x + lead_x) - player.pos_x
                        pass_dz = target_mate.pos_z - player.pos_z
                        pass_mag = max(0.1, math.hypot(pass_dx, pass_dz))

                        if player.input_lofted_pass:
                            ball.vel_x = (pass_dx / pass_mag) * 18.0
                            ball.vel_y = 8.0
                            ball.vel_z = (pass_dz / pass_mag) * 18.0
                            ball.spin_y = random.uniform(-15.0, 15.0)
                        elif player.input_through_pass:
                            ball.vel_x = (pass_dx / pass_mag) * 22.5
                            ball.vel_y = 1.2
                            ball.vel_z = (pass_dz / pass_mag) * 22.5
                            ball.spin_y = 0.0
                        else:
                            ball.vel_x = (pass_dx / pass_mag) * 20.0
                            ball.vel_y = 1.0
                            ball.vel_z = (pass_dz / pass_mag) * 20.0
                            ball.spin_y = 0.0

                        if player.tactical_role == 0:
                            state.stats.passes_attempted_0 += 1
                            state.stats.passes_completed_0 += 1
                        else:
                            state.stats.passes_attempted_1 += 1
                            state.stats.passes_completed_1 += 1
                        player.current_anim_pose_id = 3

                # B. Shooting Logic (Spacebar for Human, Tactical Decision for AI)
                elif (player.is_human and player.input_shoot) or (not player.is_human):
                    target_goal_x = 50.0 if player.tactical_role == 0 else -50.0
                    dist_to_goal = abs(target_goal_x - player.pos_x)

                    # AI passes to an advanced teammate if far from goal (> 28m), otherwise shoots
                    if not player.is_human and dist_to_goal > 28.0:
                        team_start = 0 if player.tactical_role == 0 else 5
                        forward_mate = state.players[team_start]  # striker
                        if forward_mate.player_id != player.player_id:
                            pdx = forward_mate.pos_x - player.pos_x
                            pdz = forward_mate.pos_z - player.pos_z
                            pmag = max(0.1, math.hypot(pdx, pdz))
                            ball.vel_x = (pdx / pmag) * 19.5
                            ball.vel_y = 1.5
                            ball.vel_z = (pdz / pmag) * 19.5
                            if player.tactical_role == 0:
                                state.stats.passes_attempted_0 += 1
                                state.stats.passes_completed_0 += 1
                            else:
                                state.stats.passes_attempted_1 += 1
                                state.stats.passes_completed_1 += 1
                            player.current_anim_pose_id = 3
                            continue

                    kick_dx = target_goal_x - player.pos_x
                    aim_z = random.uniform(-2.6, 2.6)
                    kick_dz = aim_z - player.pos_z
                    kick_mag = max(0.1, math.hypot(kick_dx, kick_dz))

                    charge_mult = max(0.55, min(1.25, player.shot_charge if player.is_human else 0.95))
                    power = player.shot_power * charge_mult
                    if player.input_power_shot:
                        power *= 1.22
                    ball.vel_x = (kick_dx / kick_mag) * power
                    ball.vel_y = random.uniform(3.2, 6.2) * charge_mult
                    ball.vel_z = (kick_dz / kick_mag) * power

                    if player.input_finesse:
                        ball.spin_y = player.curve_ability * (1.25 if aim_z >= 0 else -1.25)
                    else:
                        ball.spin_y = random.uniform(-player.curve_ability, player.curve_ability)

                    xg = PhysicsEngine.calculate_shot_xg(
                        player.pos_x, player.pos_z, target_goal_x,
                        is_finesse=player.input_finesse, is_power=player.input_power_shot
                    )
                    ball.last_shot_xg = xg
                    if player.tactical_role == 0:
                        state.stats.shots_0 += 1
                        state.stats.shots_on_target_0 += 1
                        state.stats.xg_0 = round(state.stats.xg_0 + xg, 2)
                    else:
                        state.stats.shots_1 += 1
                        state.stats.shots_on_target_1 += 1
                        state.stats.xg_1 = round(state.stats.xg_1 + xg, 2)
                    player.current_anim_pose_id = 3
            else:
                player.has_possession = False

            # Stamina & Pace Calculation
            stamina_factor = 0.75 + 0.25 * (player.stamina / max(1.0, player.stamina_max))
            sprinting = player.is_human and player.input_sprint and player.stamina > 5.0
            if sprinting:
                player.stamina = max(0.0, player.stamina - 0.08)
            else:
                player.stamina = min(player.stamina_max, player.stamina + 0.03)

            current_pace = player.pace * stamina_factor * (1.45 if sprinting else 1.0)

            if player.is_human:
                mag = math.hypot(player.input_dx, player.input_dz)
                if mag > 0:
                    speed = current_pace * (1.0 / 60.0)
                    vx = (player.input_dx / mag) * current_pace
                    vz = (player.input_dz / mag) * current_pace
                    player.vel_x, player.vel_z = vx, vz
                    player.pos_x += (player.input_dx / mag) * speed
                    player.pos_z += (player.input_dz / mag) * speed
                    player.facing_angle_rad = math.atan2(player.input_dz, player.input_dx)
                    player.current_anim_pose_id = 2 if sprinting else 1
                    player.anim_phase = (player.anim_phase + speed * 3.2) % (2 * math.pi)
                else:
                    player.vel_x, player.vel_z = 0.0, 0.0
                    player.current_anim_pose_id = 0
            else:
                press_radius = 19.0 if mentality in ("GEGENPRESS", "ALL_OUT_ATTACK") else 15.0
                target_x, target_z = (
                    (ball.pos_x, ball.pos_z)
                    if dist_to_ball < press_radius
                    else (home_x + (ball.pos_x * 0.18), home_z + (ball.pos_z * 0.18))
                )
                dx_target = target_x - player.pos_x
                dz_target = target_z - player.pos_z
                dist_to_target = math.hypot(dx_target, dz_target)

                if dist_to_target > 0.2 and not player.has_possession:
                    speed = current_pace * (1.0 / 60.0)
                    player.vel_x = (dx_target / dist_to_target) * current_pace
                    player.vel_z = (dz_target / dist_to_target) * current_pace
                    player.pos_x += (dx_target / dist_to_target) * speed
                    player.pos_z += (dz_target / dist_to_target) * speed
                    player.current_anim_pose_id = 1
                    player.anim_phase = (player.anim_phase + speed * 3.0) % (2 * math.pi)
                else:
                    player.vel_x, player.vel_z = 0.0, 0.0
                    player.current_anim_pose_id = 0
                player.facing_angle_rad = math.atan2(dz_ball, dx_ball)