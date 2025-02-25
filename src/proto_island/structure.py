import numpy as np
from enum import Enum
import random
from typing import Dict, List, Tuple, Optional, Any
from .map import GameMap, TerrainType

class StructureType(Enum):
    """Enum representing different structure types in the game."""
    HOUSE = 0
    SHOP = 1
    TEMPLE = 2
    WORKSHOP = 3
    STORAGE = 4
    
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

class StairType(Enum):
    """Enum representing different types of vertical connections."""
    STAIR_UP = 0
    STAIR_DOWN = 1
    LADDER_UP = 2
    LADDER_DOWN = 3
    
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

class BSPNode:
    """Binary Space Partition node for building room layout."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        """Initialize a BSP node.
        
        Args:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            width: Width of the node
            height: Height of the node
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.children: Optional[Tuple['BSPNode', 'BSPNode']] = None
        self.room: Optional[Tuple[int, int, int, int]] = None
        
    def split(self, min_size: int, rng: random.Random) -> bool:
        """Split the node into two children if possible.
        
        Args:
            min_size: Minimum size of a room
            rng: Random number generator for consistent results
            
        Returns:
            bool: True if split was successful, False otherwise
        """
        if self.width < min_size * 2 or self.height < min_size * 2:
            return False
            
        # Choose split direction based on aspect ratio with some randomness
        # Wider rooms split horizontally, taller rooms split vertically
        if self.width > self.height and self.width / self.height >= 1.25:
            horizontal = True
        elif self.height > self.width and self.height / self.width >= 1.25:
            horizontal = False
        else:
            horizontal = rng.random() < 0.5
        
        if horizontal:
            split_at = rng.randint(min_size, self.width - min_size)
            left = BSPNode(self.x, self.y, split_at, self.height)
            right = BSPNode(self.x + split_at, self.y, self.width - split_at, self.height)
        else:
            split_at = rng.randint(min_size, self.height - min_size)
            left = BSPNode(self.x, self.y, self.width, split_at)
            right = BSPNode(self.x, self.y + split_at, self.width, self.height - split_at)
            
        self.children = (left, right)
        return True
        
    def create_room(self, rng: random.Random) -> Optional[Tuple[int, int, int, int]]:
        """Create a room within this node.
        
        Args:
            rng: Random number generator
            
        Returns:
            Optional[Tuple[int, int, int, int]]: (x, y, width, height) of room or None
        """
        if self.width < 3 or self.height < 3:
            return None
            
        # Room size is a bit smaller than the node
        padding = rng.randint(1, 2)
        room_width = max(3, self.width - padding * 2)
        room_height = max(3, self.height - padding * 2)
        
        # Room position within the node (add randomness for more natural look)
        room_x = self.x + padding
        if padding > 1:
            room_x += rng.randint(0, padding // 2)
            
        room_y = self.y + padding
        if padding > 1:
            room_y += rng.randint(0, padding // 2)
            
        self.room = (room_x, room_y, room_width, room_height)
        return self.room


class StructureGenerator:
    """Generates buildings and other structures for the game map."""
    
    def __init__(self, width: int, height: int):
        """Initialize the structure generator.
        
        Args:
            width: Width of the map in tiles
            height: Height of the map in tiles
        """
        self.width = width
        self.height = height
        
    def is_buildable(self, game_map: GameMap, x: int, y: int, width: int, height: int) -> bool:
        """Check if an area is suitable for building.
        
        Args:
            game_map: The game map
            x: X coordinate of the building
            y: Y coordinate of the building
            width: Width of the building
            height: Height of the building
            
        Returns:
            bool: True if the area is suitable for building
        """
        # Check bounds
        if x < 0 or y < 0 or x + width >= game_map.width or y + height >= game_map.height:
            return False
            
        # Get terrain in the area
        terrain = game_map.z_levels[game_map.current_z]['tiles'][y:y+height, x:x+width]
        
        # Check for water and steep terrain
        if np.any(terrain == TerrainType.WATER) or np.any(terrain == TerrainType.ROCK):
            return False
            
        return True
        
    def find_buildable_area(self, game_map: GameMap, min_width: int, min_height: int, 
                           max_attempts: int = 100, rng: Optional[random.Random] = None) -> Optional[Tuple[int, int, int, int]]:
        """Find a suitable area for building.
        
        Args:
            game_map: The game map
            min_width: Minimum width of the building
            min_height: Minimum height of the building
            max_attempts: Maximum number of attempts to find a spot
            rng: Random number generator
            
        Returns:
            Optional[Tuple[int, int, int, int]]: (x, y, width, height) or None if no suitable area found
        """
        if rng is None:
            rng = random.Random()
            
        for _ in range(max_attempts):
            # Random width and height
            width = rng.randint(min_width, min(min_width + 10, game_map.width // 4))
            height = rng.randint(min_height, min(min_height + 10, game_map.height // 4))
            
            # Random position
            x = rng.randint(0, game_map.width - width - 1)
            y = rng.randint(0, game_map.height - height - 1)
            
            if self.is_buildable(game_map, x, y, width, height):
                return (x, y, width, height)
                
        return None
        
    def generate_building(self, x: int, y: int, width: int, height: int, 
                         min_room_size: int = 3, structure_type: StructureType = StructureType.HOUSE,
                         seed: Optional[int] = None) -> Dict[str, Any]:
        """Generate a building layout using BSP.
        
        Args:
            x: X coordinate of the building
            y: Y coordinate of the building
            width: Width of the building
            height: Height of the building
            min_room_size: Minimum size of rooms
            structure_type: Type of structure to generate
            seed: Random seed for deterministic generation
            
        Returns:
            Dict: Building definition with rooms, corridors, etc.
        """
        rng = random.Random(seed)
        
        # Create the root node
        root = BSPNode(x, y, width, height)
        
        # Store all leaf nodes for room creation
        leaf_nodes = [root]
        
        # Recursively split the space
        nodes_to_process = [root]
        split_chance = 0.8  # Higher means more splits
        
        # Adjust split chance based on structure type
        if structure_type == StructureType.HOUSE:
            split_chance = 0.6  # Houses have fewer rooms
        elif structure_type == StructureType.TEMPLE:
            split_chance = 0.7  # Temples have moderate rooms
        elif structure_type == StructureType.SHOP:
            split_chance = 0.75  # Shops have more rooms
            
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while nodes_to_process and iteration < max_iterations:
            iteration += 1
            new_nodes = []
            
            for node in nodes_to_process:
                # Try to split the node
                if rng.random() < split_chance and node.split(min_room_size, rng):
                    # Split was successful, add children to process list
                    leaf_nodes.remove(node)
                    leaf_nodes.extend(node.children)
                    new_nodes.extend(node.children)
                    
            nodes_to_process = new_nodes
            
        # Create rooms in leaf nodes
        rooms = []
        for i, node in enumerate(leaf_nodes):
            room = node.create_room(rng)
            if room:
                rooms.append(room)
                
        # Connect rooms
        corridors = []
        if len(rooms) > 1:
            # Create a minimal spanning tree to ensure all rooms are connected
            for i in range(len(rooms) - 1):
                # Connect room i to room i+1
                corridors.append((i, i+1))
                
            # Add a few extra corridors for redundancy
            if len(rooms) > 3 and rng.random() < 0.5:
                extra_corridor = (0, len(rooms) - 1)
                if extra_corridor not in corridors:
                    corridors.append(extra_corridor)
        
        # Create an entrance on a random edge of a random room
        if rooms:
            entrance_room = rng.choice(rooms)
            rx, ry, rw, rh = entrance_room
            
            # Decide which wall to place entrance on
            wall = rng.randint(0, 3)  # 0: north, 1: east, 2: south, 3: west
            
            if wall == 0:  # North
                entrance_x = rx + rng.randint(0, rw - 1)
                entrance_y = ry
            elif wall == 1:  # East
                entrance_x = rx + rw - 1
                entrance_y = ry + rng.randint(0, rh - 1)
            elif wall == 2:  # South
                entrance_x = rx + rng.randint(0, rw - 1)
                entrance_y = ry + rh - 1
            else:  # West
                entrance_x = rx
                entrance_y = ry + rng.randint(0, rh - 1)
                
            entrance = (entrance_x, entrance_y)
        else:
            # Fallback if no rooms (shouldn't normally happen)
            entrance = (x + width // 2, y + height // 2)
            
        return {
            "footprint": (x, y, width, height),
            "rooms": rooms,
            "corridors": corridors,
            "entrance": entrance,
            "structure_type": structure_type,
            "floors": 1  # Initialize with 1 floor
        }
        
    def generate_multi_floor_building(self, x: int, y: int, width: int, height: int,
                                    floors: int = 2, min_room_size: int = 3,
                                    structure_type: StructureType = StructureType.HOUSE,
                                    seed: Optional[int] = None) -> Dict[str, Any]:
        """Generate a multi-floor building layout using BSP.
        
        Args:
            x: X coordinate of the building
            y: Y coordinate of the building
            width: Width of the building
            height: Height of the building
            floors: Number of floors in the building
            min_room_size: Minimum size of rooms
            structure_type: Type of structure to generate
            seed: Random seed for deterministic generation
            
        Returns:
            Dict: Building definition with floors, rooms, corridors, etc.
        """
        if floors < 1:
            floors = 1
        
        rng = random.Random(seed)
        
        # Generate the base building
        building = self.generate_building(x, y, width, height, min_room_size, structure_type, seed)
        
        # Update the number of floors
        building["floors"] = floors
        
        # Add floor-specific data
        building["floor_layouts"] = {0: {  # Ground floor (z=0)
            "rooms": building["rooms"],
            "corridors": building["corridors"]
        }}
        
        # Generate additional floors
        for floor in range(1, floors):
            # Create a slightly different layout for each floor
            # Use a different seed derived from the original to ensure variation
            floor_seed = None if seed is None else seed + floor * 1000
            
            # Adjust the floor footprint (upper floors can be smaller)
            floor_width = width
            floor_height = height
            floor_x = x
            floor_y = y
            
            # For some building types, make upper floors smaller
            if structure_type in [StructureType.HOUSE, StructureType.SHOP] and rng.random() < 0.7:
                # Reduce size by 0-30%
                size_reduction = rng.uniform(0, 0.3)
                floor_width = max(min_room_size * 3, int(width * (1 - size_reduction)))
                floor_height = max(min_room_size * 3, int(height * (1 - size_reduction)))
                
                # Center the reduced footprint
                floor_x = x + (width - floor_width) // 2
                floor_y = y + (height - floor_height) // 2
            
            # Create a new floor layout
            floor_layout = self._generate_floor_layout(
                floor_x, floor_y, floor_width, floor_height,
                min_room_size, structure_type, floor_seed
            )
            
            # Add to building data
            building["floor_layouts"][floor] = floor_layout
            
        # Generate vertical connections between floors
        building["vertical_connections"] = self._generate_vertical_connections(building, rng)
        
        return building
    
    def _generate_floor_layout(self, x: int, y: int, width: int, height: int,
                           min_room_size: int, structure_type: StructureType,
                           seed: Optional[int]) -> Dict[str, Any]:
        """Generate a layout for a single floor.
        
        Args:
            x: X coordinate of the floor
            y: Y coordinate of the floor
            width: Width of the floor
            height: Height of the floor
            min_room_size: Minimum size of rooms
            structure_type: Type of structure to generate
            seed: Random seed for deterministic generation
            
        Returns:
            Dict: Floor layout with rooms and corridors
        """
        rng = random.Random(seed)
        
        # Create the root node for this floor
        root = BSPNode(x, y, width, height)
        
        # Store all leaf nodes for room creation
        leaf_nodes = [root]
        
        # Recursively split the space
        nodes_to_process = [root]
        
        # Adjust split chance based on structure type and floor
        split_chance = 0.8
        if structure_type == StructureType.HOUSE:
            split_chance = 0.6
        elif structure_type == StructureType.TEMPLE:
            split_chance = 0.7
        elif structure_type == StructureType.SHOP:
            split_chance = 0.75
            
        max_iterations = 10
        iteration = 0
        
        while nodes_to_process and iteration < max_iterations:
            iteration += 1
            new_nodes = []
            
            for node in nodes_to_process:
                if rng.random() < split_chance and node.split(min_room_size, rng):
                    leaf_nodes.remove(node)
                    leaf_nodes.extend(node.children)
                    new_nodes.extend(node.children)
                    
            nodes_to_process = new_nodes
            
        # Create rooms in leaf nodes
        rooms = []
        for node in leaf_nodes:
            room = node.create_room(rng)
            if room:
                rooms.append(room)
                
        # Connect rooms
        corridors = []
        if len(rooms) > 1:
            # Create a minimal spanning tree to ensure all rooms are connected
            for i in range(len(rooms) - 1):
                corridors.append((i, i+1))
                
            # Add a few extra corridors for redundancy
            if len(rooms) > 3 and rng.random() < 0.5:
                extra_corridor = (0, len(rooms) - 1)
                if extra_corridor not in corridors:
                    corridors.append(extra_corridor)
        
        return {
            "rooms": rooms,
            "corridors": corridors,
            "footprint": (x, y, width, height)
        }
    
    def _generate_vertical_connections(self, building: Dict[str, Any], 
                                     rng: random.Random) -> Dict[int, List[Dict[str, Any]]]:
        """Generate stairs or ladders between floors.
        
        Args:
            building: The building data
            rng: Random number generator
            
        Returns:
            Dict: Mapping of floor number to list of vertical connections
        """
        floors = building["floors"]
        if floors <= 1:
            return {}
            
        vertical_connections = {}
        
        # For each floor (except the highest), create connections to the floor above
        for floor in range(floors - 1):
            # Get room layouts for current and next floor
            current_floor_rooms = building["floor_layouts"][floor]["rooms"]
            next_floor_rooms = building["floor_layouts"][floor + 1]["rooms"]
            
            if not current_floor_rooms or not next_floor_rooms:
                continue
                
            # Choose a random room for the stairs on this floor
            current_room_idx = rng.randint(0, len(current_floor_rooms) - 1)
            current_room = current_floor_rooms[current_room_idx]
            
            # Choose a random room for the stairs on the next floor
            next_room_idx = rng.randint(0, len(next_floor_rooms) - 1)
            next_room = next_floor_rooms[next_room_idx]
            
            # Create stairs within the chosen rooms
            # First, get the rooms' coordinates
            crx, cry, crw, crh = current_room
            nrx, nry, nrw, nrh = next_room
            
            # Place stairs at valid positions within the rooms
            # Try to place them not too close to walls
            current_stair_x = crx + rng.randint(1, crw - 2)
            current_stair_y = cry + rng.randint(1, crh - 2)
            
            next_stair_x = nrx + rng.randint(1, nrw - 2)
            next_stair_y = nry + rng.randint(1, nrh - 2)
            
            # Determine stair type - houses tend to have stairs, other buildings might have ladders
            stair_type = StairType.STAIR_UP
            if structure_type := building.get("structure_type"):
                if structure_type in [StructureType.STORAGE, StructureType.WORKSHOP] and rng.random() < 0.7:
                    stair_type = StairType.LADDER_UP
            
            # Create connection data
            if floor not in vertical_connections:
                vertical_connections[floor] = []
                
            vertical_connections[floor].append({
                "type": stair_type,
                "position": (current_stair_x, current_stair_y),
                "target_floor": floor + 1,
                "target_position": (next_stair_x, next_stair_y)
            })
            
            # Create the reciprocal connection
            if floor + 1 not in vertical_connections:
                vertical_connections[floor + 1] = []
                
            vertical_connections[floor + 1].append({
                "type": StairType.STAIR_DOWN if stair_type == StairType.STAIR_UP else StairType.LADDER_DOWN,
                "position": (next_stair_x, next_stair_y),
                "target_floor": floor,
                "target_position": (current_stair_x, current_stair_y)
            })
            
        return vertical_connections
    
    def generate_buildings(self, game_map: GameMap, count: int = 5, 
                          min_size: int = 8, seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate multiple buildings with suitable placement.
        
        Args:
            game_map: The game map
            count: Number of buildings to generate
            min_size: Minimum size of buildings
            seed: Random seed for deterministic generation
            
        Returns:
            List[Dict]: List of building definitions
        """
        rng = random.Random(seed)
        buildings = []
        
        # Determine how many buildings will be multi-floor
        multi_floor_count = min(count // 2 + rng.randint(0, 1), count)  # At least half, max all
        
        for i in range(count):
            # Find a suitable area for the building
            buildable_area = self.find_buildable_area(
                game_map, min_size, min_size, max_attempts=100, rng=rng
            )
            
            if not buildable_area:
                continue  # Skip if no suitable area found
                
            x, y, width, height = buildable_area
            
            # Determine building type
            structure_type = rng.choice(list(StructureType))
            
            # Generate building
            if i < multi_floor_count:
                # Determine number of floors (1-3)
                floors = rng.randint(2, 3)
                
                # Multi-floor building
                building = self.generate_multi_floor_building(
                    x, y, width, height, floors=floors,
                    min_room_size=3, structure_type=structure_type,
                    seed=seed + i if seed else None
                )
            else:
                # Single-floor building
                building = self.generate_building(
                    x, y, width, height, min_room_size=3,
                    structure_type=structure_type,
                    seed=seed + i if seed else None
                )
            
            buildings.append(building)
            
        return buildings
    
    def add_buildings_to_map(self, game_map: GameMap, count: int = 5, seed: Optional[int] = None) -> None:
        """Generate and add buildings to the game map.
        
        Args:
            game_map: The game map
            count: Number of buildings to generate
            seed: Random seed for deterministic generation
        """
        # Generate the buildings
        buildings = self.generate_buildings(game_map, count, seed=seed)
        
        # Initialize buildings storage in map
        if 'buildings' not in game_map.z_levels[game_map.current_z]:
            game_map.z_levels[game_map.current_z]['buildings'] = []
            
        # Initialize entrances storage in map
        if 'entrances' not in game_map.z_levels[game_map.current_z]:
            game_map.z_levels[game_map.current_z]['entrances'] = []
        
        # Store the buildings in the map
        for building in buildings:
            game_map.z_levels[game_map.current_z]['buildings'].append(building)
            
            # Add entrance to the map for reference
            game_map.z_levels[game_map.current_z]['entrances'].append(building['entrance'])
            
            # For multi-floor buildings, create the additional z-levels and connections
            if building.get("floors", 1) > 1:
                self._add_multi_floor_building_to_map(game_map, building)
    
    def _add_multi_floor_building_to_map(self, game_map: GameMap, building: Dict[str, Any]) -> None:
        """Add a multi-floor building to the map, creating necessary z-levels and transitions.
        
        Args:
            game_map: The game map
            building: The building data
        """
        floors = building.get("floors", 1)
        if floors <= 1:
            return
            
        # Current z-level is our reference (usually 0)
        base_z = game_map.current_z
        
        # Create higher z-levels if needed
        for floor in range(1, floors):
            target_z = base_z + floor
            
            # Create z-level if it doesn't exist
            if target_z not in game_map.z_levels:
                game_map.add_z_level(target_z)
                
            # Initialize building storage for this level
            if 'buildings' not in game_map.z_levels[target_z]:
                game_map.z_levels[target_z]['buildings'] = []
                
            # Add this building to the level
            game_map.z_levels[target_z]['buildings'].append(building)
        
        # Add vertical connections between floors
        if "vertical_connections" in building:
            for floor, connections in building["vertical_connections"].items():
                for connection in connections:
                    from_z = base_z + floor
                    to_z = base_z + connection["target_floor"]
                    from_pos = connection["position"]
                    to_pos = connection["target_position"]
                    
                    # Add the level transition to the map
                    game_map.add_level_transition(from_z, to_z, from_pos[0], from_pos[1])
    
    def add_artificial_lights(self, game_map: GameMap) -> None:
        """Add artificial light sources to buildings.
        
        Args:
            game_map: The game map
        """
        # Iterate through all z-levels
        for z in game_map.z_levels:
            # Skip levels with no buildings
            if 'buildings' not in game_map.z_levels[z]:
                continue
                
            # Get the lighting system for this level
            lighting = game_map.z_levels[z]['lighting']
            
            # Add lights to each building on this level
            for building in game_map.z_levels[z]['buildings']:
                # Get the building data for this z-level
                floor_idx = z - game_map.current_z  # Floor index relative to base level
                
                # Skip if this floor doesn't exist in the building
                if floor_idx not in building.get("floor_layouts", {}) and floor_idx != 0:
                    continue
                    
                # Get rooms for this floor
                rooms = None
                if floor_idx == 0 and "rooms" in building:
                    rooms = building["rooms"]
                elif "floor_layouts" in building and floor_idx in building["floor_layouts"]:
                    rooms = building["floor_layouts"][floor_idx]["rooms"]
                
                if not rooms:
                    continue
                    
                # Add a light to each room
                for room in rooms:
                    rx, ry, rw, rh = room
                    # Place light in center of room
                    light_x = rx + rw // 2
                    light_y = ry + rh // 2
                    self._add_point_light(lighting, light_x, light_y, 0.6, 8)
                
                # Add a brighter light at the entrance of the ground floor
                if floor_idx == 0 and "entrance" in building:
                    entrance_x, entrance_y = building["entrance"]
                    self._add_point_light(lighting, entrance_x, entrance_y, 0.8, 10)
                    
                # Add lights at staircases
                if "vertical_connections" in building and floor_idx in building["vertical_connections"]:
                    for connection in building["vertical_connections"][floor_idx]:
                        stair_x, stair_y = connection["position"]
                        self._add_point_light(lighting, stair_x, stair_y, 0.7, 9)
    
    def _add_point_light(self, lighting, x: int, y: int, intensity: float, radius: int) -> None:
        """Add a point light source to the lighting system.
        
        Args:
            lighting: The lighting system
            x: X coordinate of the light
            y: Y coordinate of the light
            intensity: Light intensity
            radius: Light radius in tiles
        """
        # Create a simple light falloff based on distance
        yy, xx = np.ogrid[-radius:radius+1, -radius:radius+1]
        dist_squared = xx*xx + yy*yy
        mask = dist_squared <= radius*radius
        
        # Apply the light
        y_min = max(0, y - radius)
        y_max = min(lighting.height, y + radius + 1)
        x_min = max(0, x - radius)
        x_max = min(lighting.width, x + radius + 1)
        
        # Calculate offsets for the mask
        my_min = max(0, -(y - radius))
        my_max = mask.shape[0] - max(0, (y + radius + 1) - lighting.height)
        mx_min = max(0, -(x - radius))
        mx_max = mask.shape[1] - max(0, (x + radius + 1) - lighting.width)
        
        # Calculate light falloff
        light_mask = mask[my_min:my_max, mx_min:mx_max] * intensity * (1 - np.sqrt(dist_squared[my_min:my_max, mx_min:mx_max]) / radius)
        
        # Apply light (additive)
        lighting.artificial_light[y_min:y_max, x_min:x_max] += light_mask 