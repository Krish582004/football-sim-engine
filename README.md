# VectorPitch 2027 (`football-sim-engine`)

A portfolio-grade 3D football simulation engine and interactive web game combining **EAFC 27** (*FC IQ Roles*, *PlayStyles+*, *5v5 Rush*, *Ultimate Squad Builder*, *Manager Career*) and **eFootball 2027** (*Team Playstyle Tactics*, *Stunning Power Shots*, *Point-Based Player Progression*) on top of a **240Hz sub-stepped aerodynamics physics solver** and **60Hz GGPO-style rollback netcode architecture**.

---

## Architecture & Module Map

```text
football-sim-engine/
├── core-sim/
│   ├── MatchState.h          # Cache-aligned C++ structs (PlayerState, BallState, FNV-1a checksum)
│   ├── match_state.py        # Dataclass state representation + MD5 deterministic frame hashing
│   ├── physics_engine.py     # 240Hz sub-stepped solver (Quadratic Air Drag, Magnus Curl/Dip, Turf & Post Collisions, xG model)
│   ├── tactical_ai.py        # Spatial AI, Dynamic Formations (1-2-1, 2-1-1, 1-1-2), Team Mentalities, PlayStyles+
│   ├── simulation_engine.py  # 300-frame Ring Buffer, Referee & Goal Detection, GGPO Rollback & Resimulation
│   ├── server.py             # FastAPI 60Hz Bi-Directional WebSocket & Rollback Telemetry Server
│   └── main.py               # Headless CLI physics benchmark harness
├── netcode/
│   └── RollbackNetcode.h     # C++ ring-buffer state snapshot & checksum verification header
├── ai-locomotion/
│   ├── MotionMatcher.h       # C++ HyperMotion-inspired pose feature vector & cost evaluator
│   └── motion_matching.py    # Procedural gait phase & skeletal limb rotation synthesizer
├── match-microservice/
│   └── matchmaker.py         # ELO matchmaking & Monte Carlo / Poisson league fixture simulator
├── client-visualizer/
│   └── index.html            # Self-contained 3D WebGL Game (Three.js r128 + Chart.js + Hybrid Local/WebSocket Netcode)
├── docs/
│   └── ARCHITECTURE.md       # Mathematical derivations, netcode design, and CV/Interview talking points
└── tests/
    └── test_engine.py        # Automated deterministic physics, AI, xG, and rollback netcode test suite
```

---

## Key Engineering Highlights

1. **240Hz Sub-Stepped Ball Aerodynamics (`core-sim/physics_engine.py`)**:
   - Solves quadratic air drag $\vec{F}_d = -\frac{1}{2} \rho A C_d \|\vec{v}\| \vec{v}$ and the **Magnus Effect** $\vec{F}_m = S_0 (\vec{\omega} \times \vec{v})$ at $\Delta t = \frac{1}{240}\text{ s}$ (4 sub-steps per $60\text{ Hz}$ network tick) to model realistic Finesse curls, dipping power shots, and lofted through-balls without numerical tunneling.
2. **GGPO-Style Rollback Netcode & Deterministic State Hashing (`core-sim/simulation_engine.py`, `netcode/RollbackNetcode.h`)**:
   - Captures complete match snapshots in a 300-frame circular ring buffer with per-tick FNV-1a / MD5 checksums. Supports instant state rewind (`rollback_and_resimulate`), late input injection, and sub-millisecond forward resimulation.
3. **Hybrid Standalone + WebSocket 3D Client (`client-visualizer/index.html`)**:
   - Runs 100% standalone in any browser at up to 144Hz using an embedded port of the deterministic 240Hz physics & tactical AI engine, while also supporting live WebSocket streaming (`ws://localhost:8000/ws`) when paired with `core-sim/server.py`.

---

## Quick Start

### Option A: Instant Standalone Browser Mode (Zero Install)
Open `client-visualizer/index.html` directly in any modern browser. The client automatically runs the local 60Hz/240Hz deterministic simulation loop, 3D WebGL stadium renderer, Tactical Board, Ultimate Squad Lab, Career Mode, and Wind-Tunnel / Netcode Telemetry Lab.

### Option B: Run Python FastAPI WebSocket Server + Unit Tests
```bash
# Run deterministic physics & rollback netcode unit tests
python3 -m unittest discover -s tests -v

# Start the 60Hz FastAPI WebSocket server
cd core-sim
uvicorn server:app --host 0.0.0.0 --port 8000
```
