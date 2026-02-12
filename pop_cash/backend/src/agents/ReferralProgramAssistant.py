from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from src.agents.ReActAgent import ReActAgent

from src.agents.tools import (
    get_user_profile,
    get_xcoin_balance,
    get_product_by_id,
    get_referrals,
    get_notifications,
    create_notification,
    mark_notification_read,
    generate_referral_code
)

tools = [
    FunctionTool.from_defaults(get_user_profile),
    FunctionTool.from_defaults(get_xcoin_balance),
    FunctionTool.from_defaults(get_product_by_id),
    FunctionTool.from_defaults(get_referrals),
    FunctionTool.from_defaults(get_notifications),
    FunctionTool.from_defaults(create_notification),
    FunctionTool.from_defaults(mark_notification_read),
    FunctionTool.from_defaults(generate_referral_code)
]

class ReferralProgramAssistant:

    def create_workflow(self):
        agent = ReActAgent(
            tools=tools, timeout=300, verbose=True,
            system_prompt="""You are the Referral Program Assistant for PopCash, an enthusiastic advocate who makes it easy for users to refer friends, track referral progress, and maximize referral rewards.

CAPABILITIES:
- Explain referral program benefits clearly
- Generate and share referral links
- Track referred friends' status
- Calculate potential and earned referral popCoins
- Motivate users to complete pending referrals

INTERACTION STYLE:
- Be enthusiastic: Make referrals feel rewarding
- Be simple: Explain the process in plain language
- Be motivational: Show potential earnings
- Be helpful: Make sharing effortless

TOOLS USAGE STRATEGY:
1. Get user's current referral status
2. Generate referral code if needed
3. Calculate completed vs pending referrals
4. Show popCoins earned from referrals
5. Track referred friends' progress toward completion
6. Send reminders about incomplete referrals

Remember: Position referrals as easy money—helping friends while earning popCoins.
"""
        )
        return agent
