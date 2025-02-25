from enum import Enum, auto
from typing import List, Optional, Any
import random
import numpy as np
from .map import TerrainType
from .inventory import Inventory


class CharacterType(Enum):
    """Types of characters in the game."""
    PLAYER = auto()
    NPC = auto()


class NPCType(Enum):
    """Types of NPCs in the game."""
    VILLAGER = auto()
    MERCHANT = auto()
    GUARD = auto()
    ANIMAL = auto()


class NPCState(Enum):
    """Possible states for NPCs."""
    IDLE = auto()
    WANDER = auto()
    FOLLOW = auto()
    FLEE = auto()
    TALK = auto()


class Character:
    """Base character class for players and NPCs."""
    
    def __init__(self, x: int, y: int, z: int = 0, char_type: CharacterType = CharacterType.NPC):
        """Initialize a character.
        
        Args:
            x: X-coordinate
            y: Y-coordinate
            z: Z-level
            char_type: Type of character
        """
        self.x = x
        self.y = y
        self.z = z
        self.char_type = char_type
        self.health = 100
        self.max_health = 100
        self.inventory = Inventory(capacity=50)  # Default inventory capacity
        
    def move(self, game_map, dx: int, dy: int) -> bool:
        """Move the character by the given amount.
        
        Args:
            game_map: The game map
            dx: X-direction movement
            dy: Y-direction movement
            
        Returns:
            bool: True if movement was successful
        """
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Check if movement is valid
        if not game_map.in_bounds(new_x, new_y):
            return False
            
        # Check if terrain is walkable
        terrain = game_map.tiles[new_y, new_x]
        is_walkable = self._is_terrain_walkable(terrain)
        
        if not is_walkable:
            return False
            
        # Move character
        self.x = new_x
        self.y = new_y
        return True
        
    def transition_z_level(self, game_map) -> bool:
        """Attempt to transition between z-levels.
        
        Args:
            game_map: The game map
            
        Returns:
            bool: True if transition was successful
        """
        transitions = game_map.get_level_transitions(self.z)
        for to_z, locations in transitions.items():
            for x, y in locations:
                if self.x == x and self.y == y:
                    self.z = to_z
                    return True
        return False
        
    def _is_terrain_walkable(self, terrain_type) -> bool:
        """Check if the terrain type is walkable.
        
        Args:
            terrain_type: The terrain type to check
            
        Returns:
            bool: True if walkable
        """
        walkable_types = [
            TerrainType.GRASS,
            TerrainType.BEACH,
            TerrainType.CAVE_FLOOR
        ]
        unwalkable_types = [
            TerrainType.ROCK,
            TerrainType.WATER,
            TerrainType.CAVE_WALL
        ]
        
        if terrain_type in unwalkable_types:
            return False
        
        return terrain_type in walkable_types or terrain_type not in unwalkable_types


class Player(Character):
    """Player character class."""
    
    def __init__(self, x: int, y: int, z: int = 0):
        """Initialize a player character.
        
        Args:
            x: X-coordinate
            y: Y-coordinate
            z: Z-level
        """
        super().__init__(x, y, z, CharacterType.PLAYER)
        self.fov_radius = 8
        
    def calculate_fov(self, game_map) -> np.ndarray:
        """Calculate the player's field of view.
        
        Args:
            game_map: The game map
            
        Returns:
            np.ndarray: Boolean array where True represents visible tiles
        """
        # This implementation is a simple radius-based FOV
        # In a full implementation, we might use tcod.map.compute_fov for better FOV calculation
        fov = np.zeros((game_map.height, game_map.width), dtype=bool)
        
        for y in range(game_map.height):
            for x in range(game_map.width):
                # Simple distance-based FOV
                distance = ((x - self.x) ** 2 + (y - self.y) ** 2) ** 0.5
                if distance <= self.fov_radius:
                    fov[y, x] = True
                    
        return fov


class NPC(Character):
    """Non-player character class."""
    
    def __init__(self, x: int, y: int, z: int = 0, npc_type: NPCType = NPCType.VILLAGER):
        """Initialize an NPC.
        
        Args:
            x: X-coordinate
            y: Y-coordinate
            z: Z-level
            npc_type: Type of NPC
        """
        super().__init__(x, y, z, CharacterType.NPC)
        self.npc_type = npc_type
        self.state = NPCState.IDLE
        self.target = None
        self.name = f"{npc_type.name.capitalize()} #{id(self) % 1000}"
        
    def update(self, game_map, player: Optional[Player] = None):
        """Update NPC state and behavior.
        
        Args:
            game_map: The game map
            player: The player character
        """
        if self.state == NPCState.IDLE:
            # 20% chance to start wandering
            if random.random() < 0.2:
                self.state = NPCState.WANDER
        elif self.state == NPCState.WANDER:
            # Implement wandering behavior
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            self.move(game_map, dx, dy)
            
            # 10% chance to go back to idle
            if random.random() < 0.1:
                self.state = NPCState.IDLE
                
        # If player is provided, check for interactions
        if player and self._is_player_nearby(player):
            if self.state != NPCState.TALK:
                # NPCs might react differently based on type
                if self.npc_type == NPCType.VILLAGER:
                    # 50% chance to stop and talk
                    if random.random() < 0.5:
                        self.state = NPCState.TALK
                elif self.npc_type == NPCType.MERCHANT:
                    # Merchants always want to talk (sell)
                    self.state = NPCState.TALK
                elif self.npc_type == NPCType.GUARD:
                    # Guards might follow suspicious players
                    if random.random() < 0.3:
                        self.state = NPCState.FOLLOW
                        self.target = player
                elif self.npc_type == NPCType.ANIMAL:
                    # Animals typically flee
                    self.state = NPCState.FLEE
                    self.target = player
            
    def _is_player_nearby(self, player: Player) -> bool:
        """Check if player is within interaction range.
        
        Args:
            player: The player character
            
        Returns:
            bool: True if player is nearby
        """
        # Only consider players on the same z-level
        if player.z != self.z:
            return False
            
        distance = ((self.x - player.x) ** 2 + (self.y - player.y) ** 2) ** 0.5
        return distance <= 5  # 5 tile interaction range


class CharacterManager:
    """Manages all characters in the game."""
    
    def __init__(self):
        """Initialize a character manager."""
        self.player = None
        self.npcs = []
        
    def set_player(self, player: Player):
        """Set the player character.
        
        Args:
            player: The player character
        """
        self.player = player
        
    def add_npc(self, npc: NPC):
        """Add an NPC to the manager.
        
        Args:
            npc: The NPC to add
        """
        self.npcs.append(npc)
        
    def update(self, game_map):
        """Update all characters.
        
        Args:
            game_map: The game map
        """
        # Update NPCs
        for npc in self.npcs:
            npc.update(game_map, self.player)
            
    def get_characters_at_location(self, x: int, y: int, z: int) -> List[Character]:
        """Get all characters at a specific location.
        
        Args:
            x: X-coordinate
            y: Y-coordinate
            z: Z-level
            
        Returns:
            List[Character]: List of characters at the location
        """
        characters = []
        if self.player and self.player.x == x and self.player.y == y and self.player.z == z:
            characters.append(self.player)
            
        for npc in self.npcs:
            if npc.x == x and npc.y == y and npc.z == z:
                characters.append(npc)
                
        return characters 