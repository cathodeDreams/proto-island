import pytest
from proto_island.character import Character, Player

# We'll need to import the inventory module once it's created
# from proto_island.inventory import Item, ItemType, Inventory

@pytest.fixture
def basic_item():
    """Create a basic item for testing."""
    from proto_island.inventory import Item, ItemType
    return Item(name="Test Item", item_type=ItemType.GENERAL, weight=1.0)

@pytest.fixture
def weapon_item():
    """Create a weapon item for testing."""
    from proto_island.inventory import Item, ItemType
    return Item(
        name="Test Sword",
        item_type=ItemType.WEAPON,
        weight=5.0,
        damage=10,
        value=100
    )

@pytest.fixture
def basic_inventory():
    """Create a basic inventory for testing."""
    from proto_island.inventory import Inventory
    return Inventory(capacity=10)

class TestItem:
    def test_item_initialization(self):
        """Test basic item initialization."""
        from proto_island.inventory import Item, ItemType
        
        item = Item(name="Test Item", item_type=ItemType.GENERAL, weight=1.0)
        assert item.name == "Test Item"
        assert item.item_type == ItemType.GENERAL
        assert item.weight == 1.0
        assert item.value == 0
        assert item.stackable
        assert item.quantity == 1

    def test_weapon_item(self):
        """Test weapon item properties."""
        from proto_island.inventory import Item, ItemType
        
        weapon = Item(
            name="Test Sword",
            item_type=ItemType.WEAPON,
            weight=5.0,
            damage=10,
            value=100
        )
        assert weapon.name == "Test Sword"
        assert weapon.item_type == ItemType.WEAPON
        assert weapon.weight == 5.0
        assert weapon.value == 100
        assert weapon.damage == 10
        assert not weapon.stackable
        assert weapon.quantity == 1

    def test_consumable_item(self):
        """Test consumable item properties."""
        from proto_island.inventory import Item, ItemType
        
        potion = Item(
            name="Healing Potion",
            item_type=ItemType.CONSUMABLE,
            weight=0.5,
            value=25,
            healing=20,
            stackable=True
        )
        assert potion.name == "Healing Potion"
        assert potion.item_type == ItemType.CONSUMABLE
        assert potion.weight == 0.5
        assert potion.value == 25
        assert potion.healing == 20
        assert potion.stackable
        assert potion.quantity == 1

    def test_item_stacking(self):
        """Test item stacking functionality."""
        from proto_island.inventory import Item, ItemType
        
        item1 = Item(name="Gold Coin", item_type=ItemType.GENERAL, weight=0.1, stackable=True)
        item2 = Item(name="Gold Coin", item_type=ItemType.GENERAL, weight=0.1, stackable=True)
        
        # Test stacking
        result = item1.stack_with(item2)
        assert result
        assert item1.quantity == 2
        assert item1.weight == 0.2  # Weight is cumulative
        
        # Test stacking non-matching items
        item3 = Item(name="Silver Coin", item_type=ItemType.GENERAL, weight=0.1, stackable=True)
        result = item1.stack_with(item3)
        assert not result
        assert item1.quantity == 2
        assert item3.quantity == 1
        
        # Test stacking non-stackable items
        weapon1 = Item(name="Sword", item_type=ItemType.WEAPON, weight=5.0, stackable=False)
        weapon2 = Item(name="Sword", item_type=ItemType.WEAPON, weight=5.0, stackable=False)
        result = weapon1.stack_with(weapon2)
        assert not result
        assert weapon1.quantity == 1
        assert weapon2.quantity == 1

class TestInventory:
    def test_inventory_initialization(self):
        """Test inventory initialization."""
        from proto_island.inventory import Inventory
        
        inventory = Inventory(capacity=10)
        assert inventory.capacity == 10
        assert inventory.current_weight == 0
        assert len(inventory.items) == 0

    def test_inventory_add_item(self, basic_item):
        """Test adding items to inventory."""
        from proto_island.inventory import Inventory, Item, ItemType
        
        inventory = Inventory(capacity=10)
        
        # Add an item
        result = inventory.add_item(basic_item)
        assert result
        assert len(inventory.items) == 1
        assert inventory.current_weight == 1.0
        
        # Add identical item (should stack)
        item2 = Item(name="Test Item", item_type=ItemType.GENERAL, weight=1.0)
        result = inventory.add_item(item2)
        assert result
        assert len(inventory.items) == 1  # Still one item type
        assert inventory.items[0].quantity == 2
        assert inventory.current_weight == 2.0

    def test_inventory_remove_item(self, basic_item, basic_inventory):
        """Test removing items from inventory."""
        basic_inventory.add_item(basic_item)
        
        # Add a second item
        basic_inventory.add_item(basic_item)
        assert basic_inventory.items[0].quantity == 2
        
        # Remove one item
        removed = basic_inventory.remove_item(basic_item.name, quantity=1)
        assert removed
        assert len(basic_inventory.items) == 1
        assert basic_inventory.items[0].quantity == 1
        assert basic_inventory.current_weight == 1.0
        
        # Remove the last item
        removed = basic_inventory.remove_item(basic_item.name)
        assert removed
        assert len(basic_inventory.items) == 0
        assert basic_inventory.current_weight == 0

    def test_inventory_capacity(self, basic_inventory, basic_item):
        """Test inventory capacity limits."""
        from proto_island.inventory import Item, ItemType
        
        # Fill inventory to capacity
        for i in range(10):
            new_item = Item(name=f"Item {i}", item_type=ItemType.GENERAL, weight=1.0)
            basic_inventory.add_item(new_item)
            
        assert len(basic_inventory.items) == 10
        assert basic_inventory.current_weight == 10.0
        
        # Try to add one more
        extra_item = Item(name="Extra Item", item_type=ItemType.GENERAL, weight=1.0)
        result = basic_inventory.add_item(extra_item)
        assert not result  # Should fail
        assert len(basic_inventory.items) == 10  # Count unchanged

    def test_inventory_weight_calculation(self, basic_inventory):
        """Test inventory weight calculation."""
        from proto_island.inventory import Item, ItemType
        
        # Add items with different weights
        item1 = Item(name="Light Item", item_type=ItemType.GENERAL, weight=0.5)
        item2 = Item(name="Heavy Item", item_type=ItemType.GENERAL, weight=2.5)
        
        basic_inventory.add_item(item1)
        assert basic_inventory.current_weight == 0.5
        
        basic_inventory.add_item(item2)
        assert basic_inventory.current_weight == 3.0
        
        # Add stackable items
        item3 = Item(name="Stackable", item_type=ItemType.GENERAL, weight=1.0, stackable=True)
        basic_inventory.add_item(item3)
        assert basic_inventory.current_weight == 4.0
        
        # Add another of the same stackable item
        item4 = Item(name="Stackable", item_type=ItemType.GENERAL, weight=1.0, stackable=True)
        basic_inventory.add_item(item4)
        assert basic_inventory.current_weight == 5.0

class TestCharacterInventory:
    def test_character_inventory_integration(self):
        """Test integration between character and inventory systems."""
        from proto_island.inventory import Item, ItemType, Inventory
        
        # Create a character
        character = Character(x=5, y=5)
        
        # Create an inventory for the character
        inventory = Inventory(capacity=50)
        character.inventory = inventory
        
        # Add items to the character's inventory
        item = Item(name="Test Item", item_type=ItemType.GENERAL, weight=1.0)
        character.inventory.add_item(item)
        
        assert len(character.inventory.items) == 1
        assert character.inventory.current_weight == 1.0
        
        # Test item removal
        character.inventory.remove_item("Test Item")
        assert len(character.inventory.items) == 0 