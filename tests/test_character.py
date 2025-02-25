import pytest
import numpy as np
from proto_island.map import GameMap, TerrainType

# We'll need to import the character module once it's created
# from proto_island.character import Character, Player, NPC, CharacterType, NPCType, NPCState, CharacterManager

@pytest.fixture
def basic_map():
    """Create a basic test map."""
    game_map = GameMap(width=20, height=20)
    game_map.generate_terrain(seed=42)
    return game_map

class TestCharacter:
    def test_character_initialization(self):
        """Test basic character initialization."""
        from proto_island.character import Character, CharacterType
        
        character = Character(x=5, y=5, z=1, char_type=CharacterType.PLAYER)
        assert character.x == 5
        assert character.y == 5
        assert character.z == 1
        assert character.char_type == CharacterType.PLAYER
        assert character.health == 100
        assert character.max_health == 100
        
    def test_character_movement(self, basic_map):
        """Test character movement on the map."""
        from proto_island.character import Character
        
        character = Character(x=5, y=5)
        
        # Test movement out of bounds
        character.x, character.y = 19, 19
        success = character.move(basic_map, dx=1, dy=0)
        assert not success
        assert character.x == 19
        assert character.y == 19
        
        # Test movement to unwalkable terrain
        character.x, character.y = 5, 5
        
        # Create a mock method for is_terrain_walkable that returns False for the test
        original_is_walkable = character._is_terrain_walkable
        def mock_is_walkable(terrain_type):
            if terrain_type == basic_map.tiles[6, 5]:
                return False
            return original_is_walkable(terrain_type)
        
        # Apply the mock
        character._is_terrain_walkable = mock_is_walkable
        
        # Now test movement to the unwalkable tile
        success = character.move(basic_map, dx=1, dy=0)
        assert not success
        assert character.x == 5
        assert character.y == 5
        
        # Restore original method
        character._is_terrain_walkable = original_is_walkable
        
        # Test successful movement
        basic_map.tiles[6, 5] = TerrainType.GRASS
        success = character.move(basic_map, dx=1, dy=0)
        assert success
        assert character.x == 6
        assert character.y == 5

    def test_character_z_level_transition(self, basic_map):
        """Test character movement between z-levels."""
        from proto_island.character import Character
        
        basic_map.add_z_level(1)
        basic_map.add_level_transition(0, 1, 5, 5)
        
        character = Character(x=5, y=5, z=0)
        
        # Test z-level transition
        success = character.transition_z_level(basic_map)
        assert success
        assert character.z == 1
        
        # Test failed transition (not on a transition point)
        character.x, character.y = 6, 6
        success = character.transition_z_level(basic_map)
        assert not success
        assert character.z == 1

class TestPlayer:
    def test_player_initialization(self):
        """Test player character initialization."""
        from proto_island.character import Player, CharacterType
        
        player = Player(x=5, y=5, z=1)
        assert player.x == 5
        assert player.y == 5
        assert player.z == 1
        assert player.char_type == CharacterType.PLAYER
        assert player.fov_radius == 8

    def test_player_fov(self, basic_map):
        """Test player field of view calculation."""
        from proto_island.character import Player
        
        player = Player(x=10, y=10)
        fov = player.calculate_fov(basic_map)
        
        # FOV should be a boolean array matching map dimensions
        assert fov.shape == (basic_map.height, basic_map.width)
        assert fov.dtype == bool
        
        # Player's position should be visible
        assert fov[10, 10]
        
        # Points beyond FOV radius should not be visible
        assert not fov[0, 0]  # Distant corner

class TestNPC:
    def test_npc_initialization(self):
        """Test NPC initialization."""
        from proto_island.character import NPC, CharacterType, NPCType, NPCState
        
        npc = NPC(x=5, y=5, z=1, npc_type=NPCType.MERCHANT)
        assert npc.x == 5
        assert npc.y == 5
        assert npc.z == 1
        assert npc.char_type == CharacterType.NPC
        assert npc.npc_type == NPCType.MERCHANT
        assert npc.state == NPCState.IDLE
        assert npc.target is None

    def test_npc_update(self, basic_map):
        """Test NPC state updates."""
        from proto_island.character import NPC, NPCState, NPCType
        
        npc = NPC(x=10, y=10, npc_type=NPCType.VILLAGER)
        
        # Force the NPC into wander state for testing movement
        npc.state = NPCState.WANDER
        
        # Make surrounding tiles walkable
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                basic_map.tiles[npc.y + dy, npc.x + dx] = TerrainType.GRASS
        
        # Initial position
        initial_x, initial_y = npc.x, npc.y
        
        # Update several times and check if the NPC moves
        moved = False
        for _ in range(10):
            npc.update(basic_map)
            if npc.x != initial_x or npc.y != initial_y:
                moved = True
                break
                
        assert moved, "NPC should have moved during updates"

    def test_npc_player_interaction(self, basic_map):
        """Test NPC interaction with player."""
        from proto_island.character import NPC, Player, NPCType
        
        npc = NPC(x=10, y=10, npc_type=NPCType.VILLAGER)
        player = Player(x=npc.x + 2, y=npc.y)
        
        # Check player detection
        assert npc._is_player_nearby(player)
        
        # Move player away
        player.x, player.y = npc.x + 10, npc.y + 10
        
        # Player should no longer be detected
        assert not npc._is_player_nearby(player)

class TestCharacterManager:
    def test_character_manager(self, basic_map):
        """Test character manager functionality."""
        from proto_island.character import CharacterManager, Player, NPC, NPCType, NPCState
        
        manager = CharacterManager()
        player = Player(x=5, y=5)
        npc = NPC(x=10, y=10, npc_type=NPCType.VILLAGER)
        
        # Test setting player
        manager.set_player(player)
        assert manager.player == player
        
        # Test adding NPC
        manager.add_npc(npc)
        assert npc in manager.npcs
        
        # Test getting characters at location
        player.x, player.y, player.z = 5, 5, 0
        npc.x, npc.y, npc.z = 5, 5, 0
        
        characters = manager.get_characters_at_location(5, 5, 0)
        assert len(characters) == 2
        assert player in characters
        assert npc in characters
        
        # Test character not at location
        characters = manager.get_characters_at_location(6, 6, 0)
        assert len(characters) == 0
        
        # Test update method
        initial_x, initial_y = npc.x, npc.y
        npc.state = NPCState.WANDER
        
        # Make surrounding tiles walkable
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if 0 <= npc.y + dy < basic_map.height and 0 <= npc.x + dx < basic_map.width:
                    basic_map.tiles[npc.y + dy, npc.x + dx] = TerrainType.GRASS
        
        # Update and check if NPCs are updated
        manager.update(basic_map)
        # This is hard to test deterministically, so we're simply ensuring
        # the update method runs without errors 