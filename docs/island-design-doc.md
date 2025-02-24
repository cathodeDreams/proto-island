# Island Exploration Prototype - Design Document

## Core Map System

The game world exists as a large, continuous island environment. Rather than loading discrete chunks or rooms, the entire map (initially 200x200 tiles) exists as a single entity. As the player moves, the viewport smoothly pans to follow them, creating a sense of continuous exploration. A fog of war system obscures unexplored areas, revealing in a circular pattern around the player as they explore.

The base terrain consists of several primary types: water, beach, grass, rock, and forest. Each terrain type interacts differently with the lighting system and can modify both natural and artificial light. Water surfaces, for example, can reflect and amplify existing light sources.

### Z-Level Implementation
The world is built on a system of vertical layers, allowing for seamless transitions between surface exploration and underground or elevated areas. Each z-level is stored as a separate map instance, but they remain persistently loaded to maintain state across the entire game world.

## Dynamic Lighting System

The lighting engine forms a core part of the game's atmosphere and mechanics. It operates on multiple layers that combine to create the final lighting state of each tile:

### Natural Light
The primary light source during daytime is the sun, which affects the entire map based on time of day. This creates a base ambient light level that varies from full daylight to near-darkness. Moonlight provides secondary natural lighting at night, with intensity varying based on the moon's current phase.

### Artificial Light
Buildings and structures may contain working light sources that cast light through windows or open doors. These sources create localized lighting effects that interact with the environment. The player may also discover or carry portable light sources, each with unique properties and ranges.

### Environmental Effects
Different surfaces interact uniquely with light:
- Water reflects and potentially amplifies existing light
- Dense forest canopy reduces light penetration
- Building interiors have distinct lighting properties
- Cave systems may be completely dark without artificial light

### Weather Impact
The weather system modifies all light sources through a multiplicative effect. Heavy rain or cloud cover can significantly reduce ambient light, while clear conditions allow for maximum light transmission.

## Structures

### Buildings
Structures are represented using ASCII characters to create recognizable shapes and patterns. Buildings typically range from 1-3 floors, with each floor being a distinct z-level. Doors and windows are marked with specific characters and serve as both navigation points and light portals.

Building interiors maintain their own lighting state, with windows and doors allowing natural light to penetrate based on time of day and weather conditions. Artificial lighting within buildings creates distinct atmospheric effects, especially during nighttime exploration.

### Cave Systems
Cave networks begin with entrance points on the surface map and can extend multiple z-levels down. Unlike buildings, caves feature natural lighting gradients near their entrances, transitioning to complete darkness deeper inside. Each cave level is procedurally generated while maintaining logical consistency with connected levels.

## Time Systems

### Day/Night Cycle
The game operates on a 24-hour virtual clock that directly influences the lighting engine. The cycle affects:
- Base ambient light levels
- Visibility radius for the player
- Color palettes for different terrain types
- Shadow lengths and directions
- Interior/exterior lighting contrasts

### Celestial System
The sky contains both practical and atmospheric elements:
- Moon phases follow an 8-state cycle affecting nighttime visibility
- Constellations (10-15 distinct patterns) appear at night
- Star positions slowly shift over time
- The "look up" command toggles to an inverted color scheme showing the night sky
- Celestial bodies affect ambient light levels across the map

## Technical Implementation Notes

### Data Structures
- Main surface map: 2D array with tile objects
- Z-level maps: Linked list of 2D arrays
- Lighting grid: Parallel array tracking light levels
- Fog of war: Bitmasked overlay
- Time state machine: Tracks all temporal systems

### Performance Considerations
- Lighting calculations use efficient propagation algorithms
- View updates only process visible portions of map
- Z-level transitions preload adjacent levels
- Fog of war uses bitwise operations for speed
- Weather effects use shader-like systems for smooth transitions

## Future Expansion Considerations

The current design allows for future addition of:
- More complex weather patterns
- Additional structure types
- Enhanced lighting effects
- Expanded celestial mechanics
- Deeper cave generation systems
- Advanced terrain interaction