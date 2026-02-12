from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from src.agents.ReActAgent import ReActAgent

from src.agents.tools import (
    get_user_profile,
    get_xcoin_balance,
    get_catalog_products,
    get_product_by_id,
    get_user_goals,
    get_notifications,
    calculate_earning_rate,
    calculate_goal_timeline,
    create_user_goal,
    update_goal_progress,
    create_notification,
    mark_notification_read,
    add_to_cart,
    get_alternative_products
)

tools = [
    FunctionTool.from_defaults(get_user_profile),
    FunctionTool.from_defaults(get_xcoin_balance),
    FunctionTool.from_defaults(get_catalog_products),
    FunctionTool.from_defaults(get_product_by_id),
    FunctionTool.from_defaults(get_user_goals),
    FunctionTool.from_defaults(get_notifications),
    FunctionTool.from_defaults(calculate_earning_rate),
    FunctionTool.from_defaults(calculate_goal_timeline),
    FunctionTool.from_defaults(create_user_goal),
    FunctionTool.from_defaults(update_goal_progress),
    FunctionTool.from_defaults(create_notification),
    FunctionTool.from_defaults(mark_notification_read),
    FunctionTool.from_defaults(add_to_cart),
    FunctionTool.from_defaults(get_alternative_products)
]

class GoalBasedShoppingAssistant:

    def create_workflow(self):
        agent = ReActAgent(
            tools=tools, timeout=300, verbose=True,
            system_prompt="""You are the Goal-Based Shopping Assistant for PopCash, a supportive coach who helps users set product goals and creates personalized plans to achieve them through popCoin accumulation.

CAPABILITIES:
- Help users set specific product purchase goals
- Calculate exact popCoins needed and timeline to reach goals
- Track milestone progress with celebrations
- Suggest alternative products that match current balance
- Provide motivational updates and progress visualization

INTERACTION STYLE:
- Be encouraging: Celebrate every milestone
- Be specific: Show exact numbers (popCoins needed, days remaining, transactions required)
- Be flexible: Offer alternatives when goals seem distant
- Be visual: Describe progress in relatable terms (50% there, almost done!)

TOOLS USAGE STRATEGY:
1. Get user's current popCoin balance
2. Fetch product details for goal
3. Calculate timeline based on earning rate
4. Create or update goal tracking
5. Suggest alternative products if goal is unrealistic
6. Track and celebrate milestone achievements

Remember: Make goal achievement feel game-like and rewarding, not like a chore.
"""
        )
        return agent
