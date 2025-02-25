import pytest
import numpy as np
from src.proto_island.quest import (
    QuestState, QuestObjectiveType, QuestType,
    QuestObjective, Quest, QuestManager
)
from src.proto_island.character import Character, Player, NPC, NPCType, CharacterManager
from src.proto_island.inventory import Item, ItemType, Inventory
from src.proto_island.map import TerrainType

class TestQuestObjective:
    """Test quest objective functionality."""
    
    def test_objective_initialization(self):
        """Test basic objective initialization."""
        objective = QuestObjective(
            objective_type=QuestObjectiveType.COLLECT,
            description="Collect 3 mushrooms",
            target="mushroom",
            required_amount=3
        )
        
        assert objective.objective_type == QuestObjectiveType.COLLECT
        assert objective.description == "Collect 3 mushrooms"
        assert objective.target == "mushroom"
        assert objective.required_amount == 3
        assert objective.current_amount == 0
        assert not objective.is_completed
    
    def test_objective_update_progress(self):
        """Test updating objective progress."""
        objective = QuestObjective(
            objective_type=QuestObjectiveType.COLLECT,
            description="Collect 3 mushrooms",
            target="mushroom",
            required_amount=3
        )
        
        objective.update_progress(1)
        assert objective.current_amount == 1
        assert not objective.is_completed
        
        objective.update_progress(2)
        assert objective.current_amount == 3
        assert objective.is_completed
    
    def test_objective_reset(self):
        """Test resetting an objective."""
        objective = QuestObjective(
            objective_type=QuestObjectiveType.COLLECT,
            description="Collect 3 mushrooms",
            target="mushroom",
            required_amount=3
        )
        
        objective.update_progress(3)
        assert objective.is_completed
        
        objective.reset()
        assert objective.current_amount == 0
        assert not objective.is_completed


class TestQuest:
    """Test quest functionality."""
    
    def test_quest_initialization(self):
        """Test basic quest initialization."""
        quest = Quest(
            title="Mushroom Gathering",
            description="Gather mushrooms for the village healer.",
            quest_type=QuestType.GATHER,
            quest_giver_id="healer_npc"
        )
        
        assert quest.title == "Mushroom Gathering"
        assert quest.description == "Gather mushrooms for the village healer."
        assert quest.quest_type == QuestType.GATHER
        assert quest.quest_giver_id == "healer_npc"
        assert quest.state == QuestState.INACTIVE
        assert len(quest.objectives) == 0
        assert quest.rewards == {}
    
    def test_add_objective(self):
        """Test adding objectives to a quest."""
        quest = Quest(
            title="Mushroom Gathering",
            description="Gather mushrooms for the village healer.",
            quest_type=QuestType.GATHER
        )
        
        quest.add_objective(
            QuestObjective(
                objective_type=QuestObjectiveType.COLLECT,
                description="Collect 3 mushrooms",
                target="mushroom",
                required_amount=3
            )
        )
        
        assert len(quest.objectives) == 1
        assert quest.objectives[0].description == "Collect 3 mushrooms"
    
    def test_add_reward(self):
        """Test adding rewards to a quest."""
        quest = Quest(
            title="Mushroom Gathering",
            description="Gather mushrooms for the village healer.",
            quest_type=QuestType.GATHER
        )
        
        quest.add_reward("gold", 50)
        quest.add_reward("xp", 100)
        
        assert quest.rewards["gold"] == 50
        assert quest.rewards["xp"] == 100
    
    def test_activate_quest(self):
        """Test activating a quest."""
        quest = Quest(
            title="Mushroom Gathering",
            description="Gather mushrooms for the village healer.",
            quest_type=QuestType.GATHER
        )
        
        assert quest.state == QuestState.INACTIVE
        
        quest.activate()
        assert quest.state == QuestState.ACTIVE
    
    def test_complete_quest(self):
        """Test completing a quest."""
        quest = Quest(
            title="Mushroom Gathering",
            description="Gather mushrooms for the village healer.",
            quest_type=QuestType.GATHER
        )
        
        objective = QuestObjective(
            objective_type=QuestObjectiveType.COLLECT,
            description="Collect 3 mushrooms",
            target="mushroom",
            required_amount=3
        )
        quest.add_objective(objective)
        
        quest.activate()
        
        # Quest should not be complete yet
        assert not quest.is_complete
        
        # Complete the objective
        objective.update_progress(3)
        
        # Now the quest should be complete
        assert quest.is_complete
        
        # Mark the quest as completed
        quest.complete()
        assert quest.state == QuestState.COMPLETED
    
    def test_fail_quest(self):
        """Test failing a quest."""
        quest = Quest(
            title="Timed Delivery",
            description="Deliver a package before sunset.",
            quest_type=QuestType.DELIVERY,
            can_fail=True
        )
        
        quest.activate()
        quest.fail()
        
        assert quest.state == QuestState.FAILED
    
    def test_quest_state_transitions(self):
        """Test quest state transitions."""
        quest = Quest(
            title="Mushroom Gathering",
            description="Gather mushrooms for the village healer.",
            quest_type=QuestType.GATHER,
            can_fail=True
        )
        
        # Initial state
        assert quest.state == QuestState.INACTIVE
        
        # Activate
        quest.activate()
        assert quest.state == QuestState.ACTIVE
        
        # Cannot transition from ACTIVE to INACTIVE
        with pytest.raises(ValueError):
            quest.set_state(QuestState.INACTIVE)
        
        # Can complete
        quest.set_state(QuestState.COMPLETED)
        assert quest.state == QuestState.COMPLETED
        
        # Cannot transition from COMPLETED to any other state
        with pytest.raises(ValueError):
            quest.set_state(QuestState.ACTIVE)
        
        # Create a new quest for failure testing
        quest2 = Quest(
            title="Another Quest",
            description="Test quest.",
            quest_type=QuestType.GATHER,
            can_fail=True
        )
        quest2.activate()
        
        # Can fail
        quest2.set_state(QuestState.FAILED)
        assert quest2.state == QuestState.FAILED
        
        # Cannot transition from FAILED to any other state
        with pytest.raises(ValueError):
            quest2.set_state(QuestState.ACTIVE)


