import numpy as np
import matplotlib.pyplot as plt
import math

def create_grid(n=20):
    return [[{'firebreak': False} for _ in range(n)] for _ in range(n)]

class Firebreak:
    def __init__(self, grid, start_i, start_j, angle_deg, length):
        self.grid = grid
        self.start_i = start_i
        self.start_j = start_j
        self.angle_deg = angle_deg
        self.length = length
        self.cells = []

    def clear(self):
        for i, j in self.cells:
            if 0 <= i < len(self.grid) and 0 <= j < len(self.grid[0]):
                self.grid[i][j]['firebreak'] = False
        self.cells = []

    def snap_angle(self):
        allowed_angles = [0, 45, 90, 135, 180, 225, 270, 315]
        closest = min(allowed_angles, key=lambda x: abs(x - self.angle_deg))
        return closest

    def draw(self):
        self.clear()

        angle_deg_snapped = self.snap_angle()
        angle_rad = math.radians(angle_deg_snapped)

        step_i = int(round(np.sin(angle_rad)))
        step_j = int(round(np.cos(angle_rad)))

        i, j = self.start_i, self.start_j

        for _ in range(self.length):
            if 0 <= i < len(self.grid) and 0 <= j < len(self.grid[0]):
                self.grid[i][j]['firebreak'] = True
                self.cells.append((i, j))
            i += step_i
            j += step_j

    def move(self, delta_i, delta_j):
        self.start_i += delta_i
        self.start_j += delta_j
        self.draw()

    def rotate(self, delta_angle):
        self.angle_deg = (self.angle_deg + delta_angle) % 360
        self.draw()

    def resize(self, delta_length):
        self.length = max(1, self.length + delta_length)
        self.draw()

def visualize_grid(grid):
    n = len(grid)
    data = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if grid[i][j]['firebreak']:
                data[i][j] = 1

    plt.clf()
    plt.imshow(data, cmap='Greys', origin='lower', extent=[0, n, 0, n])

    # ✅ Only draw major gridlines
    plt.xticks(range(0, n+1))
    plt.yticks(range(0, n+1))
    plt.grid(True, which='major', color='black', linewidth=0.5)

    plt.xlim(0, n)
    plt.ylim(0, n)
    plt.gca().set_aspect('equal')
    plt.draw()
 

def firebreak_editor():
    grid = create_grid()
    fb = Firebreak(grid, start_i=10, start_j=10, angle_deg=45, length=8)
    fb.draw()
    plt.figure(figsize=(6,6))
    visualize_grid(grid)

    def on_key(event):
        if event.key == 'up':
            fb.move(1, 0)
        elif event.key == 'down':
            fb.move(-1, 0)
        elif event.key == 'left':
            fb.move(0, -1)
        elif event.key == 'right':
            fb.move(0, 1)
        elif event.key == 'r':
            fb.rotate(45)
        elif event.key == '+':
            fb.resize(1)
        elif event.key == '-':
            fb.resize(-1)
        elif event.key == 'q':
            plt.close()
            return
        visualize_grid(grid)

    plt.gcf().canvas.mpl_connect('key_press_event', on_key)
    plt.show()   # <-- do not use plt.pause() anymore

# -----------------------------
# ✅ Launch
# -----------------------------

firebreak_editor()
