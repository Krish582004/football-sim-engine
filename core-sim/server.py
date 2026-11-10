import asyncio
import time
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from simulation_engine import SimulationEngine

app = FastAPI()
engine = SimulationEngine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def match_stream(websocket: WebSocket):
    await websocket.accept()
    print("WebGL Client Connected! Enabling Bi-Directional Netcode...")
    
    # 1. Background Task: Listen for keyboard inputs
    async def receive_inputs():
        try:
            while True:
                data = await websocket.receive_text()
                input_payload = json.loads(data)
                
                engine.current_match_state.players[0].input_dx = input_payload.get("dx", 0)
                engine.current_match_state.players[0].input_dz = input_payload.get("dz", 0)
                engine.current_match_state.players[0].input_sprint = input_payload.get("sprint", False)
                engine.current_match_state.players[0].input_shoot = input_payload.get("shoot", False)
                engine.current_match_state.players[0].input_pass = input_payload.get("pass", False)
                engine.current_match_state.players[0].input_lofted_pass = input_payload.get("lofted_pass", False) # NEW
        except WebSocketDisconnect:
            pass

    input_task = asyncio.create_task(receive_inputs())
    
    # 2. Main Loop: Strict 60Hz Physics
    TICK_RATE = 1 / 60.0
    try:
        while True:
            start_time = time.perf_counter()
            
            engine.step()
            state = engine.get_current_state()
            
           # 3. Serialize coordinates to JSON (Phase 6: Added Hash & Possession)
            # 3. Serialize coordinates to JSON
            payload = {
                "tick": state.tick_number,
                "hash": state.state_checksum,
                "score": {
                    "blue": state.score_team_0,
                    "red": state.score_team_1
                },
                "ball": { "x": state.ball.pos_x, "y": state.ball.pos_y, "z": state.ball.pos_z },
                "players": [
                    { 
                        "x": p.pos_x, 
                        "y": p.pos_y, 
                        "z": p.pos_z, 
                        "team": p.tactical_role,
                        "has_possession": p.has_possession,
                        "playstyle": p.playstyle  # NEW: Send the EAFC PlayStyle
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