class TestQuestManager:
    """Test quest manager functionality."""
    
    def test_quest_manager_initialization(self):
        """Test quest manager initialization."""
        manager = QuestManager()
        
        assert len(manager.quests) == 0
        assert len(manager.available_quests) == 0
        assert len(manager.active_quests) == 0
        assert len(manager.completed_quests) == 0
        assert len(manager.failed_quests) == 0
    
    def test_add_quest(self):
        """Test adding a quest to the manager."""
        manager = QuestManager()
        
        quest = Quest(
            title="Mushroom Gathering",
            description="Gather mushrooms for the village healer.",
            quest_type=QuestType.GATHER
        )
        
        manager.add_quest(quest)
        
        assert len(manager.quests) == 1
        assert len(manager.available_quests) == 1
        assert quest.id in manager.quests
    
    def test_activate_quest(self):
        """Test activating a quest through the manager."""
        manager = QuestManager()
        
        quest = Quest(
            title="Mushroom Gathering",
            description="Gather mushrooms for the village healer.",
            quest_type=QuestType.GATHER
        )
        
        manager.add_quest(quest)
        manager.activate_quest(quest.id)
        
        assert quest.state == QuestState.ACTIVE
        assert len(manager.active_quests) == 1
        assert len(manager.available_quests) == 0
    
    def test_complete_quest(self):
        """Test completing a quest through the manager."""
        manager = QuestManager()
        
        quest = Quest(
            title="Mushroom Gathering",
            description="Gather mushrooms for the village healer.",
            quest_type=QuestType.GATHER
        )
        
        objective = QuestObjective(
            objective_type=QuestObjectiveType.COLLECT,
            description="Collect 3 mushrooms",
            target="mushroom",
            required_amount=3
        )
        quest.add_objective(objective)
        
        manager.add_quest(quest)
        manager.activate_quest(quest.id)
        
        # Complete the objective
        objective.update_progress(3)
        
        # Check for completable quests
        completable_quests = manager.get_completable_quests()
        assert len(completable_quests) == 1
        
        # Complete the quest
        manager.complete_quest(quest.id)
        
        assert quest.state == QuestState.COMPLETED
        assert len(manager.completed_quests) == 1
        assert len(manager.active_quests) == 0
    
    def test_fail_quest(self):
        """Test failing a quest through the manager."""
        manager = QuestManager()
        
        quest = Quest(
            title="Timed Delivery",
            description="Deliver a package before sunset.",
            quest_type=QuestType.DELIVERY,
            can_fail=True
        )
        
        manager.add_quest(quest)
        manager.activate_quest(quest.id)
        manager.fail_quest(quest.id)
        
        assert quest.state == QuestState.FAILED
        assert len(manager.failed_quests) == 1
        assert len(manager.active_quests) == 0
    
    def test_update_quest_objectives(self):
        """Test updating quest objectives through the manager."""
        manager = QuestManager()
        
        # Create a collect quest
        quest = Quest(
            title="Mushroom Gathering",
            description="Gather mushrooms for the village healer.",
            quest_type=QuestType.GATHER
        )
        
        objective = QuestObjective(
            objective_type=QuestObjectiveType.COLLECT,
            description="Collect 3 mushrooms",
            target="mushroom",
            required_amount=3
        )
        quest.add_objective(objective)
        
        manager.add_quest(quest)
        manager.activate_quest(quest.id)
        
        # Update progress for the target item
        manager.update_quest_objectives(QuestObjectiveType.COLLECT, "mushroom", 2)
        
        assert objective.current_amount == 2
        assert not objective.is_completed
        
        # Update again to complete
        manager.update_quest_objectives(QuestObjectiveType.COLLECT, "mushroom", 1)
        
        assert objective.current_amount == 3
        assert objective.is_completed
    
    def test_get_quests_by_state(self):
        """Test getting quests by state."""
        manager = QuestManager()
        
        quest1 = Quest(title="Quest 1", description="Test quest 1", quest_type=QuestType.GATHER)
        quest2 = Quest(title="Quest 2", description="Test quest 2", quest_type=QuestType.DELIVERY)
        quest3 = Quest(title="Quest 3", description="Test quest 3", quest_type=QuestType.KILL)
        
        manager.add_quest(quest1)
        manager.add_quest(quest2)
        manager.add_quest(quest3)
        
        assert len(manager.get_quests_by_state(QuestState.INACTIVE)) == 3
        
        manager.activate_quest(quest1.id)
        manager.activate_quest(quest2.id)
        
        assert len(manager.get_quests_by_state(QuestState.ACTIVE)) == 2
        assert len(manager.get_quests_by_state(QuestState.INACTIVE)) == 1
        
        # Complete quest1
        objective = QuestObjective(
            objective_type=QuestObjectiveType.LOCATION,
            description="Reach the forest",
            target="forest",
            required_amount=1
        )
        quest1.add_objective(objective)
        objective.update_progress(1)
        manager.complete_quest(quest1.id)
        
        assert len(manager.get_quests_by_state(QuestState.COMPLETED)) == 1
        assert len(manager.get_quests_by_state(QuestState.ACTIVE)) == 1
    
    def test_get_quests_from_npc(self):
        """Test getting quests from a specific NPC."""
        manager = QuestManager()
        
        quest1 = Quest(title="Quest 1", description="Test quest 1", quest_type=QuestType.GATHER, quest_giver_id="npc1")
        quest2 = Quest(title="Quest 2", description="Test quest 2", quest_type=QuestType.DELIVERY, quest_giver_id="npc2")
        quest3 = Quest(title="Quest 3", description="Test quest 3", quest_type=QuestType.KILL, quest_giver_id="npc1")
        
        manager.add_quest(quest1)
        manager.add_quest(quest2)
        manager.add_quest(quest3)
        
        npc1_quests = manager.get_quests_from_npc("npc1")
        assert len(npc1_quests) == 2
        assert quest1.id in [q.id for q in npc1_quests]
        assert quest3.id in [q.id for q in npc1_quests]
        
        npc2_quests = manager.get_quests_from_npc("npc2")
        assert len(npc2_quests) == 1
        assert quest2.id in [q.id for q in npc2_quests]


