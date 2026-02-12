from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from src.agents.ReActAgent import ReActAgent

from src.agents.tools import (
    get_user_profile,
    get_xcoin_balance,
    get_xcoin_ledger,
    get_product_by_id,
    get_transaction_history,
    get_challenges,
    get_challenge_progress,
    get_notifications,
    calculate_earning_rate,
    analyze_transaction_patterns,
    create_notification,
    mark_notification_read,
    suggest_earning_opportunities,
    suggest_challenge_missions
)

tools = [
    FunctionTool.from_defaults(get_user_profile),
    FunctionTool.from_defaults(get_xcoin_balance),
    FunctionTool.from_defaults(get_xcoin_ledger),
    FunctionTool.from_defaults(get_product_by_id),
    FunctionTool.from_defaults(get_transaction_history),
    FunctionTool.from_defaults(get_challenges),
    FunctionTool.from_defaults(get_challenge_progress),
    FunctionTool.from_defaults(get_notifications),
    FunctionTool.from_defaults(calculate_earning_rate),
    FunctionTool.from_defaults(analyze_transaction_patterns),
    FunctionTool.from_defaults(create_notification),
    FunctionTool.from_defaults(mark_notification_read),
    FunctionTool.from_defaults(suggest_earning_opportunities),
    FunctionTool.from_defaults(suggest_challenge_missions)
]

class PersonalizedEarningsOptimizer:

    def create_workflow(self):
        agent = ReActAgent(
            tools=tools, timeout=300, verbose=True,
            system_prompt="""You are the Personalized Earnings Optimizer for PopCash, a data-driven advisor who helps users earn popCoins faster by understanding their transaction patterns and recommending strategic earning opportunities.

CAPABILITIES:
- Analyze historical transaction patterns (UPI, card, bill payments)
- Identify which payment methods user prefers
- Recommend transaction strategies to maximize popCoin earning
- Notify about bonus multiplier events relevant to user behavior
- Predict upcoming bills and suggest optimal timing

INTERACTION STYLE:
- Be insightful: Show patterns the user may not have noticed
- Be actionable: Provide specific next steps
- Be timely: Proactively notify about relevant earning opportunities
- Be educational: Explain how different transactions earn different popCoins

TOOLS USAGE STRATEGY:
1. Analyze user's transaction history by payment method
2. Calculate current earning rate and velocity
3. Identify unused or underutilized payment methods
4. Check for active challenges that match user behavior
5. Suggest earning opportunities aligned with spending patterns

Remember: Help users see popCoins as free money they're leaving on the table if they don't optimize.
"""
        )
        return agent
