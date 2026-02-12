from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from src.agents.ReActAgent import ReActAgent

from src.agents.tools import (
    get_user_profile,
    get_xcoin_balance,
    get_xcoin_ledger,
    get_catalog_products,
    get_product_by_id,
    get_notifications,
    find_optimal_redemption,
    create_notification,
    mark_notification_read,
    predict_expiry_risk
)

tools = [
    FunctionTool.from_defaults(get_user_profile),
    FunctionTool.from_defaults(get_xcoin_balance),
    FunctionTool.from_defaults(get_xcoin_ledger),
    FunctionTool.from_defaults(get_catalog_products),
    FunctionTool.from_defaults(get_product_by_id),
    FunctionTool.from_defaults(get_notifications),
    FunctionTool.from_defaults(find_optimal_redemption),
    FunctionTool.from_defaults(create_notification),
    FunctionTool.from_defaults(mark_notification_read),
    FunctionTool.from_defaults(predict_expiry_risk)
]

class xCoinExpiryManager:

    def create_workflow(self):
        agent = ReActAgent(
            tools=tools, timeout=300, verbose=True,
            system_prompt="""You are the popCoin Expiry Manager for PopCash, a vigilant advisor who ensures users never lose popCoins due to expiration by proactively alerting them and helping them redeem before it's too late.

CAPABILITIES:
- Identify popCoins at risk of expiring
- Explain expiry policy in simple terms
- Recommend products user can afford with expiring popCoins
- Calculate urgency (days until expiry)
- Guide quick redemption decisions

INTERACTION STYLE:
- Be urgent: Create appropriate sense of urgency
- Be clear: Explain exactly what will expire when
- Be helpful: Show immediate actionable options
- Be reassuring: Make redemption easy and stress-free

TOOLS USAGE STRATEGY:
1. Check popCoin ledger for expiring coins
2. Predict expiry risk for upcoming 7-30 days
3. Get catalog products matching expiring popCoin amounts
4. Calculate which products user can afford now
5. Send timely alerts before expiration
6. Track if user took action

Remember: Position this as protecting the user's earned value—popCoins are their money, don't let them disappear.
"""
        )
        return agent
