# Poetry Environment Report
**Generated:** 2025-02-25 01:23:43

---

## Dependencies
```
Resolving dependencies...
Installing dependencies from lock file

No dependencies to install or update

Installing the current project: proto-island (0.1.0)
```

## Installed Packages
```
cffi              1.17.1 Foreign Function Interface for Python calling C code.
coverage          7.6.12 Code coverage measurement for Python
iniconfig         2.0.0  brain-dead simple config-ini parsing
numpy             2.2.3  Fundamental package for array computing in Python
packaging         24.2   Core utilities for Python packages
pluggy            1.5.0  plugin and hook calling mechanisms for python
pycparser         2.22   C parser in Python
pytest            8.3.4  pytest: simple powerful testing with Python
pytest-cov        6.0.0  Pytest plugin for measuring coverage.
scipy             1.15.2 Fundamental algorithms for scientific computing in...
tcod              16.2.3 The official Python port of libtcod.
typing-extensions 4.12.2 Backported and Experimental Type Hints for Python ...
```

## Environment Information
```

Virtualenv
Python:         3.12.9
Implementation: CPython
Path:           /home/user/.cache/pypoetry/virtualenvs/proto-island-jz_o8MaH-py3.12
Executable:     /home/user/.cache/pypoetry/virtualenvs/proto-island-jz_o8MaH-py3.12/bin/python
Valid:          True

Base
Platform:   linux
OS:         posix
Python:     3.12.9
Path:       /home/user/.pyenv/versions/3.12.9
Executable: /home/user/.pyenv/versions/3.12.9/bin/python3.12
```