class TestQuestIntegration:
    """Test integration with other systems."""
    
    def setup_method(self):
        """Set up test environment."""
        self.player = Player(10, 10)
        self.inventory = self.player.inventory
        self.quest_manager = QuestManager()
    
    def test_item_collection_quest(self):
        """Test a quest to collect items."""
        # Create a collection quest
        quest = Quest(
            title="Herb Collection",
            description="Collect herbs for the village healer.",
            quest_type=QuestType.GATHER
        )
        
        objective = QuestObjective(
            objective_type=QuestObjectiveType.COLLECT,
            description="Collect 2 healing herbs",
            target="healing_herb",
            required_amount=2
        )
        quest.add_objective(objective)
        quest.add_reward("gold", 50)
        
        # Add to manager and activate
        self.quest_manager.add_quest(quest)
        self.quest_manager.activate_quest(quest.id)
        
        # Player finds and collects herbs
        herb = Item("healing_herb", ItemType.QUEST, 0.1, 5, stackable=True)
        self.inventory.add_item(herb)
        self.quest_manager.update_quest_objectives(QuestObjectiveType.COLLECT, "healing_herb", 1)
        
        assert objective.current_amount == 1
        assert not objective.is_completed
        
        # Player finds another herb
        self.inventory.add_item(Item("healing_herb", ItemType.QUEST, 0.1, 5, stackable=True))
        self.quest_manager.update_quest_objectives(QuestObjectiveType.COLLECT, "healing_herb", 1)
        
        assert objective.current_amount == 2
        assert objective.is_completed
        assert quest.is_complete
        
        # Complete the quest and get rewards
        self.quest_manager.complete_quest(quest.id)
        
        assert quest.state == QuestState.COMPLETED
        assert len(self.quest_manager.completed_quests) == 1
    
    def test_kill_quest(self):
        """Test a quest to defeat enemies."""
        # Create a kill quest
        quest = Quest(
            title="Pest Control",
            description="Clear the cave of bats.",
            quest_type=QuestType.KILL
        )
        
        objective = QuestObjective(
            objective_type=QuestObjectiveType.KILL,
            description="Defeat 3 cave bats",
            target="cave_bat",
            required_amount=3
        )
        quest.add_objective(objective)
        
        # Add to manager and activate
        self.quest_manager.add_quest(quest)
        self.quest_manager.activate_quest(quest.id)
        
        # Player defeats bats
        self.quest_manager.update_quest_objectives(QuestObjectiveType.KILL, "cave_bat", 2)
        
        assert objective.current_amount == 2
        assert not objective.is_completed
        
        # Player defeats the last bat
        self.quest_manager.update_quest_objectives(QuestObjectiveType.KILL, "cave_bat", 1)
        
        assert objective.current_amount == 3
        assert objective.is_completed
        assert quest.is_complete
        
        # Complete the quest
        self.quest_manager.complete_quest(quest.id)
        
        assert quest.state == QuestState.COMPLETED
    
    def test_location_quest(self):
        """Test a quest to reach a location."""
        # Create a location quest
        quest = Quest(
            title="Exploration",
            description="Explore the ancient ruins.",
            quest_type=QuestType.EXPLORE
        )
        
        objective = QuestObjective(
            objective_type=QuestObjectiveType.LOCATION,
            description="Find the ancient ruins",
            target="ancient_ruins",
            required_amount=1
        )
        quest.add_objective(objective)
        
        # Add to manager and activate
        self.quest_manager.add_quest(quest)
        self.quest_manager.activate_quest(quest.id)
        
        # Player reaches the location
        self.quest_manager.update_quest_objectives(QuestObjectiveType.LOCATION, "ancient_ruins", 1)
        
        assert objective.current_amount == 1
        assert objective.is_completed
        assert quest.is_complete
        
        # Complete the quest
        self.quest_manager.complete_quest(quest.id)
        
        assert quest.state == QuestState.COMPLETED
    
    def test_multi_objective_quest(self):
        """Test a quest with multiple objectives."""
        # Create a quest with multiple objectives
        quest = Quest(
            title="Village Supplies",
            description="Gather supplies for the village.",
            quest_type=QuestType.GATHER
        )
        
        objective1 = QuestObjective(
            objective_type=QuestObjectiveType.COLLECT,
            description="Collect 2 logs",
            target="log",
            required_amount=2
        )
        
        objective2 = QuestObjective(
            objective_type=QuestObjectiveType.COLLECT,
            description="Collect 3 stones",
            target="stone",
            required_amount=3
        )
        
        quest.add_objective(objective1)
        quest.add_objective(objective2)
        
        # Add to manager and activate
        self.quest_manager.add_quest(quest)
        self.quest_manager.activate_quest(quest.id)
        
        # Update first objective
        self.quest_manager.update_quest_objectives(QuestObjectiveType.COLLECT, "log", 2)
        
        assert objective1.is_completed
        assert not objective2.is_completed
        assert not quest.is_complete
        
        # Update second objective
        self.quest_manager.update_quest_objectives(QuestObjectiveType.COLLECT, "stone", 3)
        
        assert objective2.is_completed
        assert quest.is_complete
        
        # Complete the quest
        self.quest_manager.complete_quest(quest.id)
        
        assert quest.state == QuestState.COMPLETED 