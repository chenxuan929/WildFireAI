import numpy as np
import pickle
import random
import math
import matplotlib.pyplot as plt
from firebreak_utils import Firebreak
from fire_spread_sim_without_fb import run_fire_simulation_without_fb
import fire_spread_sim

# Constants
GRID_SIZE = 30
MAX_ITERS = 40
INITIAL_TEMP = 1.0
COOLING_RATE = 0.95

def compute_unburned_area(state):
    return np.sum(state == 0)

def compute_firebreak_area(mask):
    return np.sum(mask)

def objective(unburned_area, firebreak_area, max_area):
    return (unburned_area / max_area) - 0.001 * (firebreak_area / max_area)

def get_neighbors(params):
    neighbors = []
    for di in [-1, 0, 1]:
        for dj in [-1, 0, 1]:
            for d_angle in [-45, 0, 45]:
                for d_len in [-2, 0, 2]:
                    if di == 0 and dj == 0 and d_angle == 0 and d_len == 0:
                        continue
                    new_i = min(max(0, params["start_i"] + di), GRID_SIZE - 1)
                    new_j = min(max(0, params["start_j"] + dj), GRID_SIZE - 1)
                    new_angle = (params["angle"] + d_angle) % 360
                    new_length = min(max(5, params["length"] + d_len), 25)
                    neighbors.append({
                        "start_i": new_i,
                        "start_j": new_j,
                        "angle": new_angle,
                        "length": new_length
                    })
    return neighbors

def create_firebreak(params):
    with open("saved_grid.pkl", "rb") as f:
        temp_grid = pickle.load(f)

    fb = Firebreak(temp_grid, length_range=(params["length"], params["length"]), angles=[params["angle"]])
    fb.start_i = params["start_i"]
    fb.start_j = params["start_j"]
    fb.angle_deg = params["angle"]
    fb.length = params["length"]
    fb.firebreak_mask[:] = False
    fb.cells.clear()
    fb.apply_firebreak()
    return temp_grid, fb

def simulated_annealing():
    print("Loading saved grid...")
    baseline_state = run_fire_simulation_without_fb(iterations=30, display=False)
    baseline_unburned = compute_unburned_area(baseline_state)
    max_possible = GRID_SIZE * GRID_SIZE

    print(f"Baseline unburned area: {baseline_unburned}/{max_possible}")
    print("Starting Simulated Annealing...\n")

    best_cost = -np.inf
    current_params = {
        "start_i": random.randint(0, GRID_SIZE - 1),
        "start_j": random.randint(0, GRID_SIZE - 1),
        "angle": random.choice([0, 45, 90, 135, 180, 225, 270, 315]),
        "length": random.randint(10, 25)
    }

    temp = INITIAL_TEMP
    best_params = None

    for step in range(MAX_ITERS):
        neighbors = get_neighbors(current_params)
        new_params = random.choice(neighbors)

        MAX_RETRIES = 10
        retry_count = 0
        new_unburned = GRID_SIZE * GRID_SIZE
        new_state = None
        new_fb = None
        new_grid = None

        while retry_count < MAX_RETRIES:
            new_grid, new_fb = create_firebreak(new_params)
            pickle.dump(new_grid, open("temp_grid.pkl", "wb"))
            fire_spread_sim.grid = new_grid
            new_state = fire_spread_sim.run_fire_simulation(iterations=30, display=False, reset=True)

            new_unburned = compute_unburned_area(new_state)
            new_burned = GRID_SIZE * GRID_SIZE - new_unburned
            if new_unburned <= 880 and new_burned > new_params["length"] + 20:
                break
            retry_count += 1

        if retry_count == MAX_RETRIES and new_unburned > 880:
            print(f"[Step {step}]  Skipped: Fire did not spread after {MAX_RETRIES} retries (Unburned: {new_unburned})")
            continue

        new_area = compute_firebreak_area(new_fb.firebreak_mask)
        new_cost = objective(new_unburned, new_area, max_possible)

        cost_diff = new_cost - best_cost
        accepted = False

        if cost_diff > 0 or np.random.rand() < math.exp(cost_diff / temp):
            current_params = new_params
            accepted = True
            if new_cost > best_cost:
                best_cost = new_cost
                best_params = new_params
                with open("best_final_grid.pkl", "wb") as f:
                    pickle.dump(new_grid, f)

        status = "Accepted" if accepted else "Rejected"
        print(f"[Step {step}] Temp: {temp:.4f} | Cost: {new_cost:.4f} | Best: {best_cost:.4f} | {status} "
              f"| Start: ({new_params['start_i']},{new_params['start_j']}) | Len: {new_params['length']} | "
              f"Angle: {new_params['angle']} | Unburned: {new_unburned}")

        temp *= COOLING_RATE

    print("\nOptimization complete!")
    if best_params:
        print(f"Best Firebreak Params: {best_params}")
        visualize_best_firebreak_on_clean_grid(best_params)

#  Visualize firebreak-only on clean grid
def visualize_best_firebreak_on_clean_grid(best_params):
    with open("saved_grid.pkl", "rb") as f:
        clean_grid = pickle.load(f)

    # Initialize without placing random firebreak
    fb = Firebreak(clean_grid, length_range=(best_params["length"], best_params["length"]), angles=[best_params["angle"]])

    # Overwrite with best SA values
    fb.start_i = best_params["start_i"]
    fb.start_j = best_params["start_j"]
    fb.angle_deg = best_params["angle"]
    fb.length = best_params["length"]

    # Clear mask and reapply firebreak with new settings
    fb.firebreak_mask[:] = False
    fb.cells.clear()
    fb.apply_firebreak()  # This must be called AFTER updating the params

    firebreak_mask = fb.firebreak_mask

    # Plot grid with only the best firebreak
    fig, ax = plt.subplots(figsize=(8, 8))
    color_matrix = np.empty((GRID_SIZE, GRID_SIZE), dtype=object)

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if firebreak_mask[i][j]:
                color_matrix[i, j] = "white"
            else:
                color_matrix[i, j] = clean_grid[i][j]["fuel_type_color"]

    ax.set_xlim(0, GRID_SIZE)
    ax.set_ylim(0, GRID_SIZE)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal')
    ax.set_title("Best Firebreak Placement Only")

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            ax.add_patch(
                plt.Rectangle((j, GRID_SIZE - i - 1), 1, 1,
                              facecolor=color_matrix[i, j], edgecolor='black')
            )

    plt.tight_layout()
    plt.show()
    plt.close(fig)

if __name__ == "__main__":
    simulated_annealing()

