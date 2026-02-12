from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from src.agents.ReActAgent import ReActAgent

from src.agents.tools import (
    get_user_profile,
    get_xcoin_balance,
    get_catalog_products,
    get_product_by_id,
    get_browsing_history,
    get_purchase_history,
    get_product_recommendations,
    get_product_trends,
    get_notifications,
    create_notification,
    mark_notification_read,
    add_to_cart,
    get_alternative_products,
    rank_products_by_value
)

tools = [
    FunctionTool.from_defaults(get_user_profile),
    FunctionTool.from_defaults(get_xcoin_balance),
    FunctionTool.from_defaults(get_catalog_products),
    FunctionTool.from_defaults(get_product_by_id),
    FunctionTool.from_defaults(get_browsing_history),
    FunctionTool.from_defaults(get_purchase_history),
    FunctionTool.from_defaults(get_product_recommendations),
    # FunctionTool.from_defaults(get_product_trends),
    FunctionTool.from_defaults(get_notifications),
    FunctionTool.from_defaults(create_notification),
    FunctionTool.from_defaults(mark_notification_read),
    FunctionTool.from_defaults(add_to_cart),
    FunctionTool.from_defaults(get_alternative_products),
    FunctionTool.from_defaults(rank_products_by_value)
]

class CatalogDiscoveryTrendInsights:

    def create_workflow(self):
        agent = ReActAgent(
            tools=tools, timeout=300, verbose=True,
            system_prompt="""You are the Catalog Discovery & Trend Insights Agent for PopCash, a knowledgeable curator who helps users discover relevant products from the curated catalog based on their preferences, trends, and popCoin balance.

CAPABILITIES:

- Optimize product discovery for current popCoin balance



TOOLS USAGE STRATEGY:
1. Get products based on user's question
2. Strictly answer using the tools provided

Remember: Act like a personal shopper who helps find relevant products and deals.
"""
        )
        return agent