## Test Results
```
============================= test session starts ==============================
platform linux -- Python 3.12.9, pytest-8.3.4, pluggy-1.5.0 -- /home/user/.cache/pypoetry/virtualenvs/proto-island-jz_o8MaH-py3.12/bin/python
cachedir: .pytest_cache
rootdir: /home/user/Dev/proto_island
configfile: pyproject.toml
testpaths: tests
plugins: cov-6.0.0
collecting ... collected 75 items

tests/test_cave.py::test_cave_generator_initialization PASSED            [  1%]
tests/test_cave.py::test_cave_generation PASSED                          [  2%]
tests/test_cave.py::test_cave_connectivity PASSED                        [  4%]
tests/test_cave.py::test_cave_integration PASSED                         [  5%]
tests/test_cave.py::test_cave_entrance_generation PASSED                 [  6%]
tests/test_character.py::TestCharacter::test_character_initialization PASSED [  8%]
tests/test_character.py::TestCharacter::test_character_movement PASSED   [  9%]
tests/test_character.py::TestCharacter::test_character_z_level_transition PASSED [ 10%]
tests/test_character.py::TestPlayer::test_player_initialization PASSED   [ 12%]
tests/test_character.py::TestPlayer::test_player_fov PASSED              [ 13%]
tests/test_character.py::TestNPC::test_npc_initialization PASSED         [ 14%]
tests/test_character.py::TestNPC::test_npc_update PASSED                 [ 16%]
tests/test_character.py::TestNPC::test_npc_player_interaction PASSED     [ 17%]
tests/test_character.py::TestCharacterManager::test_character_manager PASSED [ 18%]
tests/test_inventory.py::TestItem::test_item_initialization PASSED       [ 20%]
tests/test_inventory.py::TestItem::test_weapon_item PASSED               [ 21%]
tests/test_inventory.py::TestItem::test_consumable_item PASSED           [ 22%]
tests/test_inventory.py::TestItem::test_item_stacking PASSED             [ 24%]
tests/test_inventory.py::TestInventory::test_inventory_initialization PASSED [ 25%]
tests/test_inventory.py::TestInventory::test_inventory_add_item PASSED   [ 26%]
tests/test_inventory.py::TestInventory::test_inventory_remove_item PASSED [ 28%]
tests/test_inventory.py::TestInventory::test_inventory_capacity PASSED   [ 29%]
tests/test_inventory.py::TestInventory::test_inventory_weight_calculation PASSED [ 30%]
tests/test_inventory.py::TestCharacterInventory::test_character_inventory_integration PASSED [ 32%]
tests/test_lighting.py::test_lighting_system_initialization PASSED       [ 33%]
tests/test_lighting.py::test_natural_light_day_cycle PASSED              [ 34%]
tests/test_lighting.py::test_surface_reflectivity PASSED                 [ 36%]
tests/test_lighting.py::test_light_level_bounds PASSED                   [ 37%]
tests/test_lighting.py::test_get_light_level PASSED                      [ 38%]
tests/test_map.py::test_map_initialization PASSED                        [ 40%]
tests/test_map.py::test_terrain_types PASSED                             [ 41%]
tests/test_map.py::test_map_bounds PASSED                                [ 42%]
tests/test_map.py::test_terrain_generation PASSED                        [ 44%]
tests/test_map.py::test_terrain_features PASSED                          [ 45%]
tests/test_map.py::test_lighting_integration PASSED                      [ 46%]
tests/test_map.py::test_terrain_lighting_interaction PASSED              [ 48%]
tests/test_map.py::TestZLevels::test_z_level_initialization PASSED       [ 49%]
tests/test_map.py::TestZLevels::test_z_level_navigation PASSED           [ 50%]
tests/test_map.py::TestZLevels::test_z_level_state_persistence PASSED    [ 52%]
tests/test_map.py::TestZLevels::test_z_level_connectivity PASSED         [ 53%]
tests/test_multi_floor_buildings.py::TestMultiFloorBuildings::test_multi_floor_building_generation PASSED [ 54%]
tests/test_multi_floor_buildings.py::TestMultiFloorBuildings::test_variable_floor_sizes PASSED [ 56%]
tests/test_multi_floor_buildings.py::TestMultiFloorBuildings::test_map_integration PASSED [ 57%]
tests/test_multi_floor_buildings.py::TestMultiFloorBuildings::test_artificial_lighting_at_staircases PASSED [ 58%]
tests/test_multi_floor_buildings.py::TestMultiFloorBuildings::test_different_structure_types PASSED [ 60%]
tests/test_structure.py::TestStructureGenerator::test_structure_generator_initialization PASSED [ 61%]
tests/test_structure.py::TestStructureGenerator::test_structure_type_enum PASSED [ 62%]
tests/test_structure.py::TestStructureGenerator::test_building_placement_constraints PASSED [ 64%]
tests/test_structure.py::TestStructureGenerator::test_bsp_generation PASSED [ 65%]
tests/test_structure.py::TestStructureGenerator::test_structure_connectivity PASSED [ 66%]
tests/test_structure.py::TestStructureGenerator::test_map_integration PASSED [ 68%]
tests/test_structure.py::TestStructureGenerator::test_artificial_light_sources PASSED [ 69%]
tests/test_time.py::test_time_system_initialization PASSED               [ 70%]
tests/test_time.py::test_time_advancement PASSED                         [ 72%]
tests/test_time.py::test_multi_day_advancement PASSED                    [ 73%]
tests/test_time.py::test_daylight_factor PASSED                          [ 74%]
tests/test_time.py::test_moon_illumination PASSED                        [ 76%]
tests/test_time.py::test_weather_light_modifier PASSED                   [ 77%]
tests/test_time.py::test_moon_phase_advancement PASSED                   [ 78%]
tests/test_time.py::test_weather_transition PASSED                       [ 80%]
tests/test_time.py::test_get_star_positions PASSED                       [ 81%]
tests/test_time_coverage.py::test_weather_selection_with_controlled_randomness PASSED [ 82%]
tests/test_time_coverage.py::test_weather_weights_for_all_conditions PASSED [ 84%]
tests/test_time_coverage.py::test_specific_weather_transitions PASSED    [ 85%]
tests/test_time_coverage.py::test_moon_illumination_at_exact_midnight PASSED [ 86%]
tests/test_time_coverage.py::test_all_weather_light_modifiers PASSED     [ 88%]
tests/test_time_coverage.py::test_star_positions_day_night PASSED        [ 89%]
tests/test_time_coverage.py::test_star_positions_structure PASSED        [ 90%]
tests/test_time_coverage.py::test_update_weather_transition PASSED       [ 92%]
tests/test_time_integration.py::test_map_time_system_integration PASSED  [ 93%]
tests/test_time_integration.py::test_set_time_updates_lighting PASSED    [ 94%]
tests/test_time_integration.py::test_advance_time PASSED                 [ 96%]
tests/test_time_integration.py::test_z_level_lighting_consistency PASSED [ 97%]
tests/test_time_integration.py::test_weather_affects_lighting PASSED     [ 98%]
tests/test_time_integration.py::test_moon_phase_affects_night_lighting PASSED [100%]

---------- coverage: platform linux, python 3.12.9-final-0 -----------
Name                            Stmts   Miss  Cover
---------------------------------------------------
src/proto_island/__init__.py        0      0   100%
src/proto_island/cave.py           80      2    98%
src/proto_island/character.py     122     15    88%
src/proto_island/inventory.py      64      5    92%
src/proto_island/lighting.py       89      3    97%
src/proto_island/map.py           188     14    93%
src/proto_island/structure.py     319     18    94%
src/proto_island/time.py          137      2    99%
---------------------------------------------------
TOTAL                             999     59    94%


============================= 75 passed in 11.53s ==============================
```

## Project Directory Structure
```
.
├── docs
│   ├── island-design-doc.md
│   ├── poetry_environment_report.md
│   ├── project_status.md
│   ├── tcod_performance.md
│   ├── tcod_reference.md
│   └── tcod_testing_patterns.md
├── poetry.lock
├── poetry_report.txt
├── pyproject.toml
├── README.md
├── report.sh
├── src
│   └── proto_island
│       ├── cave.py
│       ├── character.py
│       ├── __init__.py
│       ├── inventory.py
│       ├── lighting.py
│       ├── map.py
│       ├── structure.py
│       └── time.py
└── tests
    ├── __init__.py
    ├── test_cave.py
    ├── test_character.py
    ├── test_inventory.py
    ├── test_lighting.py
    ├── test_map.py
    ├── test_multi_floor_buildings.py
    ├── test_structure.py
    ├── test_time_coverage.py
    ├── test_time_integration.py
    └── test_time.py

5 directories, 30 files
```

---
*Report generated by report.sh*
