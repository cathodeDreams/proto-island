from dataclasses import dataclass
import numpy as np
from typing import Tuple, List
import scipy.signal
from scipy.ndimage import label

@dataclass
class CaveParams:
    """Parameters for cave generation using cellular automata."""
    initial_fill_probability: float  # Probability of a cell being a wall initially
    birth_limit: int  # Number of neighbors needed for a cell to become a wall
    death_limit: int  # Number of neighbors needed for a wall to remain a wall
    iterations: int  # Number of cellular automata iterations

class CaveGenerator:
    """Generates cave layouts using cellular automata."""
    
    def __init__(self, params: CaveParams):
        """Initialize the cave generator with given parameters.
        
        Args:
            params: Parameters controlling the cave generation process
        """
        self.params = params
    
    def generate(self, width: int, height: int, seed: int | None = None) -> np.ndarray:
        """Generate a new cave layout.
        
        Args:
            width: Width of the cave area
            height: Height of the cave area
            seed: Random seed for generation
            
        Returns:
            np.ndarray: 2D boolean array where True represents walls
        """
        rng = np.random.RandomState(seed)
        
        # Initialize random cave layout
        cave = rng.random((height, width)) < self.params.initial_fill_probability
        
        # Run cellular automata iterations
        for _ in range(self.params.iterations):
            cave = self._apply_automata_rules(cave)
        
        # Ensure cave is connected
        cave = self._ensure_connectivity(cave, rng)
        
        return cave
    
    def _apply_automata_rules(self, cave: np.ndarray) -> np.ndarray:
        """Apply one iteration of cellular automata rules.
        
        Args:
            cave: Current cave layout
            
        Returns:
            np.ndarray: New cave layout after applying rules
        """
        # Count neighbors using convolution
        kernel = np.ones((3, 3))
        kernel[1, 1] = 0  # Don't count the cell itself
        neighbor_count = scipy.signal.convolve2d(
            cave.astype(int),
            kernel,
            mode='same'
        )
        
        # Apply cellular automata rules
        new_cave = np.copy(cave)
        new_cave[neighbor_count >= self.params.birth_limit] = True   # Birth rule
        new_cave[neighbor_count < self.params.death_limit] = False  # Death rule
        
        # Ensure border is walls
        new_cave[0, :] = True
        new_cave[-1, :] = True
        new_cave[:, 0] = True
        new_cave[:, -1] = True
        
        return new_cave
    
    def _ensure_connectivity(self, cave: np.ndarray, rng: np.random.RandomState) -> np.ndarray:
        """Ensure all open areas in the cave are connected.
        
        Args:
            cave: Current cave layout
            rng: Random number generator
            
        Returns:
            np.ndarray: Cave layout with all areas connected
        """
        # Find distinct regions
        open_space = ~cave  # Invert to get open spaces
        labeled_array, num_features = label(open_space)
        
        if num_features <= 1:
            return cave  # Already connected
        
        # Find sizes of all regions
        region_sizes = np.zeros(num_features + 1, dtype=int)
        for i in range(1, num_features + 1):
            region_sizes[i] = np.sum(labeled_array == i)
        
        # Find the largest region
        largest_region = np.argmax(region_sizes[1:]) + 1
        
        # Connect other regions to the largest one
        connected_cave = cave.copy()
        for region in range(1, num_features + 1):
            if region == largest_region:
                continue
                
            # Find points in current region
            points = np.where(labeled_array == region)
            if len(points[0]) == 0:
                continue
                
            # Find points in largest region
            largest_points = np.where(labeled_array == largest_region)
            
            # Find closest point pair between regions
            min_dist = float('inf')
            best_path = None
            
            # Sample points to reduce computation
            num_samples = min(20, len(points[0]))
            sampled_indices = rng.choice(len(points[0]), num_samples, replace=False)
            
            for idx in sampled_indices:
                y1, x1 = points[0][idx], points[1][idx]
                
                # Sample points from largest region
                num_target_samples = min(20, len(largest_points[0]))
                target_indices = rng.choice(len(largest_points[0]), num_target_samples, replace=False)
                
                for target_idx in target_indices:
                    y2, x2 = largest_points[0][target_idx], largest_points[1][target_idx]
                    
                    # Calculate Manhattan distance
                    dist = abs(x2 - x1) + abs(y2 - y1)
                    if dist < min_dist:
                        min_dist = dist
                        best_path = [(y1, x1), (y2, x2)]
            
            if best_path:
                # Create tunnel between regions
                y1, x1 = best_path[0]
                y2, x2 = best_path[1]
                
                # Determine intermediate points for the tunnel
                points_to_clear = []
                
                # First go horizontally
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    points_to_clear.append((y1, x))
                
                # Then vertically
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    points_to_clear.append((y, x2))
                
                # Clear the tunnel
                for y, x in points_to_clear:
                    connected_cave[y, x] = False
                    
                    # Clear a 1-tile buffer around the tunnel for better playability
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            ny, nx = y + dy, x + dx
                            if (0 < ny < cave.shape[0] - 1 and 
                                0 < nx < cave.shape[1] - 1):
                                connected_cave[ny, nx] = False
        
        return connected_cave 