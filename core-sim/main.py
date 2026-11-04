import time
from simulation_engine import SimulationEngine

def main():
    engine = SimulationEngine()
    print("Starting Phase 2: Magnus Aerodynamics Test...")

    TICK_RATE = 1 / 60.0  

    # Run for 90 frames (1.5 seconds) to watch the bounce and curve
    for _ in range(90):
        start_time = time.perf_counter()
        engine.step()
        state = engine.get_current_state()
        
        # Print the Ball's 3D Trajectory
        x = state.ball.pos_x
        y = state.ball.pos_y
        z = state.ball.pos_z
        print(f"Tick: {state.tick_number:02d} | Ball Pos -> X: {x:5.2f}, Y: {y:5.2f}, Z: {z:5.2f}")

        elapsed = time.perf_counter() - start_time
        sleep_time = TICK_RATE - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

if __name__ == "__main__":
    main()