import numpy as np
import pygame
import matplotlib.pyplot as plt

# Grid dimensions
WIDTH, HEIGHT = 800, 600
CELL_SIZE = 10

# Colors
EMPTY = (0, 0, 0)  # Black
TREE = (0, 128, 0)  # Green
FIRE = (255, 0, 0)  # Red

# Probabilities
p_tree_growth = 0.05
p_lightning_strike = 0.001

# Simulation parameters
elevation_data = np.random.rand(HEIGHT // CELL_SIZE, WIDTH // CELL_SIZE)  # Example elevation data
moisture_data = np.random.rand(HEIGHT // CELL_SIZE, WIDTH // CELL_SIZE)  # Example moisture data
temperature_data = np.random.rand(HEIGHT // CELL_SIZE, WIDTH // CELL_SIZE)  # Example temperature data
land_cover_data = np.random.randint(0, 2, size=(HEIGHT // CELL_SIZE, WIDTH // CELL_SIZE))  # Example land cover data (0 = empty, 1 = tree)

def iterate(grid):
    new_grid = np.copy(grid)
    
    for y in range(grid.shape[0]):
        for x in range(grid.shape[1]):
            if grid[y, x] == 1:  # TREE
                # Check for fire spread
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < grid.shape[1] and 0 <= ny < grid.shape[0]:
                        if grid[ny, nx] == 2:  # FIRE
                            # Spread fire with a certain probability based on elevation, moisture, temperature
                            spread_prob = 0.5 * (1 - moisture_data[ny, nx]) * (1 + elevation_data[ny, nx] / 10) * (1 + temperature_data[ny, nx] / 10)
                            if np.random.random() < spread_prob:
                                new_grid[y, x] = 2
                                break
                # Lightning strike
                if np.random.random() < p_lightning_strike:
                    new_grid[y, x] = 2
            elif grid[y, x] == 0:  # EMPTY
                # Tree growth
                if np.random.random() < p_tree_growth:
                    new_grid[y, x] = 1
            elif grid[y, x] == 2:  # FIRE
                # Extinguish fire after one step
                new_grid[y, x] = 0
    
    return new_grid

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Initialize grid with some trees
    grid = np.zeros((HEIGHT // CELL_SIZE, WIDTH // CELL_SIZE))
    grid[1:-1, 1:-1] = np.random.choice([1, 0], size=(HEIGHT // CELL_SIZE - 2, WIDTH // CELL_SIZE - 2), p=[0.2, 0.8])

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        grid = iterate(grid)
        
        screen.fill(EMPTY)
        for y in range(grid.shape[0]):
            for x in range(grid.shape[1]):
                if grid[y, x] == 1:  # TREE
                    pygame.draw.rect(screen, TREE, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                elif grid[y, x] == 2:  # FIRE
                    pygame.draw.rect(screen, FIRE, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
