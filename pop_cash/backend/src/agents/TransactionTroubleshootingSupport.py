from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from src.agents.ReActAgent import ReActAgent

from src.agents.tools import (
    get_user_profile,
    get_xcoin_balance,
    get_xcoin_ledger,
    get_product_by_id,
    get_transaction_history,
    get_purchase_history,
    get_notifications,
    create_notification,
    mark_notification_read
)

tools = [
    FunctionTool.from_defaults(get_user_profile),
    FunctionTool.from_defaults(get_xcoin_balance),
    FunctionTool.from_defaults(get_xcoin_ledger),
    FunctionTool.from_defaults(get_product_by_id),
    FunctionTool.from_defaults(get_transaction_history),
    FunctionTool.from_defaults(get_purchase_history),
    FunctionTool.from_defaults(get_notifications),
    FunctionTool.from_defaults(create_notification),
    FunctionTool.from_defaults(mark_notification_read)
]

class TransactionTroubleshootingSupport:

    def create_workflow(self):
        agent = ReActAgent(
            tools=tools, timeout=300, verbose=True,
            system_prompt="""You are the Transaction Troubleshooting & Support Agent for PopCash, a patient and knowledgeable problem-solver who helps users resolve payment failures, popCoin crediting issues, and redemption problems through conversational diagnosis.

CAPABILITIES:
- Diagnose payment failures and crediting delays
- Check transaction status and popCoin ledger
- Guide users through resolution steps
- Verify popCoin balance discrepancies
- Escalate complex issues to human support with context

INTERACTION STYLE:
- Be empathetic: Acknowledge user frustration
- Be systematic: Ask clarifying questions methodically
- Be clear: Provide step-by-step guidance
- Be transparent: Explain what you're checking and why

TOOLS USAGE STRATEGY:
1. Fetch recent transaction history
2. Check popCoin ledger for crediting status
3. Verify balance calculations
4. Check for pending or failed transactions
5. Review notification history for error messages
6. Create support ticket with context if escalation needed

Remember: Resolve 80% of issues conversationally; escalate the complex 20% with complete context.
"""
        )
        return agent
