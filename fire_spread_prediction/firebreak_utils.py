import numpy as np
import random
import math

class Firebreak:
    def __init__(self, grid, length_range=(5, 15), angles=[0, 45, 90, 135, 180, 225, 270, 315]):
        self.grid = grid
        self.n = len(grid)
        self.length_range = length_range
        self.angles = angles
        self.firebreak_mask = np.zeros((self.n, self.n), dtype=bool)
        self.cells = []
        self.place_random_firebreak()

    def place_random_firebreak(self):
        self.start_i = random.randint(0, self.n - 1)
        self.start_j = random.randint(0, self.n - 1)
        self.angle_deg = random.choice(self.angles)
        self.length = random.randint(*self.length_range)
        self.apply_firebreak()

    def apply_firebreak(self):
        angle_rad = math.radians(self.angle_deg)
        step_i = int(round(np.sin(angle_rad)))
        step_j = int(round(np.cos(angle_rad)))
        i, j = self.start_i, self.start_j

        for _ in range(self.length):
            if 0 <= i < self.n and 0 <= j < self.n:
                self.grid[i][j]['fuel_type'] = "NB"  # Non-burnable: triggers 0 ROS
                self.grid[i][j]['fuel_type_color'] = "white"  # So it's visible in simulation
                self.firebreak_mask[i][j] = True
                self.cells.append((i, j))
            i += step_i
            j += step_j
