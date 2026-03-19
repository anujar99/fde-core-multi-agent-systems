"""
Pasta Factory Exercise - Starter Code
====================================

In this exercise, you'll extend the Italian Pasta Factory multi-agent system 
to handle more complex scenarios with shared state coordination and proper
multi-agent orchestration patterns.

You'll need to:
1. Implement the missing production and custom recipe tools
2. Create the CustomPastaDesignerAgent
3. Build the proper Orchestrator using ToolCallingAgent
4. Add coordination tools that route requests between specialized agents

This demonstrates extending multi-agent systems with new capabilities while
maintaining proper orchestration patterns.
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
import random
from dataclasses import dataclass, field, asdict
import traceback

from smolagents import (
    ToolCallingAgent,
    OpenAIServerModel,
    tool,
)

# Load your OpenAI API key
import os
import dotenv
dotenv.load_dotenv(dotenv_path="../.env")
openai_api_key = os.getenv("UDACITY_OPENAI_API_KEY")

model = OpenAIServerModel(
    model_id="gpt-4o-mini",
    api_base="https://openai.vocareum.com/v1",
    api_key=openai_api_key,
)

# Pasta Factory State Management

@dataclass
class PastaOrder:
    order_id: str
    pasta_shape: str
    quantity: float  # in kg
    status: str = "pending"  # pending, queued, completed, cancelled
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: int = 1  # 1 = normal, 2 = rush, 3 = emergency
    customer_notes: str = ""
    estimated_delivery_date: str = ""

@dataclass
class FactoryState:
    inventory: Dict[str, float] = field(default_factory=lambda: {
        "flour": 10.0,  # kg
        "water": 5.0,   # liters
        "eggs": 24,     # count
        "semolina": 8.0 # kg
    })
    production_queue: List[PastaOrder] = field(default_factory=list)
    pasta_recipes: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "spaghetti": {"flour": 0.2, "water": 0.1},
        "fettuccine": {"flour": 0.25, "water": 0.1},
        "penne": {"flour": 0.2, "water": 0.1},
        "ravioli": {"flour": 0.3, "water": 0.1, "eggs": 2},
        "lasagna": {"flour": 0.3, "water": 0.15, "eggs": 3}
    })
    custom_recipes: Dict[str, Dict[str, float]] = field(default_factory=dict)
    order_counter: int = 0
    known_pasta_shapes: List[str] = field(default_factory=lambda: [
        "spaghetti", "fettuccine", "penne", "ravioli", "lasagna"
    ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inventory": self.inventory,
            "production_queue": [asdict(order) for order in self.production_queue],
            "pasta_recipes": self.pasta_recipes,
            "custom_recipes": self.custom_recipes
        }
    
    def update_known_pasta_shapes(self):
        """Update the list of known pasta shapes based on recipes."""
        self.known_pasta_shapes = list(self.pasta_recipes.keys()) + list(self.custom_recipes.keys())

# Initialize the shared factory state
factory_state = FactoryState()

# ======= Agent Tools =======

@tool
def check_pasta_recipe(pasta_shape: str) -> Dict[str, float]:
    """
    Check what ingredients are needed for a specific pasta shape.
    Returns a dictionary of ingredients and amounts needed per kg of pasta.

    Args:
        pasta_shape: The name of the past shape to check

    Returns:
        Dict[str, float] A dictionary of recipe ingredients and the amounts required per kg of pasta 
    """
    if pasta_shape in factory_state.pasta_recipes:
        return factory_state.pasta_recipes[pasta_shape]
    elif pasta_shape in factory_state.custom_recipes:
        return factory_state.custom_recipes[pasta_shape]
    return {}

@tool
def check_inventory() -> Dict[str, float]:
    """Check current inventory levels of all ingredients."""
    return factory_state.inventory

@tool
def generate_order_id() -> str:
    """Generate a unique order ID."""
    factory_state.order_counter += 1
    return f"ORD-{factory_state.order_counter:04d}"

@tool
def list_available_pasta_shapes() -> List[str]:
    """List all available pasta shapes that can be ordered."""
    return factory_state.known_pasta_shapes

@tool
def update_inventory(ingredient: str, amount: float) -> Dict[str, Any]:
    """
    Update the inventory amount for a specific ingredient.
    
    Args:
        ingredient: Name of the ingredient
        amount: New amount (will replace current amount)
        
    Returns:
        Status of the inventory update
    """
    if ingredient not in factory_state.inventory:
        return {
            "success": False,
            "message": f"Unknown ingredient: {ingredient}. Cannot update inventory."
        }
    
    old_amount = factory_state.inventory[ingredient]
    factory_state.inventory[ingredient] = amount
    
    return {
        "success": True,
        "message": f"Inventory updated: {ingredient} from {old_amount} to {amount}.",
        "ingredient": ingredient,
        "old_amount": old_amount,
        "new_amount": amount
    }

@tool
def check_production_capacity(days_ahead: int = 7) -> Dict[str, Any]:
    """
    Check the current production capacity and queue for the next X days.
    Returns information about queue size and estimated completion times.

    Args:
        days_ahead (str): The time window in days (default=7) to check the production capacity
    
    Returns:
        Dict[str, Any] Information about the queue size and estimated completion times
    """
    # This block of code is to actually use days_ahead.
    # cutoff = datetime.now() + timedelta(days=days_ahead)
    # queue = factory_state.production_queue
    # queue_for_days_ahead = [
    #     order for order in queue
    #     if datetime.fromisoformat(order.estimated_delivery_date) <= cutoff
    # ]
    # queue_size = len(queue_for_days_ahead)
    
    # # Calculate the total production volume (in kg)
    # total_volume = sum(order.quantity for order in queue_for_days_ahead)

    # This code does not use days_ahead
    queue_size = len(factory_state.production_queue)
    
    # Calculate the total production volume (in kg)
    total_volume = sum(order.quantity for order in factory_state.production_queue)
    
    # Simple capacity estimation: assume we can produce 10kg per day
    daily_capacity = 10.0  # kg per day
    days_to_complete = max(1, total_volume / daily_capacity)
    
    # Consider priority orders
    priority_orders = [o for o in factory_state.production_queue if o.priority > 1]
    priority_volume = sum(order.quantity for order in priority_orders)
    
    return {
        "queue_size": queue_size,
        "total_volume_kg": total_volume,
        "days_to_complete_current_queue": days_to_complete,
        "daily_capacity_kg": daily_capacity,
        "priority_orders": len(priority_orders),
        "priority_volume_kg": priority_volume
    }

# TODO: Implement the following tools

@tool
def add_to_production_queue(
    order_id: str,
    pasta_shape: str,
    quantity: float,
    priority: int = 1,
    customer_notes: str = ""
) -> Dict[str, Any]:
    """
    Add an order to the production queue.
    
    Args:
        order_id: Unique order identifier
        pasta_shape: Type of pasta to produce
        quantity: Amount in kg
        priority: Order priority (1=normal, 2=rush, 3=emergency)
        customer_notes: Additional notes from customer
        
    Returns:
        Status of the queuing operation with estimated delivery date
    """
    # TODO: Implement this function
    # 1. Verify that pasta_shape is valid using check_pasta_recipe
    if pasta_shape not in list_available_pasta_shapes():
        return {
            "success": False,
            "message": f"Uh oh, {pasta_shape} is not a valid pasta shape!"
        }
    
    # 2. Calculate required ingredients and check inventory availability
    pasta_recipe = check_pasta_recipe(pasta_shape)
    inventory = check_inventory()
    for ingredient in pasta_recipe.keys():
        if (pasta_recipe[ingredient] * quantity) > inventory[ingredient]:
            return {
                "success": False,
                "message": f"We have a problem. There is not enough {ingredient} in the factory inventory!"
            }

    # 4. Calculate estimated delivery date based on priority and production capacity
    production_capacity = check_production_capacity()
    days_to_complete = production_capacity["days_to_complete_current_queue"]
    if priority == 3:
        days_to_complete = 1
    elif priority == 2:
        days_to_complete = max(1, days_to_complete / 2)
    estimated_delivery_date = datetime.now() + timedelta(days=days_to_complete)
    
    # 3. Create PastaOrder object and add to factory_state.production_queue
    new_pasta_order = PastaOrder(
        order_id=order_id,
        pasta_shape=pasta_shape,
        quantity=quantity,
        priority=priority,
        customer_notes=customer_notes,
        estimated_delivery_date=estimated_delivery_date.date().isoformat()
    )
    factory_state.production_queue.append(new_pasta_order)

    # 5. Update inventory by subtracting required ingredients
    for ingredient in pasta_recipe.keys():
        new_ingredient_amount = inventory[ingredient] - (pasta_recipe[ingredient] * quantity)
        update_inventory(ingredient=ingredient, amount=new_ingredient_amount)
    
    # 6. Return success status with delivery date
    return {
        "success": True,
        "message": f"Succesfully placed the order for {quantity}kg of {pasta_shape}.",
        "delivery_date": estimated_delivery_date.date()
    }

@tool
def create_custom_pasta_recipe(
    pasta_name: str,
    ingredients: Dict[str, float]
) -> Dict[str, Any]:
    """
    Create a custom pasta recipe with specific ingredient ratios.
    
    Args:
        pasta_name: Name of the custom pasta
        ingredients: Dictionary mapping ingredient names to amounts needed per kg
        
    Returns:
        Status of the recipe creation
    """
    # TODO: Implement this function
    # 1. Validate ingredients exist in factory_state.inventory
    inventory = check_inventory()
    for ingredient in ingredients:
        if ingredient not in inventory.keys():
            return {
                "success": False,
                "message": f"We cannot accommodate this recipe. We do not have ingredient {ingredient}."
            }

    # 2. Check if recipe name already exists
    if pasta_name in list_available_pasta_shapes():
        return {
            "success": False,
            "message": f"Pasta name {pasta_name} is taken, we cannot make a new pasta shape with that name."
        }

    # 3. Add the custom recipe to factory_state.custom_recipes
    factory_state.custom_recipes[pasta_name] = ingredients

    # 4. Update factory_state.known_pasta_shapes using update_known_pasta_shapes()
    factory_state.update_known_pasta_shapes()

    # 5. Return success status with recipe details
    return {
        "success": True,
        "message": f"Successfully created recipe for {pasta_name} with ingredients {json.dumps(ingredients)}"
    }

@tool
def prioritize_order(order_id: str, new_priority: int) -> Dict[str, Any]:
    """
    Change the priority of an existing order in the queue.
    
    Args:
        order_id: ID of the order to update
        new_priority: New priority level (1=normal, 2=rush, 3=emergency)
        
    Returns:
        Status of the priority change
    """
    # TODO: Implement this function
    # 1. Validate priority level (1, 2, or 3)
    if new_priority not in [1, 2, 3]:
        return {
            "success": False,
            "message": f"We do not allow a new priority of {new_priority}. Allowed values are only 1, 2 or 3 (1=normal, 2=rush, 3=emergency)."
        }

    # 2. Find the order in factory_state.production_queue
    # 3. Update the order's priority
    order_found = False
    for order in factory_state.production_queue:
        if order.order_id == order_id:
            order_found = True
            order.priority = new_priority
    if not order_found:
        return {
            "success": False,
            "message": f"Sorry, could not find the order with ID {order_id}"
        }

    # 4. Recalculate estimated delivery date based on new priority
    production_capacity = check_production_capacity()
    days_to_complete = production_capacity["days_to_complete_current_queue"]
    if new_priority == 3:
        days_to_complete = 1
    elif new_priority == 2:
        days_to_complete = max(1, days_to_complete / 2)
    estimated_delivery_date = datetime.now() + timedelta(days=days_to_complete)

    # 5. Return success status with new delivery date
    return {
        "success": True,
        "message": f"Succesfully updated the priority of order{order_id} to priority {new_priority}.",
        "delivery_date": estimated_delivery_date.date()
    }

# ======= Agents =======

class OrderProcessorAgent(ToolCallingAgent):
    """Agent responsible for processing customer order requests."""
    
    def __init__(self, model):
        super().__init__(
            tools=[check_pasta_recipe, generate_order_id, list_available_pasta_shapes],
            model=model,
            name="order_processor",
            description="Agent responsible for processing customer orders. Parses requests, identifies pasta shapes and quantities."
        )

class InventoryManagerAgent(ToolCallingAgent):
    """Agent responsible for managing ingredient inventory."""
    
    def __init__(self, model):
        super().__init__(
            tools=[check_inventory, check_pasta_recipe],
            model=model,
            name="inventory_manager",
            description="Agent responsible for tracking and managing ingredient inventory."
        )

class ProductionManagerAgent(ToolCallingAgent):
    """Agent responsible for managing the production queue."""
    
    def __init__(self, model):
        super().__init__(
            tools=[check_production_capacity, add_to_production_queue, prioritize_order],  # TODO: Add add_to_production_queue, prioritize_order
            model=model,
            name="production_manager",
            description="Agent responsible for managing production scheduling and prioritization."
        )

# TODO: Implement the CustomPastaDesignerAgent class
class CustomPastaDesignerAgent(ToolCallingAgent):
    """TODO: Agent responsible for designing custom pasta recipes."""
    
    def __init__(self, model):
        # TODO: Initialize with appropriate tools for custom pasta design
        super().__init__(
            tools=[check_inventory, create_custom_pasta_recipe],  # TODO: Add check_inventory, create_custom_pasta_recipe
            model=model,
            name="pasta_designer",
            description="Agent responsible for creating custom pasta recipes that do not already exist.",
        )

# ======= Orchestrator =======

# TODO: Create proper Orchestrator using ToolCallingAgent pattern
class Orchestrator(ToolCallingAgent):
    """TODO: Orchestrator that coordinates workflow between specialized agents."""
    
    def __init__(self, model):
        self.model = model
        
        # TODO: Initialize specialized agents
        self.order_processor = OrderProcessorAgent(model)
        self.inventory_manager = InventoryManagerAgent(model)
        self.production_manager = ProductionManagerAgent(model)
        self.pasta_designer = CustomPastaDesignerAgent(model)

        # TODO: Create coordination tools that route requests to different agents
        @tool
        def process_order_info(customer_request: str) -> str:
            """Process customer order information to extract details.
            
            Args:
                customer_request: The customer's order request
                
            Returns:
                Processed order information with pasta shape and quantity
            """
            # TODO: Route this request to the OrderProcessorAgent
            return self.order_processor.run(f"""
            The customer says "{customer_request}"

            First, idenfity:
            1. What pasta they want and how much of it they need.
            2. Whether we have that pasta in our set of recipes (list_available_pasta_shapes) and whether we have the inventory for it (check_pasta_recipe)
            3. The urgency of their request which will determine the priority we give the request

            Then, generate an order ID using generate_order_id.
            """)
            

        @tool
        def manage_inventory(order_details: str) -> str:
            """Check and manage inventory for an order.
            
            Args:
                order_details: Details about the order including pasta shape and quantity
                
            Returns:
                Inventory management result
            """
            # TODO: Route this request to the InventoryManagerAgent
            return self.inventory_manager.run(f"""
            The details of the order are: {order_details}.

            You need to identify how much of the ingredients are required by the order (check_pasta_recipe).
            You must determine check whether we can fulfill the order from our factory inventory (check_inventory).
            """)

        @tool
        def schedule_production(order_info: str, priority: int = 1) -> str:
            """Schedule production for an order.
            
            Args:
                order_info: Information about the order to schedule
                priority: Order priority (1=normal, 2=rush, 3=emergency)
                
            Returns:
                Production scheduling result with delivery date
            """
            return self.production_manager.run(f"""
            The customer's order is "{order_info}" and it has priority {priority}.

            You must add the order to the production queue with add_to_production_queue.
            You must also set the priority of the order with prioritize_order
            You should calculate the delivery date estimate using check_production_capacity and the priority of the order:
            """)

        @tool
        def design_custom_pasta(customer_request: str) -> str:
            """Design a custom pasta recipe based on customer requirements.
            
            Args:
                customer_request: Customer's custom pasta request
                
            Returns:
                Custom pasta design result
            """
            return self.pasta_designer.run(f"""
            The customer's request is "{customer_request}" -- this is a custom pasta request.

            You must identify the recipe for the custom pasta shape, the desired quantity and the name of the custom pasta shape.
            Use check_inventory to see if we can fulfill the order.
            Use create_custom_pasta_recipe to add the recipe to our set of recipes.

            If you cannot fulfill the request, be clear why that is the case.
            """)

        super().__init__(
            tools=[process_order_info, manage_inventory, schedule_production, design_custom_pasta],  # TODO: Add the coordination tools
            model=model,
            name="orchestrator",
            description="""
            You are an orchestrator agent for a pasta factory system. 
            You coordinate between the order processor, inventory manager, production manager, and custom pasta designer.
            
            For customer orders, follow this workflow:
            1. First, understand the customer order with process_order_info
            2. If it's a custom pasta shape, use design_custom_pasta
            3. Use manage_inventory to see if we can fulfill the order
            4. Schedule the order and get a delivery date estimate using schedule_production

            Feed the final status and any estimated delivery date to the customer.
            Be clear in your responses to the customer.
            """,
        )
        
    def process_order(self, customer_request: str) -> str:
        """
        Process a customer order through coordinated agent workflow.

        Args:
            customer_request (str): The customer request in natural language

        Returns:
            A response to the customer request
        """
        # TODO: Implement coordinated workflow
        # 1. Check if it's a custom pasta request
        # 2. Determine priority from customer language
        # 3. Use coordination tools to process through appropriate agents
        # 4. Return comprehensive response to customer
        try:
            print("\n--- Processing New Order ---")

            # Use the orchestrator's own coordination workflow
            context = f"""
            Customer request: {customer_request}

            Process this order by coordinating with our specialised agents:
            1. Check if it's a custom pasta request
            2. Determine priority from customer language (rush is next day, urgent is higher priority than normal)
            3. Use coordination tools to process through appropriate agents
            4. Return a direct and clear response to the customer.

            If at any step we cannot fulfill the order, explain why to the customer.
            """

            return self.run(context)
        except Exception as e:
            print(f"Error processing order: {str(e)}")
            print(traceback.format_exc())
            return "I'm sorry, we encountered an error processing your order. Please try again or contact customer service."

# ======= Main Demo =======

def run_demo():
    """Run a demonstration of the pasta factory system."""
    # TODO: Create orchestrator and test the multi-agent coordination
    orchestrator = Orchestrator(model)
    
    print("Welcome to the Pasta Factory Multi-Agent System!")
    print("Initial Factory State:", json.dumps(factory_state.to_dict(), indent=2))
    
    orders = [
        "I'd like to order 2kg of spaghetti please. When can I get it?",
        "I need a custom pasta with extra semolina and no eggs. Can you make that?",
        "Rush order! We need 5kg of fettuccine for a catering event tomorrow!",
    ]
    
    for i, order in enumerate(orders):
        print(f"\n--- Processing Order {i+1} ---")
        print(f"Customer: {order}")
        
        response = orchestrator.process_order(order)
        print(f"Factory: {response}")
        # print("Factory: [TODO: Implement orchestrator.process_order]")
        
    print("\n--- Final Factory State ---")
    print(json.dumps(factory_state.to_dict(), indent=2))
    print("\nDemo complete! This demonstrates multi-agent coordination with shared state management.")

if __name__ == "__main__":
    run_demo()