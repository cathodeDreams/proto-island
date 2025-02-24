from enum import Enum
import numpy as np
from tcod import libtcodpy
from tcod.noise import Noise
from tcod.random import Random
from .lighting import LightingSystem, TimeOfDay

class TerrainType(Enum):
    """Enum representing different terrain types in the game."""
    WATER = 0
    BEACH = 1
    GRASS = 2
    ROCK = 3
    FOREST = 4
    CAVE_WALL = 5
    CAVE_FLOOR = 6
    CAVE_ENTRANCE = 7
    
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

class GameMap:
    """Represents the game's map with terrain and various game mechanics."""
    
    def __init__(self, width: int, height: int):
        """Initialize a new game map with the specified dimensions.
        
        Args:
            width: The width of the map in tiles
            height: The height of the map in tiles
        """
        self.width = width
        self.height = height
        
        # Z-level management
        self.current_z = 0
        self.z_levels = {0: {
            'tiles': np.full((height, width), TerrainType.GRASS, dtype=object),
            'heightmap': np.zeros((height, width), dtype=np.float32),
            'lighting': LightingSystem(width, height)
        }}
        
        # Level transition storage
        self.level_transitions = {0: {}}  # {z_level: {target_z: [(x, y), ...]}}
        
        # Reference current level's data
        self.tiles = self.z_levels[0]['tiles']
        self._heightmap = self.z_levels[0]['heightmap']
        self.lighting = self.z_levels[0]['lighting']
    
    def add_z_level(self, z: int) -> None:
        """Add a new z-level to the map.
        
        Args:
            z: The z-coordinate of the new level (positive = up, negative = down)
        """
        if z in self.z_levels:
            raise ValueError(f"Z-level {z} already exists")
        
        self.z_levels[z] = {
            'tiles': np.full((self.height, self.width), TerrainType.GRASS, dtype=object),
            'heightmap': np.zeros((self.height, self.width), dtype=np.float32),
            'lighting': LightingSystem(self.width, self.height)
        }
        self.level_transitions[z] = {}
    
    def change_level(self, z: int) -> None:
        """Change the current z-level.
        
        Args:
            z: The z-level to change to
            
        Raises:
            ValueError: If the target z-level doesn't exist
        """
        if z not in self.z_levels:
            raise ValueError(f"Z-level {z} does not exist")
        
        # Store current level's state
        self.z_levels[self.current_z]['tiles'] = self.tiles.copy()
        self.z_levels[self.current_z]['heightmap'] = self._heightmap.copy()
        
        # Change level
        self.current_z = z
        level_data = self.z_levels[z]
        
        # Update references to current level's data
        self.tiles = level_data['tiles'].copy()
        self._heightmap = level_data['heightmap'].copy()
        self.lighting = level_data['lighting']
    
    def add_level_transition(self, from_z: int, to_z: int, x: int, y: int) -> None:
        """Add a transition point between z-levels.
        
        Args:
            from_z: The source z-level
            to_z: The target z-level
            x: X-coordinate of the transition point
            y: Y-coordinate of the transition point
            
        Raises:
            ValueError: If either z-level doesn't exist
        """
        if from_z not in self.z_levels or to_z not in self.z_levels:
            raise ValueError("Source or target z-level does not exist")
        
        # Add transition to source level
        if to_z not in self.level_transitions[from_z]:
            self.level_transitions[from_z][to_z] = []
        self.level_transitions[from_z][to_z].append((x, y))
        
        # Add reciprocal transition
        if from_z not in self.level_transitions[to_z]:
            self.level_transitions[to_z][from_z] = []
        self.level_transitions[to_z][from_z].append((x, y))
    
    def get_level_transitions(self, z: int) -> dict:
        """Get all transitions from a z-level.
        
        Args:
            z: The z-level to query
            
        Returns:
            dict: Mapping of target z-levels to lists of transition coordinates
            
        Raises:
            ValueError: If the z-level doesn't exist
        """
        if z not in self.z_levels:
            raise ValueError(f"Z-level {z} does not exist")
        return self.level_transitions[z].copy()
    
    def in_bounds(self, x: int, y: int) -> bool:
        """Check if the given coordinates are within the map bounds.
        
        Args:
            x: The x coordinate to check
            y: The y coordinate to check
            
        Returns:
            bool: True if the coordinates are within bounds, False otherwise
        """
        return 0 <= x < self.width and 0 <= y < self.height
    
    def generate_terrain(self, seed: int = None) -> None:
        """Generate the terrain using noise and heightmap functions.
        
        Args:
            seed: Random seed for terrain generation
        """
        # Create noise generator
        noise = Noise(
            dimensions=2,
            algorithm=libtcodpy.NOISE_SIMPLEX,
            seed=seed,
            octaves=6,
            lacunarity=2.5,
            hurst=0.9
        )
        
        # Generate base terrain using noise
        scale = 4.0  # Controls the size of terrain features
        
        # Pre-calculate normalized coordinates and circular mask
        y_coords = np.linspace(-0.5, 0.5, self.height)[:, np.newaxis]
        x_coords = np.linspace(-0.5, 0.5, self.width)[np.newaxis, :]
        dx = x_coords * 2
        dy = y_coords * 2
        d = 1.0 - np.sqrt(dx*dx + dy*dy)  # Distance from center
        
        # Generate noise grid using vectorized operations
        coords = np.stack(
            np.meshgrid(x_coords[0] * scale, y_coords[:, 0] * scale),
            axis=-1
        )
        noise_grid = np.array([noise[tuple(coord)] for coord in coords.reshape(-1, 2)]).reshape(self.height, self.width)
        
        # Apply transformations to noise grid
        self._heightmap = (noise_grid + 1.0) / 2.0  # Convert from [-1,1] to [0,1]
        self._heightmap *= d  # Apply island mask
        
        # Store the generated heightmap in the current z-level
        self.z_levels[self.current_z]['heightmap'] = self._heightmap.copy()
        
        # Normalize heightmap to [0,1]
        self._normalize_heightmap()
        self._apply_heightmap_to_terrain()
        
        # Store the generated terrain in the current z-level
        self.z_levels[self.current_z]['tiles'] = self.tiles.copy()
    
    def add_terrain_features(self, seed: int = None) -> None:
        """Add terrain features like hills and apply erosion.
        
        Args:
            seed: Random seed for feature generation
        """
        rng = np.random.RandomState(seed)
        
        # Store original heightmap for comparison
        heightmap_before = self._heightmap.copy()
        
        # Add some hills
        num_hills = rng.randint(10, 20)
        for _ in range(num_hills):
            x = rng.randint(0, self.width)
            y = rng.randint(0, self.height)
            radius = rng.uniform(5, 15)
            height = rng.uniform(0.2, 0.4)
            self._add_hill(x, y, radius, height)
        
        # Apply erosion
        self._apply_erosion(rng)
        
        # Ensure the terrain features have created higher elevations
        if np.max(self._heightmap) <= np.max(heightmap_before):
            # Scale up the new features to ensure they create peaks
            scale_factor = 1.5
            diff = self._heightmap - heightmap_before
            self._heightmap = heightmap_before + diff * scale_factor
        
        # Normalize and update terrain
        self._normalize_heightmap()
        self._apply_heightmap_to_terrain()
    
    def get_heightmap(self) -> np.ndarray:
        """Get a copy of the current heightmap data.
        
        Returns:
            np.ndarray: 2D array of height values
        """
        return self._heightmap.copy()
    
    def _normalize_heightmap(self) -> None:
        """Normalize heightmap values to range [0,1]."""
        min_height = np.min(self._heightmap)
        max_height = np.max(self._heightmap)
        if max_height > min_height:
            self._heightmap = (self._heightmap - min_height) / (max_height - min_height)
    
    def _add_hill(self, cx: float, cy: float, radius: float, height: float) -> None:
        """Add a hill to the heightmap.
        
        Args:
            cx: Center x coordinate
            cy: Center y coordinate
            radius: Radius of the hill
            height: Height of the hill
        """
        radius_sq = radius * radius
        min_x = max(0, int(cx - radius))
        max_x = min(self.width, int(cx + radius + 1))
        min_y = max(0, int(cy - radius))
        max_y = min(self.height, int(cy + radius + 1))
        
        y_coords = np.arange(min_y, max_y)[:, np.newaxis]
        x_coords = np.arange(min_x, max_x)
        
        dy = y_coords - cy
        dx = x_coords - cx
        dist_sq = dx*dx + dy*dy
        mask = dist_sq < radius_sq
        factor = np.where(mask, (1 - dist_sq/radius_sq) * height, 0)
        self._heightmap[min_y:max_y, min_x:max_x] += factor
    
    def _apply_erosion(self, rng: np.random.RandomState) -> None:
        """Apply hydraulic erosion to the heightmap.
        
        Args:
            rng: Random number generator
        """
        # Simple hydraulic erosion
        num_drops = rng.randint(8000, 12000)
        erosion_factor = 0.05
        deposit_factor = 0.05
        
        # Pre-calculate neighbor offsets
        neighbors = np.array([(-1,0), (1,0), (0,-1), (0,1)])
        
        for _ in range(num_drops):
            # Start at random position
            x = rng.randint(1, self.width-2)
            y = rng.randint(1, self.height-2)
            sediment = 0.0
            
            for _ in range(30):  # Max steps per droplet
                current_height = self._heightmap[y, x]
                
                # Calculate height differences for all neighbors
                neighbor_coords = np.array([[y+dy, x+dx] for dy, dx in neighbors])
                valid_mask = (
                    (neighbor_coords[:, 0] >= 0) & 
                    (neighbor_coords[:, 0] < self.height) &
                    (neighbor_coords[:, 1] >= 0) & 
                    (neighbor_coords[:, 1] < self.width)
                )
                
                if not np.any(valid_mask):
                    break
                
                valid_coords = neighbor_coords[valid_mask]
                height_diffs = current_height - self._heightmap[valid_coords[:, 0], valid_coords[:, 1]]
                
                if not np.any(height_diffs > 0):
                    # Deposit sediment at local minimum
                    self._heightmap[y, x] += sediment
                    break
                
                # Find steepest descent
                steepest_idx = np.argmax(height_diffs)
                next_y, next_x = valid_coords[steepest_idx]
                steepest_diff = height_diffs[steepest_idx]
                
                # Erode current position and move
                eroded = steepest_diff * erosion_factor
                self._heightmap[y, x] -= eroded
                sediment += eroded
                
                # Deposit some sediment
                deposit = sediment * deposit_factor
                self._heightmap[y, x] += deposit
                sediment -= deposit
                
                x, y = next_x, next_y
    
    def _apply_heightmap_to_terrain(self) -> None:
        """Convert heightmap values to terrain types."""
        # Only apply terrain conversion if we're at surface level (z >= 0)
        if self.current_z >= 0:
            self.tiles = np.where(self._heightmap < 0.3, TerrainType.WATER,
                       np.where(self._heightmap < 0.35, TerrainType.BEACH,
                       np.where(self._heightmap < 0.7, TerrainType.GRASS,
                       np.where(self._heightmap < 0.8, TerrainType.ROCK,
                       TerrainType.FOREST))))
        # For underground levels, preserve cave terrain
        else:
            cave_mask = (self.tiles == TerrainType.CAVE_WALL) | (self.tiles == TerrainType.CAVE_FLOOR)
            self.tiles = np.where(cave_mask, self.tiles,
                       np.where(self._heightmap < 0.3, TerrainType.CAVE_FLOOR,
                       TerrainType.CAVE_WALL))
        
        # Update lighting system's surface reflectivity
        self.lighting.update_surface_reflectivity(self._heightmap, np.array([[t.value for t in row] for row in self.tiles]))
    
    def update_lighting(self) -> None:
        """Update the lighting system for the current game state."""
        self.lighting.update()
    
    def get_light_level(self, x: int, y: int) -> float:
        """Get the light level at the specified coordinates.
        
        Args:
            x: The x coordinate
            y: The y coordinate
            
        Returns:
            float: Light level from 0.0 to 1.0
        """
        return self.lighting.get_light_level(x, y)
    
    def set_time(self, hour: int, minute: int) -> None:
        """Set the current time of day.
        
        Args:
            hour: Hour of the day (0-23)
            minute: Minute of the hour (0-59)
        """
        self.lighting.time = TimeOfDay(
            hour=hour,
            minute=minute,
            base_intensity=1.0,
            color_temperature=5500.0
        )

    def apply_cave_layout(self, cave_layout: np.ndarray) -> None:
        """Apply a cave layout to the current z-level.
        
        Args:
            cave_layout: Boolean array where True represents walls
        """
        if cave_layout.shape != (self.height, self.width):
            raise ValueError("Cave layout dimensions must match map dimensions")
        
        # Convert cave layout to terrain types
        self.tiles = np.where(
            cave_layout,
            TerrainType.CAVE_WALL,
            TerrainType.CAVE_FLOOR
        )
        
        # Update heightmap to reflect cave structure
        self._heightmap = np.where(
            cave_layout,
            0.8,  # Cave walls are high
            0.2   # Cave floors are low
        ).astype(np.float32)

    def generate_cave_entrance(self, seed: int | None = None) -> tuple[int, int]:
        """Generate a cave entrance on the current level.
        
        Args:
            seed: Random seed for entrance placement
            
        Returns:
            tuple[int, int]: (x, y) coordinates of the entrance
        """
        rng = np.random.RandomState(seed)
        
        # Find suitable locations (not water or beach)
        suitable = np.where(
            (self.tiles != TerrainType.WATER) &
            (self.tiles != TerrainType.BEACH)
        )
        
        if len(suitable[0]) == 0:
            raise ValueError("No suitable location for cave entrance")
        
        # Choose random suitable location
        idx = rng.randint(len(suitable[0]))
        entrance_y, entrance_x = suitable[0][idx], suitable[1][idx]
        
        # Mark entrance on current level
        self.tiles[entrance_y, entrance_x] = TerrainType.CAVE_ENTRANCE
        
        # Ensure underground level exists
        if -1 not in self.z_levels:
            self.add_z_level(-1)
        
        # Add transition points
        self.add_level_transition(self.current_z, -1, entrance_x, entrance_y)
        
        return entrance_x, entrance_y 