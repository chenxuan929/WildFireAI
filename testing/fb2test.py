import numpy as np
import matplotlib.pyplot as plt
import math
import random

# -----------------------------
# Create Grid with Fuel Loads
# -----------------------------

def create_grid(n=20):
    grid = []
    for i in range(n):
        row = []
        for j in range(n):
            fuel = np.random.randint(1, 10)  # fuel load between 1 and 9
            row.append({'fuel_type': fuel})
        grid.append(row)
    return grid

# -----------------------------
# Firebreak Class
# -----------------------------

class Firebreak:
    def __init__(self, grid):
        self.grid = grid
        self.n = len(grid)
        self.randomize()

    def randomize(self):
        self.start_i = random.randint(0, self.n - 1)
        self.start_j = random.randint(0, self.n - 1)
        self.angle_deg = random.choice([0, 45, 90, 135, 180, 225, 270, 315])
        self.length = random.randint(5, 15)  # or any length range you want
        self.cells = []
        self.draw()

    def draw(self):
        self.clear()
        angle_rad = math.radians(self.angle_deg)
        step_i = int(round(np.sin(angle_rad)))
        step_j = int(round(np.cos(angle_rad)))
        i, j = self.start_i, self.start_j

        for _ in range(self.length):
            if 0 <= i < self.n and 0 <= j < self.n:
                self.grid[i][j]['fuel_type'] = 0  # firebreak = no fuel
                self.cells.append((i, j))
            i += step_i
            j += step_j

    def clear(self):
        # optional if you want to re-place randomly later
        pass


# Visualization with Numbers


def visualize_grid(grid):
    n = len(grid)
    data = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            data[i][j] = grid[i][j]['fuel_type']

    plt.clf()
    cmap = plt.cm.get_cmap('Greens', 9)
    cmap.set_under('white')  # fuel=0 will appear white (firebreak)

    plt.imshow(data, cmap=cmap, vmin=0.5, vmax=9.5, origin='lower', extent=[0, n, 0, n], interpolation='nearest')

    # Draw grid
    for x in range(n + 1):
        plt.plot([x, x], [0, n], color='black', linewidth=0.5)
    for y in range(n + 1):
        plt.plot([0, n], [y, y], color='black', linewidth=0.5)

    # Label cells with fuel numbers
    for i in range(n):
        for j in range(n):
            val = int(data[i][j])
            color = 'black' if val > 0 else 'red'
            plt.text(j + 0.5, i + 0.5, str(val), color=color,
                     va='center', ha='center', fontsize=8)

    plt.xticks(range(0, n + 1))
    plt.yticks(range(0, n + 1))
    plt.xlim(0, n)
    plt.ylim(0, n)
    plt.gca().set_aspect('equal')
    plt.title(" Fuel Load Grid + Firebreak (Fuel=0) ")
    plt.show()


#  Generate + Display


grid = create_grid()
firebreak = Firebreak(grid)
visualize_grid(grid)

