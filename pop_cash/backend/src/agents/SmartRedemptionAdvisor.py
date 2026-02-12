from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from src.agents.ReActAgent import ReActAgent

from src.agents.tools import (
    get_user_profile,
    get_xcoin_balance,
    get_xcoin_ledger,
    get_catalog_products,
    get_product_by_id,
    get_browsing_history,
    get_shopping_cart,
    get_user_goals,
    get_product_recommendations,
    get_product_trends,
    get_notifications,
    calculate_savings_potential,
    find_optimal_redemption,
    calculate_conversion_value,
    create_notification,
    mark_notification_read,
    add_to_cart,
    rank_products_by_value,
    calculate_total_cart_value_with_popcoins
)

tools = [
    FunctionTool.from_defaults(get_user_profile),
    FunctionTool.from_defaults(get_xcoin_balance),
    FunctionTool.from_defaults(get_xcoin_ledger),
    FunctionTool.from_defaults(get_catalog_products),
    FunctionTool.from_defaults(get_product_by_id),
    FunctionTool.from_defaults(get_browsing_history),
    FunctionTool.from_defaults(get_shopping_cart),
    FunctionTool.from_defaults(get_user_goals),
    FunctionTool.from_defaults(get_product_recommendations),
    FunctionTool.from_defaults(get_product_trends),
    FunctionTool.from_defaults(get_notifications),
    # FunctionTool.from_defaults(calculate_savings_potential),
    FunctionTool.from_defaults(find_optimal_redemption),
    FunctionTool.from_defaults(calculate_conversion_value),
    FunctionTool.from_defaults(create_notification),
    FunctionTool.from_defaults(mark_notification_read),
    FunctionTool.from_defaults(add_to_cart),
    FunctionTool.from_defaults(rank_products_by_value),
    FunctionTool.from_defaults(calculate_total_cart_value_with_popcoins)
]

class SmartRedemptionAdvisor:

    def create_workflow(self):
        sma_agent = ReActAgent(
            tools=tools, timeout=300, verbose=True,
            system_prompt="""You are the Smart Redemption Advisor for PopCash, an expert at maximizing popCoin value for users. Your role is to analyze the user's current popCoin balance, catalog availability, and redemption opportunities to guide optimal spending decisions.

CAPABILITIES:
- Analyze catalog products to find best cash+popCoin deals
- Calculate real-time savings percentages for any product
- Alert users about limited-time high-value opportunities
- Compare multiple redemption options
- Recommend whether to redeem now or accumulate more popCoins
- Your Final Answer should be a short summary enticing the user to buy. The output of recommendations, if given by your tools, will be rendered in UI and you need not repeat it in your final answer.

INTERACTION STYLE:
- Be proactive: Initiate conversations when great deals appear
- Be quantitative: Always show exact savings amounts and percentages
- Be comparative: Show multiple options with clear trade-offs
- Be strategic: Consider user's earning rate and product availability

TOOLS USAGE STRATEGY:
1. Always start by checking current popCoin balance
2. Fetch catalog products matching user preferences
3. Calculate savings potential for top candidates
4. Find optimal cash+popCoin combinations
5. Rank products by value efficiency

Remember: Your goal is to help users feel they're getting exceptional value from their popCoins.
"""
        )
        return sma_agent
