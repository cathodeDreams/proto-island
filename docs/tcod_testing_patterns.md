# TCOD Testing Patterns

## Overview
This document outlines testing patterns and strategies derived from the TCOD examples, adapted for Test-Driven Development (TDD) in Proto Island.

## Table of Contents
1. [Map Generation Testing](#map-generation)
2. [Lighting System Tests](#lighting-tests)
3. [Input Handling Tests](#input-tests)
4. [Performance Testing](#performance-tests)

## Map Generation Testing {#map-generation}

### Cave Generation Tests

```python
import pytest
import numpy as np
from scipy import signal

def test_cave_generation_basic_properties():
    """Test basic properties of generated caves."""
    width, height = 50, 50
    cave = generate_cave(width, height)
    
    assert cave.shape == (height, width)
    assert cave.dtype == np.bool_
    
    # Check reasonable fill ratio (should be ~40-60% walkable)
    fill_ratio = np.sum(cave) / cave.size
    assert 0.4 <= fill_ratio <= 0.6

def test_cave_connectivity():
    """Test that all walkable areas are connected."""
    cave = generate_cave(30, 30)
    connected = ensure_connectivity(cave)
    
    # Flood fill from first walkable tile
    y, x = np.where(connected)[0][0], np.where(connected)[1][0]
    filled = flood_fill(connected, (y, x))
    
    # All walkable tiles should be reachable
    np.testing.assert_array_equal(filled, connected)

def test_cave_wall_rules():
    """Test that cellular automata rules are applied correctly."""
    # Create a known pattern
    cave = np.zeros((5, 5), dtype=bool)
    cave[2, 2] = True  # Center tile
    
    # Apply one iteration
    next_cave = apply_cave_iteration(cave, wall_rule=5)
    
    # Center tile should become a wall (too few neighbors)
    assert not next_cave[2, 2]
```

### BSP Room Generation Tests

```python
def test_bsp_node_splitting():
    """Test BSP node splitting behavior."""
    node = BSPNode(0, 0, 20, 20)
    success = node.split(min_size=5)
    
    assert success
    assert node.children is not None
    left, right = node.children
    
    # Check children dimensions
    assert left.width + right.width == node.width
    assert left.height == node.height or left.width == node.width
    
    # Check minimum size constraints
    assert left.width >= 5 and left.height >= 5
    assert right.width >= 5 and right.height >= 5

def test_room_generation():
    """Test room generation within BSP nodes."""
    node = BSPNode(0, 0, 15, 15)
    rooms = node.create_rooms()
    
    for x, y, w, h in rooms:
        # Check room bounds
        assert 0 <= x < node.width - w
        assert 0 <= y < node.height - h
        assert w >= 3  # Minimum room width
        assert h >= 3  # Minimum room height
```

## Lighting System Tests {#lighting-tests}

```python
def test_light_source_application():
    """Test light source calculations."""
    lighting = LightingSystem(10, 10)
    
    # Add a light source in the center
    lighting.apply_light_source(5, 5, 1.0, (255, 255, 255))
    
    # Center should be brightest
    assert lighting.artificial_light[5, 5].sum() == pytest.approx(3.0, rel=1e-5)
    
    # Light should fall off with distance
    assert lighting.artificial_light[0, 0].sum() < lighting.artificial_light[5, 5].sum()

def test_fov_calculation():
    """Test field of view calculations."""
    width, height = 20, 20
    transparent = np.ones((height, width), dtype=bool)
    
    # Create a wall
    transparent[10, :] = False
    
    lighting = LightingSystem(width, height)
    fov = lighting.calculate_fov(5, 5, radius=8, transparent=transparent)
    
    # Points behind wall should not be visible
    assert not np.any(fov[11:, :])
    
    # Points in front of wall should be visible
    assert np.any(fov[:10, :])

def test_time_based_lighting():
    """Test natural lighting changes with time."""
    lighting = LightingSystem(10, 10)
    
    # Test different times of day
    lighting.update(0.0)  # Midnight
    assert np.all(lighting.natural_light == 0.2)  # Minimum ambient
    
    lighting.update(0.5)  # Noon
    assert np.all(lighting.natural_light == 0.8)  # Maximum ambient
```

## Input Handling Tests {#input-tests}

```python
def test_input_handler_key_tracking():
    """Test key press tracking."""
    handler = InputHandler()
    
    # Simulate key press
    event = tcod.event.KeyDown(
        scancode=0,
        sym=tcod.event.KeySym.a,
        mod=0,
        repeat=False,
    )
    handler.ev_keydown(event)
    assert tcod.event.KeySym.a in handler.keys_pressed
    
    # Simulate key release
    event = tcod.event.KeyUp(
        scancode=0,
        sym=tcod.event.KeySym.a,
        mod=0,
    )
    handler.ev_keyup(event)
    assert tcod.event.KeySym.a not in handler.keys_pressed

def test_mouse_motion_tracking():
    """Test mouse position tracking."""
    handler = InputHandler()
    
    event = tcod.event.MouseMotion(
        position=(100, 100),
        motion=(10, 10),
        tile=(5, 5),
        tile_motion=(1, 1),
    )
    handler.ev_mousemotion(event)
    
    assert handler.mouse_pos == (5, 5)
```

## Performance Testing {#performance-tests}

```python
def test_rendering_performance():
    """Test rendering performance meets requirements."""
    width, height = 80, 50
    renderer = RenderSystem(width, height)
    game_map = np.random.choice([0, 1], size=(height, width))
    fov = np.ones((height, width), dtype=bool)
    
    # Measure render time
    start_time = time.perf_counter()
    for _ in range(100):  # 100 frames
        renderer.render_map(game_map, fov)
    end_time = time.perf_counter()
    
    frame_time = (end_time - start_time) / 100
    assert frame_time < 1/60  # Should maintain 60 FPS

def test_light_calculation_performance():
    """Test light calculation performance."""
    width, height = 200, 200
    lighting = LightingSystem(width, height)
    
    start_time = time.perf_counter()
    for _ in range(10):  # Simulate 10 light sources
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        lighting.apply_light_source(x, y, 1.0, (255, 255, 255))
    end_time = time.perf_counter()
    
    assert end_time - start_time < 0.016  # Should complete within one frame
```

## Test Fixtures

```python
@pytest.fixture
def basic_map():
    """Create a basic test map."""
    return np.array([
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ], dtype=bool)

@pytest.fixture
def lighting_system():
    """Create a basic lighting system for tests."""
    return LightingSystem(10, 10)

@pytest.fixture
def bsp_tree():
    """Create a basic BSP tree for tests."""
    root = BSPNode(0, 0, 20, 20)
    root.split(5)
    return root
```

## Testing Guidelines

1. **Test Data Generation**
   - Use fixed seeds for random generation
   - Create small, predictable test cases
   - Use fixtures for common test data

2. **Performance Testing**
   - Set clear performance targets
   - Test with realistic data sizes
   - Include stress tests for edge cases

3. **Integration Testing**
   - Test interactions between systems
   - Verify state consistency
   - Test boundary conditions

4. **Visual Testing**
   - Capture and compare screenshots
   - Test color calculations
   - Verify rendering output

## Test Organization

Structure tests by system:
```
tests/
├── test_map/
│   ├── test_cave_generation.py
│   ├── test_bsp_generation.py
│   └── test_noise.py
├── test_lighting/
│   ├── test_fov.py
│   └── test_light_sources.py
├── test_input/
│   └── test_event_handling.py
└── test_performance/
    └── test_rendering.py
```

## Continuous Integration

Example GitHub Actions workflow:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        pytest --cov=./ --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Notes for Proto Island

When implementing new features from the TCOD examples:
1. Start with the test cases above as templates
2. Adapt tests for our specific requirements
3. Follow TDD process: test → implement → refactor
4. Focus on performance testing for large maps
5. Include visual regression tests for rendering 