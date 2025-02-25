from enum import Enum, auto
from typing import List, Dict, Optional, Any


class ItemType(Enum):
    """Types of items in the game."""
    GENERAL = auto()    # General items
    WEAPON = auto()     # Weapons
    ARMOR = auto()      # Armor
    CONSUMABLE = auto() # Potions, food, etc.
    QUEST = auto()      # Quest items
    KEY = auto()        # Keys and access items


class Item:
    """Represents an item in the game."""
    
    def __init__(
        self,
        name: str,
        item_type: ItemType,
        weight: float,
        value: int = 0,
        stackable: bool = True,
        quantity: int = 1,
        **properties
    ):
        """Initialize an item.
        
        Args:
            name: Item name
            item_type: Type of item
            weight: Weight per unit (not total weight)
            value: Value in currency
            stackable: Whether items can stack
            quantity: Initial quantity
            **properties: Additional item properties
        """
        self.name = name
        self.item_type = item_type
        self.unit_weight = weight  # Store the weight per unit
        self.weight = weight * quantity  # Total weight
        self.value = value
        
        # Set weapons and quest items as non-stackable by default
        if self.item_type in [ItemType.WEAPON, ItemType.QUEST]:
            self.stackable = False
        else:
            self.stackable = stackable
            
        self.quantity = quantity
        
        # Store additional properties
        for key, value in properties.items():
            setattr(self, key, value)
            
    def stack_with(self, other: 'Item') -> bool:
        """Try to stack this item with another.
        
        Args:
            other: The other item to stack with
            
        Returns:
            bool: True if stacking was successful
        """
        if (
            not self.stackable or
            not other.stackable or
            self.name != other.name or
            self.item_type != other.item_type
        ):
            return False
            
        # Stack items
        self.quantity += other.quantity
        self.weight = self.unit_weight * self.quantity
        return True


class Inventory:
    """Manages a collection of items."""
    
    def __init__(self, capacity: float):
        """Initialize an inventory.
        
        Args:
            capacity: Maximum weight capacity
        """
        self.capacity = capacity
        self.current_weight = 0.0
        self.items: List[Item] = []
        
    def add_item(self, item: Item) -> bool:
        """Add an item to the inventory.
        
        Args:
            item: The item to add
            
        Returns:
            bool: True if item was added successfully
        """
        # Check weight capacity
        if self.current_weight + item.weight > self.capacity:
            return False
            
        # Try to stack with existing items
        if item.stackable:
            for existing_item in self.items:
                if existing_item.name == item.name and existing_item.item_type == item.item_type:
                    # Calculate weight before stacking
                    old_weight = existing_item.weight
                    
                    # Try to stack
                    if existing_item.stack_with(item):
                        # Update inventory weight with the difference
                        self.current_weight += (existing_item.weight - old_weight)
                        return True
                    
        # Add as new item
        self.items.append(item)
        self.current_weight += item.weight
        return True
        
    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """Remove an item from the inventory.
        
        Args:
            item_name: Name of the item to remove
            quantity: Quantity to remove
            
        Returns:
            bool: True if item was removed
        """
        for i, item in enumerate(self.items):
            if item.name == item_name:
                weight_per_unit = item.unit_weight
                
                if item.quantity <= quantity:
                    # Remove the entire stack
                    self.current_weight -= item.weight
                    self.items.pop(i)
                else:
                    # Remove part of the stack
                    weight_to_remove = weight_per_unit * quantity
                    item.quantity -= quantity
                    item.weight = item.unit_weight * item.quantity
                    self.current_weight -= weight_to_remove
                    
                return True
                
        return False
        
    def get_item(self, item_name: str) -> Optional[Item]:
        """Get an item from the inventory without removing it.
        
        Args:
            item_name: Name of the item to get
            
        Returns:
            Optional[Item]: The item, or None if not found
        """
        for item in self.items:
            if item.name == item_name:
                return item
        return None 