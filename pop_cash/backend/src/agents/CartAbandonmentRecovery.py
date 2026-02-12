from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from src.agents.ReActAgent import ReActAgent

from src.agents.tools import (
    get_user_profile,
    get_xcoin_balance,
    get_catalog_products,
    get_product_by_id,
    get_shopping_cart,
    get_notifications,
    calculate_savings_potential,
    create_notification,
    mark_notification_read,
    remove_from_cart,
    add_to_cart,
    update_cart_quantity,
    detect_cart_abandonment,
    calculate_total_cart_value_with_popcoins
)

tools = [
    FunctionTool.from_defaults(get_user_profile),
    FunctionTool.from_defaults(get_xcoin_balance),
    FunctionTool.from_defaults(get_catalog_products),
    FunctionTool.from_defaults(get_product_by_id),
    FunctionTool.from_defaults(get_shopping_cart),
    FunctionTool.from_defaults(get_notifications),
    FunctionTool.from_defaults(calculate_savings_potential),
    FunctionTool.from_defaults(create_notification),
    FunctionTool.from_defaults(mark_notification_read),
    FunctionTool.from_defaults(remove_from_cart),
    FunctionTool.from_defaults(add_to_cart),
    FunctionTool.from_defaults(update_cart_quantity),
    FunctionTool.from_defaults(detect_cart_abandonment),
    FunctionTool.from_defaults(calculate_total_cart_value_with_popcoins)
]

class CartAbandonmentRecovery:

    def create_workflow(self):
        agent = ReActAgent(
            tools=tools, timeout=300, verbose=True,
            system_prompt="""You are the Cart Abandonment Recovery Agent for PopCash, a persuasive consultant who reminds users about items in their cart and provides compelling reasons to complete their purchase.

CAPABILITIES:
- Identify items left in cart
- Check if cart items' prices or availability changed
- Calculate total savings with popCoins
- Offer incentives to complete purchase
- Remove unavailable items and suggest alternatives

INTERACTION STYLE:
- Be gentle: Remind, don't nag
- Be value-focused: Show savings and benefits
- Be timely: Engage when items might sell out or price changes
- Be helpful: Remove friction to purchase

TOOLS USAGE STRATEGY:
1. Get shopping cart contents
2. Check product availability and current pricing
3. Calculate savings potential with user's popCoins
4. Detect if prices changed since adding to cart
5. Suggest completing purchase if great value
6. Offer alternatives if items unavailable

Remember: Help users see completing the purchase as smart decision-making, not impulse buying.
"""
        )
        return agent
