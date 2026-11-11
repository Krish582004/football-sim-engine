import asyncio
import time
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from simulation_engine import SimulationEngine

app = FastAPI(title="VectorPitch 2027 Deterministic Match Server", version="2.7.0")
engine = SimulationEngine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    state = engine.get_current_state()
    return {
        "status": "ok",
        "tick": state.tick_number,
        "hash": state.state_checksum,
        "score": {"blue": state.score_team_0, "red": state.score_team_1},
        "stats": state.stats.__dict__
    }

@app.post("/rollback")
def trigger_rollback(payload: dict):
    target_tick = payload.get("target_tick", max(0, engine.latest_tick - 15))
    corrected_input = payload.get("input", {"dx": 1.0, "dz": -0.5, "sprint": True})
    return engine.rollback_and_resimulate(target_tick, corrected_input)

@app.websocket("/ws")
async def match_stream(websocket: WebSocket):
    await websocket.accept()
    print("WebGL Client Connected! Enabling 60Hz Bi-Directional Rollback Netcode...")

    async def receive_inputs():
        try:
            while True:
                data = await websocket.receive_text()
                input_payload = json.loads(data)

                if input_payload.get("action") == "switch_player":
                    engine.ai.switch_human_to_nearest(engine.current_match_state, 0)
                    continue
                if input_payload.get("action") == "set_tactics":
                    engine.current_match_state.team_0_mentality = input_payload.get("mentality", "BALANCED")
                    engine.current_match_state.team_0_formation = input_payload.get("formation", "1-2-1")
                    continue

                # Route input to active human-controlled player
                human_player = next((p for p in engine.current_match_state.players if p.is_human), engine.current_match_state.players[0])
                human_player.input_dx = input_payload.get("dx", 0.0)
                human_player.input_dz = input_payload.get("dz", 0.0)
                human_player.input_sprint = input_payload.get("sprint", False)
                human_player.input_shoot = input_payload.get("shoot", False)
                human_player.input_finesse = input_payload.get("finesse", False)
                human_player.input_power_shot = input_payload.get("power_shot", False)
                human_player.input_pass = input_payload.get("pass", False)
                human_player.input_through_pass = input_payload.get("through_pass", False)
                human_player.input_lofted_pass = input_payload.get("lofted_pass", False)
                human_player.shot_charge = input_payload.get("shot_charge", 0.8)
        except WebSocketDisconnect:
            pass

    input_task = asyncio.create_task(receive_inputs())

    TICK_RATE = 1.0 / 60.0
    try:
        while True:
            start_time = time.perf_counter()

            engine.step()
            state = engine.get_current_state()

            payload = {
                "tick": state.tick_number,
                "hash": state.state_checksum,
                "score": {
                    "blue": state.score_team_0,
                    "red": state.score_team_1
                },
                "stats": state.stats.__dict__,
                "events": state.recent_events[-3:],
                "ball": {
                    "x": state.ball.pos_x,
                    "y": state.ball.pos_y,
                    "z": state.ball.pos_z,
                    "vx": state.ball.vel_x,
                    "vy": state.ball.vel_y,
                    "vz": state.ball.vel_z,
                    "spin_y": state.ball.spin_y
                },
                "players": [
                    {
                        "id": p.player_id,
                        "name": p.name,
                        "number": p.shirt_number,
                        "x": p.pos_x,
                        "y": p.pos_y,
                        "z": p.pos_z,
                        "angle": p.facing_angle_rad,
                        "stamina": round(p.stamina, 1),
                        "pose": p.current_anim_pose_id,
                        "phase": round(p.anim_phase, 2),
                        "team": p.tactical_role,
                        "is_human": p.is_human,
                        "has_possession": p.has_possession,
                        "playstyle": p.playstyle,
                        "playstyle_plus": p.playstyle_plus
                    } for p in state.players
                ]
            }
            await websocket.send_text(json.dumps(payload))

            elapsed = time.perf_counter() - start_time
            sleep_time = TICK_RATE - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            else:
                await asyncio.sleep(0)

    except WebSocketDisconnect:
        input_task.cancel()
        print("Client disconnected.")