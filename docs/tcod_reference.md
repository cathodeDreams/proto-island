# TCOD Reference Guide

## Overview
This document collects useful patterns, code examples, and implementation details from the python-tcod examples that are relevant to Proto Island. It serves as a reference for key functionality we may want to incorporate or learn from.

## Table of Contents
1. [Cave Generation](#cave-generation)
2. [Field of View & Lighting](#fov-and-lighting)
3. [BSP Room Generation](#bsp-room-generation)
4. [Noise Generation](#noise-generation)
5. [Performance Patterns](#performance-patterns)
6. [Input Handling](#input-handling)
7. [Rendering Techniques](#rendering-techniques)

## Cave Generation {#cave-generation}

The cave generation system uses cellular automata to create natural-looking cave layouts. Key components:

```python
def generate_cave(width: int, height: int, wall_rule: int = 5) -> np.ndarray:
    """Generate a cave using cellular automata.
    
    Args:
        width: Width of the cave
        height: Height of the cave
        wall_rule: Number of neighboring walls needed to create a wall (default 5)
        
    Returns:
        Boolean array where True represents walkable space
    """
    # Initial random cave with ~45% walls
    cave = np.random.random((height, width)) > 0.45
    
    for _ in range(4):  # Number of iterations
        # Count walls in 3x3 neighborhood
        neighbors = scipy.signal.convolve2d(
            cave == 0,  # Convert to 0s and 1s
            [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
            'same'
        )
        # Apply the wall rule
        cave = neighbors < wall_rule
        
    return cave

def ensure_connectivity(cave: np.ndarray) -> np.ndarray:
    """Ensure all open areas are connected.
    
    Uses flood fill to identify and connect separate chambers.
    """
    # Implementation would go here
    pass
```

Key parameters that affect cave generation:
- Initial fill probability (0.45 works well)
- Wall rule threshold (4-5 creates natural looking caves)
- Number of iterations (3-4 is usually sufficient)
- Minimum room size for connectivity

Variations we could implement:
- Multiple layers of caves with connecting tunnels
- Different rules for different depths
- Integration with water features
- Support for placed features (crystals, ore veins, etc)

## Field of View & Lighting {#fov-and-lighting}

The FOV system demonstrates several useful patterns for visibility and lighting:

```python
class LightingSystem:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.light_levels = np.zeros((height, width), dtype=np.float32)
        self.natural_light = np.zeros_like(self.light_levels)
        self.artificial_light = np.zeros_like(self.light_levels)
        self.reflected_light = np.zeros_like(self.light_levels)
        
    def calculate_fov(self, x: int, y: int, radius: int, transparent: np.ndarray) -> np.ndarray:
        """Calculate field of view from a point."""
        return tcod.map.compute_fov(
            transparency=transparent,
            pov=(x, y),
            radius=radius,
            light_walls=True,
            algorithm=tcod.FOV_SYMMETRIC_SHADOWCAST
        )
        
    def apply_light_source(self, x: int, y: int, intensity: float, color: tuple[int, int, int]):
        """Add a point light source."""
        # Create distance array using numpy broadcasting
        yy, xx = np.mgrid[:self.height, :self.width]
        dist_squared = (xx - x) ** 2 + (yy - y) ** 2
        
        # Light falls off with inverse square
        light = intensity / (1 + dist_squared)
        
        # Add colored light
        for i, channel in enumerate(color):
            self.artificial_light[..., i] += light * (channel / 255.0)
            
    def update(self, time_of_day: float):
        """Update lighting for current time of day."""
        # Base ambient light varies with time
        ambient = 0.2 + 0.6 * math.sin(time_of_day * math.pi)
        self.natural_light.fill(ambient)
        
        # Combine light sources
        self.light_levels = (
            self.natural_light + 
            self.artificial_light +
            self.reflected_light
        ).clip(0, 1)
```

Notable features:
- Efficient numpy operations for light calculations
- Support for colored lighting
- Natural day/night cycle
- Light reflection from surfaces
- Multiple lighting algorithms available

## BSP Room Generation {#bsp-room-generation}

The Binary Space Partition (BSP) system provides a robust way to generate connected rooms:

```python
class BSPNode:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.children: tuple[BSPNode, BSPNode] | None = None
        
    def split(self, min_size: int) -> bool:
        """Split node into two children if possible."""
        if self.width < min_size * 2 or self.height < min_size * 2:
            return False
            
        # Choose split direction based on aspect ratio
        horizontal = self.width / self.height >= 1.0
        
        if horizontal:
            split_at = random.randint(min_size, self.width - min_size)
            left = BSPNode(self.x, self.y, split_at, self.height)
            right = BSPNode(self.x + split_at, self.y, self.width - split_at, self.height)
        else:
            split_at = random.randint(min_size, self.height - min_size)
            left = BSPNode(self.x, self.y, self.width, split_at)
            right = BSPNode(self.x, self.y + split_at, self.width, self.height - split_at)
            
        self.children = (left, right)
        return True
        
    def create_rooms(self) -> list[tuple[int, int, int, int]]:
        """Create rooms in leaf nodes."""
        if not self.children:
            # This is a leaf node, create a room
            room_width = random.randint(3, self.width - 2)
            room_height = random.randint(3, self.height - 2)
            room_x = self.x + random.randint(1, self.width - room_width - 1)
            room_y = self.y + random.randint(1, self.height - room_height - 1)
            return [(room_x, room_y, room_width, room_height)]
            
        # Recurse on children
        rooms = []
        for child in self.children:
            rooms.extend(child.create_rooms())
        return rooms
```

Key considerations:
- Minimum room size affects layout density
- Room placement within nodes can be random or centered
- Corridor generation between rooms
- Support for special rooms (entrances, treasures, etc)

## Noise Generation {#noise-generation}

The noise generation system shows how to create natural-looking terrain:

```python
def create_heightmap(width: int, height: int, scale: float = 1.0) -> np.ndarray:
    """Generate a heightmap using multiple octaves of noise."""
    noise = tcod.noise.Noise(
        dimensions=2,
        algorithm=tcod.NOISE_SIMPLEX,
        implementation=tcod.noise.Implementation.FBM,
        hurst=0.5,
        lacunarity=2.0,
        octaves=4.0,
    )
    
    # Generate coordinates
    xc = np.linspace(0, scale, width)
    yc = np.linspace(0, scale, height)
    xx, yy = np.meshgrid(xc, yc)
    
    # Get noise values
    heightmap = np.zeros((height, width))
    for y in range(height):
        for x in range(width):
            heightmap[y,x] = noise.get_point(xx[y,x], yy[y,x])
            
    return heightmap

def apply_erosion(heightmap: np.ndarray, iterations: int = 1000) -> np.ndarray:
    """Apply hydraulic erosion to a heightmap."""
    # Implementation would go here
    pass
```

Useful variations:
- Multiple noise layers for different features
- Erosion simulation for realistic terrain
- Mask application for island shapes
- Biome definition based on height/moisture

## Performance Patterns {#performance-patterns}

Several performance optimization patterns are demonstrated:

```python
# Use numpy operations instead of loops where possible
def calculate_distances(x: int, y: int, width: int, height: int) -> np.ndarray:
    """Calculate distances from a point to all other points."""
    yy, xx = np.meshgrid(range(height), range(width))
    return np.sqrt((xx - x)**2 + (yy - y)**2)

# Efficient light calculation
def calculate_light_mask(radius: int) -> np.ndarray:
    """Pre-calculate a circular light mask."""
    y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
    mask = x*x + y*y <= radius*radius
    return mask.astype(float) / (radius * radius)

# Texture management
class TextureManager:
    def __init__(self):
        self._textures = {}
        
    def get_texture(self, name: str) -> np.ndarray:
        """Get or load a texture."""
        if name not in self._textures:
            self._textures[name] = self._load_texture(name)
        return self._textures[name]
```

Key performance tips:
- Use numpy operations for bulk calculations
- Pre-calculate static data
- Cache frequently used resources
- Use appropriate data structures
- Profile and optimize hot spots

## Input Handling {#input-handling}

The event system shows good patterns for input handling:

```python
class InputHandler(tcod.event.EventDispatch[None]):
    def __init__(self):
        self.mouse_pos = (0, 0)
        self.keys_pressed = set()
        
    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        """Track mouse position."""
        self.mouse_pos = event.tile.x, event.tile.y
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        """Track pressed keys."""
        self.keys_pressed.add(event.sym)
        
    def ev_keyup(self, event: tcod.event.KeyUp) -> None:
        """Remove released keys."""
        self.keys_pressed.discard(event.sym)
        
    def handle_input(self) -> None:
        """Process current input state."""
        for event in tcod.event.get():
            self.dispatch(event)
```

Useful patterns:
- Event dispatch system
- State tracking
- Mouse position handling
- Key combination support

## Rendering Techniques {#rendering-techniques}

Various rendering techniques are demonstrated:

```python
class RenderSystem:
    def __init__(self, width: int, height: int):
        self.console = tcod.Console(width, height)
        self.light_console = tcod.Console(width, height)
        
    def render_map(self, game_map: np.ndarray, fov: np.ndarray):
        """Render the game map with FOV."""
        # Clear consoles
        self.console.clear()
        self.light_console.clear()
        
        # Draw terrain
        visible = fov > 0
        self.console.tiles_rgb[visible] = VISIBLE_TILES[game_map[visible]]
        self.console.tiles_rgb[~visible] = HIDDEN_TILES[game_map[~visible]]
        
        # Apply lighting
        np.multiply(
            self.console.tiles_rgb["fg"],
            self.light_console.tiles_rgb["fg"],
            out=self.console.tiles_rgb["fg"]
        )
```

Notable techniques:
- Multiple console layers
- Efficient array operations
- FOV integration
- Color manipulation
- Texture mapping

## Additional Resources

- [TCOD Documentation](https://python-tcod.readthedocs.io/)
- [Roguelike Tutorial](http://rogueliketutorials.com/)
- [TCOD GitHub](https://github.com/libtcod/python-tcod)

## Notes for Proto Island

The most immediately useful components for our project are:
1. The cave generation system for underground areas
2. The lighting system for day/night cycle
3. The BSP room generation for structures
4. The noise generation for terrain features
5. The performance patterns for large map handling

Consider implementing these in order of priority based on our current development stage. 