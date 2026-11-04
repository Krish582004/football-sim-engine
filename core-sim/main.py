import time
from simulation_engine import SimulationEngine

def main():
    engine = SimulationEngine()
    print("Starting 60Hz Deterministic Match Engine (Python)...")

    TICK_RATE = 1 / 60.0  # 16.66ms per tick

    # Run for 60 frames (1 second of game time)
    for _ in range(60):
        start_time = time.perf_counter()

        engine.step()
        state = engine.get_current_state()
        print(f"Tick: {state.tick_number:02d} | Hash: {state.state_checksum}")

        # Hardware-accurate sleep to maintain 60Hz
        elapsed = time.perf_counter() - start_time
        sleep_time = TICK_RATE - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

    print("Phase 1 Engine test completed successfully!")

if __name__ == "__main__":
    main()