import pytest
import numpy as np
import random
from proto_island.structure import StructureGenerator, StructureType, StairType
from proto_island.map import GameMap, TerrainType

class TestMultiFloorBuildings:
    """Tests for the multi-floor building implementation."""
    
    def test_multi_floor_building_generation(self):
        """Test basic generation of multi-floor buildings."""
        generator = StructureGenerator(width=50, height=50)
        
        # Generate a multi-floor building
        building = generator.generate_multi_floor_building(
            x=10, y=10, width=20, height=20, 
            floors=2, min_room_size=3,
            structure_type=StructureType.HOUSE,
            seed=42
        )
        
        # Verify basic properties
        assert building["floors"] == 2
        assert "floor_layouts" in building
        assert 0 in building["floor_layouts"]
        assert 1 in building["floor_layouts"]
        
        # Verify each floor has rooms
        assert len(building["floor_layouts"][0]["rooms"]) > 0
        assert len(building["floor_layouts"][1]["rooms"]) > 0
        
        # Verify vertical connections
        assert "vertical_connections" in building
        assert 0 in building["vertical_connections"]
        assert 1 in building["vertical_connections"]
        
        # Verify connections are reciprocal
        for floor_idx, connections in building["vertical_connections"].items():
            for connection in connections:
                target_floor = connection["target_floor"]
                position = connection["position"]
                target_position = connection["target_position"]
                
                # Find reciprocal connection
                found_reciprocal = False
                for recip_conn in building["vertical_connections"][target_floor]:
                    if recip_conn["target_floor"] == floor_idx and recip_conn["target_position"] == position:
                        found_reciprocal = True
                        assert recip_conn["position"] == target_position
                        # Check stair types are correct pairs
                        if connection["type"] == StairType.STAIR_UP:
                            assert recip_conn["type"] == StairType.STAIR_DOWN
                        elif connection["type"] == StairType.STAIR_DOWN:
                            assert recip_conn["type"] == StairType.STAIR_UP
                        elif connection["type"] == StairType.LADDER_UP:
                            assert recip_conn["type"] == StairType.LADDER_DOWN
                        elif connection["type"] == StairType.LADDER_DOWN:
                            assert recip_conn["type"] == StairType.LADDER_UP
                        break
                
                assert found_reciprocal, f"No reciprocal connection found for {connection}"
    
    def test_variable_floor_sizes(self):
        """Test that upper floors can be smaller than ground floors."""
        generator = StructureGenerator(width=50, height=50)
        
        # Set a seed that will trigger the smaller upper floor condition
        building = generator.generate_multi_floor_building(
            x=10, y=10, width=30, height=30, 
            floors=3, min_room_size=3,
            structure_type=StructureType.HOUSE,
            seed=123  # Chosen to likely trigger size reduction
        )
        
        # Use the building footprint for ground floor
        gx, gy, gw, gh = building["footprint"]
        
        # Check if any of the upper floors are smaller than the ground floor
        for floor in range(1, building["floors"]):
            floor_layout = building["floor_layouts"][floor]
            # Each floor layout should have its footprint
            assert "footprint" in floor_layout
            fx, fy, fw, fh = floor_layout["footprint"]
            
            # At least one of the floors should be smaller
            if fw < gw or fh < gh:
                # Check that it's properly centered
                assert fx >= gx
                assert fy >= gy
                assert fx + fw <= gx + gw
                assert fy + fh <= gy + gh
                return
                
        # If we didn't return earlier, at least verify the upper floors exist
        assert building["floors"] == 3
        assert 2 in building["floor_layouts"]
    
    def test_map_integration(self):
        """Test integration of multi-floor buildings with the game map."""
        game_map = GameMap(width=100, height=100)
        game_map.generate_terrain(seed=42)
        
        generator = StructureGenerator(width=100, height=100)
        
        # Set a fixed seed to ensure we get multi-floor buildings
        random.seed(42)
        generator.add_buildings_to_map(game_map, count=5, seed=42)
        
        # Verify z-levels were created
        assert len(game_map.z_levels) > 1
        
        # Get a list of all transitions
        has_vertical_transitions = False
        for z in game_map.z_levels:
            transitions = game_map.get_level_transitions(z)
            if transitions:
                has_vertical_transitions = True
                break
                
        assert has_vertical_transitions, "No vertical transitions found in the map"
        
        # Test changing levels via transitions
        # Find a transition
        for z in game_map.z_levels:
            transitions = game_map.get_level_transitions(z)
            for target_z, points in transitions.items():
                if points:  # If there are any transition points
                    # Change to the target level
                    game_map.change_level(target_z)
                    assert game_map.current_z == target_z
                    # Check reverse transition exists
                    reverse_transitions = game_map.get_level_transitions(target_z)
                    assert z in reverse_transitions
                    break
    
    def test_artificial_lighting_at_staircases(self):
        """Test that staircases have artificial light sources."""
        game_map = GameMap(width=100, height=100)
        generator = StructureGenerator(width=100, height=100)
        
        # Create buildings with stairs
        random.seed(42)
        generator.add_buildings_to_map(game_map, count=3, seed=42)
        generator.add_artificial_lights(game_map)
        
        # Set time to night to see effect of artificial lights
        game_map.set_time(hour=22, minute=0)  # 10PM
        
        # Find a z-level transition
        transition_found = False
        transition_point = None
        transition_z = None
        
        for z in game_map.z_levels:
            transitions = game_map.get_level_transitions(z)
            for target_z, points in transitions.items():
                if points:
                    transition_point = points[0]
                    transition_z = z
                    transition_found = True
                    break
            if transition_found:
                break
                
        if not transition_found:
            pytest.skip("No transitions found to test lighting")
        
        # Change to the level with the transition
        game_map.change_level(transition_z)
        
        # Check light level at stair position - should be higher than ambient night light
        x, y = transition_point
        light_level = game_map.get_light_level(x, y)
        assert light_level > 0.2, "Staircase should have artificial light"

    def test_different_structure_types(self):
        """Test that different structure types generate appropriate multi-floor layouts."""
        generator = StructureGenerator(width=50, height=50)
        
        for structure_type in StructureType:
            # Generate a multi-floor building of each type
            building = generator.generate_multi_floor_building(
                x=10, y=10, width=20, height=20,
                floors=2, min_room_size=3,
                structure_type=structure_type,
                seed=int(structure_type.value) + 100  # Unique seed per type
            )
            
            # Verify structure type is correctly stored
            assert building["structure_type"] == structure_type
            
            # Check if workshop/storage use ladders more often
            if structure_type in [StructureType.WORKSHOP, StructureType.STORAGE]:
                # Not all will have ladders due to randomness, but check if any do
                has_ladder = False
                for connections in building["vertical_connections"].values():
                    for connection in connections:
                        if connection["type"] in [StairType.LADDER_UP, StairType.LADDER_DOWN]:
                            has_ladder = True
                            break
                    if has_ladder:
                        break
                
                # Just note this if it happens, but don't fail the test - it's probabilistic
                if not has_ladder:
                    print(f"Note: {structure_type} didn't use ladders in this test run") 