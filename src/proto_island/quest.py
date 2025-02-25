from enum import Enum, auto
import uuid
from typing import List, Dict, Optional, Any


class QuestState(Enum):
    """Possible states for a quest."""
    INACTIVE = auto()  # Not yet started
    ACTIVE = auto()    # In progress
    COMPLETED = auto() # Successfully completed
    FAILED = auto()    # Failed to complete


class QuestObjectiveType(Enum):
    """Types of quest objectives."""
    COLLECT = auto()  # Collect items
    KILL = auto()     # Defeat enemies
    LOCATION = auto() # Reach a location
    ESCORT = auto()   # Escort an NPC
    DELIVER = auto()  # Deliver an item
    TALK = auto()     # Talk to an NPC


class QuestType(Enum):
    """Types of quests."""
    GATHER = auto()   # Gathering resources
    KILL = auto()     # Combat-focused
    EXPLORE = auto()  # Exploration-focused
    DELIVERY = auto() # Item delivery
    ESCORT = auto()   # NPC protection
    DIALOGUE = auto() # Conversation-based


class QuestObjective:
    """Represents a single objective within a quest."""
    
    def __init__(
        self,
        objective_type: QuestObjectiveType,
        description: str,
        target: str,
        required_amount: int = 1,
        current_amount: int = 0
    ):
        """Initialize a quest objective.
        
        Args:
            objective_type: Type of objective
            description: Description of the objective
            target: Target of the objective (item name, enemy type, etc.)
            required_amount: Amount required to complete
            current_amount: Current progress
        """
        self.objective_type = objective_type
        self.description = description
        self.target = target
        self.required_amount = required_amount
        self.current_amount = current_amount
        self.is_completed = False
        
    def update_progress(self, amount: int) -> None:
        """Update progress towards completing the objective.
        
        Args:
            amount: Amount to add to current progress
        """
        self.current_amount += amount
        if self.current_amount >= self.required_amount:
            self.current_amount = self.required_amount
            self.is_completed = True
            
    def reset(self) -> None:
        """Reset progress on the objective."""
        self.current_amount = 0
        self.is_completed = False


class Quest:
    """Represents a quest in the game."""
    
    def __init__(
        self,
        title: str,
        description: str,
        quest_type: QuestType,
        quest_giver_id: str = "",
        can_fail: bool = False
    ):
        """Initialize a quest.
        
        Args:
            title: Quest title
            description: Quest description
            quest_type: Type of quest
            quest_giver_id: ID of the NPC giving this quest
            can_fail: Whether this quest can fail
        """
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.quest_type = quest_type
        self.quest_giver_id = quest_giver_id
        self.state = QuestState.INACTIVE
        self.objectives: List[QuestObjective] = []
        self.rewards: Dict[str, Any] = {}
        self.can_fail = can_fail
        
    def add_objective(self, objective: QuestObjective) -> None:
        """Add an objective to this quest.
        
        Args:
            objective: The objective to add
        """
        self.objectives.append(objective)
        
    def add_reward(self, reward_type: str, value: Any) -> None:
        """Add a reward to this quest.
        
        Args:
            reward_type: Type of reward (e.g., "gold", "xp", "item")
            value: Value of the reward
        """
        self.rewards[reward_type] = value
        
    def activate(self) -> None:
        """Activate this quest."""
        self.set_state(QuestState.ACTIVE)
        
    def complete(self) -> None:
        """Mark this quest as completed."""
        self.set_state(QuestState.COMPLETED)
        
    def fail(self) -> None:
        """Mark this quest as failed."""
        if not self.can_fail:
            raise ValueError(f"Quest '{self.title}' cannot fail")
        self.set_state(QuestState.FAILED)
        
    def set_state(self, new_state: QuestState) -> None:
        """Set the quest state with validation.
        
        Args:
            new_state: The new state for the quest
            
        Raises:
            ValueError: If the state transition is invalid
        """
        # Define valid state transitions
        valid_transitions = {
            QuestState.INACTIVE: [QuestState.ACTIVE],
            QuestState.ACTIVE: [QuestState.COMPLETED, QuestState.FAILED],
            QuestState.COMPLETED: [],  # Terminal state
            QuestState.FAILED: []      # Terminal state
        }
        
        if new_state not in valid_transitions[self.state]:
            raise ValueError(
                f"Invalid state transition from {self.state} to {new_state}"
            )
            
        self.state = new_state
    
    @property
    def is_complete(self) -> bool:
        """Check if all objectives are completed.
        
        Returns:
            bool: True if all objectives are completed
        """
        if not self.objectives:
            return False
        return all(obj.is_completed for obj in self.objectives)


