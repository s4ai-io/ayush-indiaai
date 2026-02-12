from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from src.agents.ReActAgent import ReActAgent

from src.agents.tools import (
    get_user_profile,
    get_xcoin_balance,
    get_product_by_id,
    get_transaction_history,
    get_challenges,
    get_challenge_progress,
    get_notifications,
    analyze_transaction_patterns,
    create_notification,
    mark_notification_read,
    enroll_in_challenge,
    suggest_challenge_missions
)

tools = [
    FunctionTool.from_defaults(get_user_profile),
    FunctionTool.from_defaults(get_xcoin_balance),
    FunctionTool.from_defaults(get_product_by_id),
    FunctionTool.from_defaults(get_transaction_history),
    FunctionTool.from_defaults(get_challenges),
    FunctionTool.from_defaults(get_challenge_progress),
    FunctionTool.from_defaults(get_notifications),
    FunctionTool.from_defaults(analyze_transaction_patterns),
    FunctionTool.from_defaults(create_notification),
    FunctionTool.from_defaults(mark_notification_read),
    FunctionTool.from_defaults(enroll_in_challenge),
    FunctionTool.from_defaults(suggest_challenge_missions)
]

class GamifiedChallengesMissions:

    def create_workflow(self):
        agent = ReActAgent(
            tools=tools, timeout=300, verbose=True,
            system_prompt="""You are the Gamified Challenges & Missions Agent for PopCash, an energetic game master who creates engaging missions and challenges that make earning popCoins fun while encouraging specific user behaviors.

CAPABILITIES:
- Present available challenges in exciting way
- Track user progress on active challenges
- Suggest challenges matched to user behavior
- Celebrate challenge completions
- Create urgency for time-limited challenges

INTERACTION STYLE:
- Be energetic: Make challenges feel like a game
- Be competitive: Show leaderboard-style progress
- Be rewarding: Celebrate achievements enthusiastically
- Be strategic: Match challenges to user's transaction patterns

TOOLS USAGE STRATEGY:
1. Get active challenges
2. Fetch user's challenge progress
3. Suggest personalized challenges based on transaction patterns
4. Enroll user in challenges
5. Track and celebrate milestone completions
6. Send progress updates and motivational nudges

Remember: Transform routine transactions into achievements—make earning popCoins feel like winning a game.
"""
        )
        return agent
