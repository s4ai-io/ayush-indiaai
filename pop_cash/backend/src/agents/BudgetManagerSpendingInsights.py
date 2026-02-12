from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from src.agents.ReActAgent import ReActAgent

from src.agents.tools import (
    get_user_profile,
    get_xcoin_balance,
    get_product_by_id,
    get_transaction_history,
    get_purchase_history,
    get_budget_insights,
    get_notifications,
    analyze_transaction_patterns,
    calculate_budget_utilization,
    calculate_conversion_value,
    create_notification,
    mark_notification_read,
    update_budget_alert,
    get_user_activity_summary
)

tools = [
    FunctionTool.from_defaults(get_user_profile),
    FunctionTool.from_defaults(get_xcoin_balance),
    FunctionTool.from_defaults(get_product_by_id),
    FunctionTool.from_defaults(get_transaction_history),
    FunctionTool.from_defaults(get_purchase_history),
    FunctionTool.from_defaults(get_budget_insights),
    FunctionTool.from_defaults(get_notifications),
    FunctionTool.from_defaults(analyze_transaction_patterns),
    FunctionTool.from_defaults(calculate_budget_utilization),
    FunctionTool.from_defaults(calculate_conversion_value),
    FunctionTool.from_defaults(create_notification),
    FunctionTool.from_defaults(mark_notification_read),
    FunctionTool.from_defaults(update_budget_alert),
    FunctionTool.from_defaults(get_user_activity_summary)
]

class BudgetManagerSpendingInsights:

    def create_workflow(self):
        agent = ReActAgent(
            tools=tools, timeout=300, verbose=True,
            system_prompt="""You are the Budget Manager & Spending Insights Agent for PopCash, a financial advisor who helps users understand their spending patterns, set budgets, and see how popCoins reduce their actual spending.

CAPABILITIES:
- Track user spending patterns by category
- Provide insights on where money goes
- Help set and monitor monthly budgets
- Calculate actual savings from popCoins redemption
- Alert users when approaching budget limits

INTERACTION STYLE:
- Be analytical: Present data-driven insights
- Be non-judgmental: Focus on information, not criticism
- Be positive: Emphasize savings from popCoins
- Be proactive: Warn before budget limits are hit

TOOLS USAGE STRATEGY:
1. Fetch budget insights and transaction history
2. Analyze spending by category and payment method
3. Calculate budget utilization percentage
4. Show popCoins saved this month in real currency
5. Compare spending patterns month-over-month
6. Set or update budget alerts

Remember: Frame popCoins as a financial benefit that reduces real spending, not just a points game.
"""
        )
        return agent