class QuestManager:
    """Manages quests in the game."""
    
    def __init__(self):
        """Initialize the quest manager."""
        self.quests: Dict[str, Quest] = {}
        
    def add_quest(self, quest: Quest) -> None:
        """Add a quest to the manager.
        
        Args:
            quest: The quest to add
        """
        self.quests[quest.id] = quest
        
    def activate_quest(self, quest_id: str) -> None:
        """Activate a quest.
        
        Args:
            quest_id: ID of the quest to activate
        """
        if quest_id in self.quests:
            self.quests[quest_id].activate()
            
    def complete_quest(self, quest_id: str) -> None:
        """Mark a quest as completed.
        
        Args:
            quest_id: ID of the quest to complete
        """
        if quest_id in self.quests:
            self.quests[quest_id].complete()
            
    def fail_quest(self, quest_id: str) -> None:
        """Mark a quest as failed.
        
        Args:
            quest_id: ID of the quest to fail
        """
        if quest_id in self.quests:
            self.quests[quest_id].fail()
            
    def update_quest_objectives(
        self,
        objective_type: QuestObjectiveType,
        target: str,
        amount: int = 1
    ) -> None:
        """Update objectives across all active quests.
        
        Args:
            objective_type: Type of objective to update
            target: Target to update
            amount: Amount to update by
        """
        for quest in self.active_quests:
            for objective in quest.objectives:
                if (
                    objective.objective_type == objective_type and
                    objective.target == target
                ):
                    objective.update_progress(amount)
    
    def get_completable_quests(self) -> List[Quest]:
        """Get active quests that are ready to be completed.
        
        Returns:
            List[Quest]: List of completable quests
        """
        return [
            quest for quest in self.active_quests
            if quest.is_complete
        ]
    
    def get_quests_by_state(self, state: QuestState) -> List[Quest]:
        """Get quests with the specified state.
        
        Args:
            state: State to filter by
            
        Returns:
            List[Quest]: List of quests with the specified state
        """
        return [
            quest for quest in self.quests.values()
            if quest.state == state
        ]
    
    def get_quests_from_npc(self, npc_id: str) -> List[Quest]:
        """Get quests from a specific NPC.
        
        Args:
            npc_id: ID of the NPC
            
        Returns:
            List[Quest]: List of quests from the NPC
        """
        return [
            quest for quest in self.quests.values()
            if quest.quest_giver_id == npc_id
        ]
    
    @property
    def available_quests(self) -> List[Quest]:
        """Get quests that are available but not yet active.
        
        Returns:
            List[Quest]: List of available quests
        """
        return self.get_quests_by_state(QuestState.INACTIVE)
    
    @property
    def active_quests(self) -> List[Quest]:
        """Get currently active quests.
        
        Returns:
            List[Quest]: List of active quests
        """
        return self.get_quests_by_state(QuestState.ACTIVE)
    
    @property
    def completed_quests(self) -> List[Quest]:
        """Get completed quests.
        
        Returns:
            List[Quest]: List of completed quests
        """
        return self.get_quests_by_state(QuestState.COMPLETED)
    
    @property
    def failed_quests(self) -> List[Quest]:
        """Get failed quests.
        
        Returns:
            List[Quest]: List of failed quests
        """
        return self.get_quests_by_state(QuestState.FAILED) 