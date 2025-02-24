# TCOD Performance Optimization Guide

## Overview
This document focuses on performance optimization patterns from the TCOD examples, particularly relevant for Proto Island's large map sizes and complex systems.

## Table of Contents
1. [Numpy Optimizations](#numpy-optimizations)
2. [Memory Management](#memory-management)
3. [Parallel Processing](#parallel-processing)
4. [Rendering Optimizations](#rendering-optimizations)
5. [Data Structure Choices](#data-structures)

## Numpy Optimizations {#numpy-optimizations}

### Array Operations

Instead of using loops, use numpy's vectorized operations:

```python
# Slow way
def calculate_distances_slow(x: int, y: int, width: int, height: int) -> list[list[float]]:
    distances = []
    for i in range(height):
        row = []
        for j in range(width):
            dist = math.sqrt((j - x)**2 + (i - y)**2)
            row.append(dist)
        distances.append(row)
    return distances

# Fast way using numpy
def calculate_distances_fast(x: int, y: int, width: int, height: int) -> np.ndarray:
    yy, xx = np.meshgrid(range(height), range(width))
    return np.sqrt((xx - x)**2 + (yy - y)**2)

# Even faster for simple distance checks
def is_within_radius(x: int, y: int, radius: int, width: int, height: int) -> np.ndarray:
    yy, xx = np.ogrid[:height, :width]
    return (xx - x)**2 + (yy - y)**2 <= radius**2
```

### Memory Layout

Optimize memory layout for your access patterns:

```python
class OptimizedMap:
    def __init__(self, width: int, height: int):
        # Use 'F' order for column-major access (better for vertical operations)
        self.height_map = np.zeros((height, width), dtype=np.float32, order='F')
        self.terrain_types = np.zeros((height, width), dtype=np.int8, order='F')
        
        # Pre-allocate buffers for frequent operations
        self.light_buffer = np.zeros_like(self.height_map)
        self.fov_buffer = np.zeros_like(self.height_map, dtype=bool)
        
    def update_region(self, x: int, y: int, width: int, height: int):
        """Update a region of the map efficiently."""
        # Use views instead of copies
        region = self.height_map[y:y+height, x:x+width]
        region_terrain = self.terrain_types[y:y+height, x:x+width]
        
        # Operate on views directly
        region[region < 0.3] = 0  # water level
        region_terrain[region < 0.3] = TerrainType.WATER
```

### Masking and Boolean Operations

Use boolean masks for efficient filtering:

```python
class TerrainProcessor:
    def __init__(self, map_data: np.ndarray):
        self.map_data = map_data
        
    def get_buildable_areas(self) -> np.ndarray:
        """Find areas suitable for building."""
        # Combine multiple conditions efficiently
        return (
            (self.map_data > 0.3) &  # Above water
            (self.map_data < 0.7) &  # Below mountains
            (self.slope_map < 0.3)    # Not too steep
        )
        
    def apply_erosion(self, iterations: int):
        """Apply erosion to terrain."""
        # Use boolean masks to track affected areas
        affected = np.zeros_like(self.map_data, dtype=bool)
        kernel = np.array([[0.1, 0.2, 0.1],
                          [0.2, 0.0, 0.2],
                          [0.1, 0.2, 0.1]])
                          
        for _ in range(iterations):
            # Only process areas that need erosion
            mask = (self.map_data > 0.5) & ~affected
            if not np.any(mask):
                break
                
            # Apply erosion only to masked areas
            eroded = scipy.signal.convolve2d(
                self.map_data * mask,
                kernel,
                mode='same'
            )
            self.map_data[mask] = eroded[mask]
            affected |= mask
```

## Memory Management {#memory-management}

### Resource Pooling

```python
class ResourcePool:
    def __init__(self, initial_size: int = 100):
        self._available = []
        self._in_use = set()
        self.expand(initial_size)
        
    def expand(self, size: int):
        """Add new resources to the pool."""
        for _ in range(size):
            self._available.append(self._create_resource())
            
    def acquire(self) -> Any:
        """Get a resource from the pool."""
        if not self._available:
            self.expand(len(self._in_use) // 2 + 1)
        resource = self._available.pop()
        self._in_use.add(resource)
        return resource
        
    def release(self, resource: Any):
        """Return a resource to the pool."""
        self._in_use.remove(resource)
        self._available.append(resource)
        
class LightSourcePool(ResourcePool):
    def _create_resource(self) -> np.ndarray:
        """Create a pre-allocated light mask."""
        return np.zeros((32, 32), dtype=np.float32)
```

### Memory Mapping

For very large maps:

```python
class LargeMap:
    def __init__(self, width: int, height: int, filename: str):
        self.shape = (height, width)
        self.filename = filename
        
        # Create memory mapped array
        self.data = np.memmap(
            filename,
            dtype=np.float32,
            mode='w+',
            shape=self.shape
        )
        
    def get_region(self, x: int, y: int, width: int, height: int) -> np.ndarray:
        """Get a view of a region without loading it all into memory."""
        return self.data[y:y+height, x:x+width]
        
    def save(self):
        """Ensure changes are written to disk."""
        self.data.flush()
```

## Parallel Processing {#parallel-processing}

### Thread Pool for Independent Tasks

```python
import concurrent.futures
from typing import List, Tuple

class ParallelMapGenerator:
    def __init__(self, width: int, height: int, chunks: int = 4):
        self.width = width
        self.height = height
        self.chunks = chunks
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=chunks
        )
        
    def generate_chunk(self, x: int, y: int, w: int, h: int) -> np.ndarray:
        """Generate a single chunk of the map."""
        chunk = np.zeros((h, w), dtype=np.float32)
        # ... generation code ...
        return chunk
        
    def generate(self) -> np.ndarray:
        """Generate the entire map in parallel."""
        chunk_width = self.width // self.chunks
        chunk_height = self.height // self.chunks
        
        futures = []
        for y in range(0, self.height, chunk_height):
            for x in range(0, self.width, chunk_width):
                future = self.executor.submit(
                    self.generate_chunk,
                    x, y,
                    min(chunk_width, self.width - x),
                    min(chunk_height, self.height - y)
                )
                futures.append((x, y, future))
                
        # Combine results
        result = np.zeros((self.height, self.width), dtype=np.float32)
        for x, y, future in futures:
            chunk = future.result()
            result[y:y+chunk.shape[0], x:x+chunk.shape[1]] = chunk
            
        return result
```

### Numpy Parallel Operations

```python
class ParallelProcessor:
    def __init__(self):
        # Set number of threads for numpy operations
        threads = os.cpu_count() or 4
        os.environ["OMP_NUM_THREADS"] = str(threads)
        os.environ["OPENBLAS_NUM_THREADS"] = str(threads)
        os.environ["MKL_NUM_THREADS"] = str(threads)
        os.environ["VECLIB_MAXIMUM_THREADS"] = str(threads)
        os.environ["NUMEXPR_NUM_THREADS"] = str(threads)
```

## Rendering Optimizations {#rendering-optimizations}

### Tile Batching

```python
class TileRenderer:
    def __init__(self, tileset: tcod.tileset.Tileset):
        self.tileset = tileset
        self.batch_size = 1000
        self.vertex_buffer = np.zeros((self.batch_size, 4, 2), dtype=np.float32)
        self.color_buffer = np.zeros((self.batch_size, 4, 3), dtype=np.uint8)
        
    def draw_tiles(self, console: tcod.console.Console):
        """Draw tiles in batches."""
        visible = console.tiles_rgb["fg"][:, :, 3] > 0
        tile_count = np.sum(visible)
        
        for i in range(0, tile_count, self.batch_size):
            batch = visible.ravel()[i:i+self.batch_size]
            self._draw_batch(batch)
```

### View Culling

```python
class ViewportRenderer:
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
    def get_visible_chunks(self, camera_x: float, camera_y: float) -> List[Tuple[int, int]]:
        """Get chunks that are currently visible."""
        chunk_size = 32
        margin = 1  # Extra chunks to load
        
        min_x = int((camera_x - self.screen_width/2) / chunk_size) - margin
        max_x = int((camera_x + self.screen_width/2) / chunk_size) + margin
        min_y = int((camera_y - self.screen_height/2) / chunk_size) - margin
        max_y = int((camera_y + self.screen_height/2) / chunk_size) + margin
        
        return [
            (x, y)
            for x in range(min_x, max_x + 1)
            for y in range(min_y, max_y + 1)
        ]
```

## Data Structure Choices {#data-structures}

### Spatial Partitioning

```python
class SpatialHash:
    def __init__(self, cell_size: int = 32):
        self.cell_size = cell_size
        self.cells: Dict[Tuple[int, int], Set[Any]] = {}
        
    def _get_cell(self, x: float, y: float) -> Tuple[int, int]:
        """Get cell coordinates for a position."""
        return (int(x / self.cell_size), int(y / self.cell_size))
        
    def insert(self, item: Any, x: float, y: float):
        """Insert an item at a position."""
        cell = self._get_cell(x, y)
        if cell not in self.cells:
            self.cells[cell] = set()
        self.cells[cell].add(item)
        
    def query_range(self, x: float, y: float, radius: float) -> Set[Any]:
        """Get all items within radius of position."""
        min_cell = self._get_cell(x - radius, y - radius)
        max_cell = self._get_cell(x + radius, y + radius)
        
        results = set()
        for cx in range(min_cell[0], max_cell[0] + 1):
            for cy in range(min_cell[1], max_cell[1] + 1):
                if (cx, cy) in self.cells:
                    results.update(self.cells[(cx, cy)])
                    
        return results
```

### Efficient Collections

```python
from collections import deque
from typing import Dict, Set, Deque

class EntityManager:
    def __init__(self):
        # Fast lookup by ID
        self.entities: Dict[int, Any] = {}
        # Fast iteration over types
        self.by_type: Dict[type, Set[int]] = {}
        # Fast update queue
        self.pending_updates: Deque[Tuple[int, Any]] = deque()
        
    def add(self, entity: Any) -> int:
        """Add an entity and return its ID."""
        entity_id = len(self.entities)
        self.entities[entity_id] = entity
        
        # Track by type for fast queries
        entity_type = type(entity)
        if entity_type not in self.by_type:
            self.by_type[entity_type] = set()
        self.by_type[entity_type].add(entity_id)
        
        return entity_id
        
    def get_by_type(self, entity_type: type) -> Set[Any]:
        """Get all entities of a specific type."""
        return {
            self.entities[eid]
            for eid in self.by_type.get(entity_type, set())
        }
```

## Performance Monitoring

```python
class PerformanceMonitor:
    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.frame_times = deque(maxlen=window_size)
        self.section_times: Dict[str, deque] = {}
        
    def start_frame(self):
        """Start timing a new frame."""
        self.frame_start = time.perf_counter()
        
    def end_frame(self):
        """End timing the current frame."""
        frame_time = time.perf_counter() - self.frame_start
        self.frame_times.append(frame_time)
        
    @contextlib.contextmanager
    def measure(self, section: str):
        """Measure time spent in a section of code."""
        if section not in self.section_times:
            self.section_times[section] = deque(maxlen=self.window_size)
            
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.section_times[section].append(duration)
            
    def get_stats(self) -> Dict[str, float]:
        """Get performance statistics."""
        stats = {
            'fps': len(self.frame_times) / sum(self.frame_times),
            'frame_time': sum(self.frame_times) / len(self.frame_times)
        }
        
        for section, times in self.section_times.items():
            stats[section] = sum(times) / len(times)
            
        return stats
```

## Notes for Proto Island

Key performance considerations for our project:
1. Use numpy operations for all map manipulations
2. Implement spatial partitioning for entity management
3. Use memory mapping for very large maps
4. Batch rendering operations
5. Monitor performance continuously
6. Profile and optimize hot spots
7. Consider parallel processing for generation tasks

Remember to benchmark different approaches in your specific use cases, as the optimal solution may vary depending on exact requirements and data patterns. 