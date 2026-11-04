import asyncio
import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from simulation_engine import SimulationEngine

app = FastAPI()
engine = SimulationEngine()

# Allow the HTML frontend to connect
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
    print("WebGL Client Connected! Streaming 60Hz Match Data...")
    
    try:
        while True:
            # 1. Advance the simulation
            engine.step()
            state = engine.get_current_state()
            
                
            # 3. Serialize coordinates to JSON
            payload = {
                "tick": state.tick_number,
                "ball": {
                    "x": state.ball.pos_x,
                    "y": state.ball.pos_y,
                    "z": state.ball.pos_z
                },
                "players": [
                    {
                        "x": p.pos_x, 
                        "y": p.pos_y, 
                        "z": p.pos_z, 
                        "team": p.tactical_role
                    } for p in state.players
                ]
            }
            
            # 4. Stream to browser
            await websocket.send_text(json.dumps(payload))
            
            # 5. Hardware sleep to maintain exact 60Hz tick rate
            await asyncio.sleep(1 / 60.0)
            
    except Exception as e:
        print("Client disconnected.")