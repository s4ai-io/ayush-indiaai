# from __future__ import annotations
from llama_index.core.workflow.context import Context
from llama_index.core.tools import FunctionTool
from llama_index.core import Settings
from dotenv import load_dotenv
import os
import uuid
load_dotenv()

from datetime import datetime
import json
from textwrap import dedent
from zoneinfo import ZoneInfo
from fastapi import FastAPI
from llama_index.llms.openai import OpenAI
from src.ag_ui_router import get_ag_ui_workflow_router

Settings.llm = OpenAI(model="gpt-4.1-mini",
    api_key=os.environ.get("OPENAI_API_KEY"),
    max_tokens=5000,
    temperature=0.4,
    parallel_tool_calls=False)

user_id = "U000001"

from src.agents.SmartRedemptionAdvisor import SmartRedemptionAdvisor
from src.agents.PersonalizedEarningsOptimizer import PersonalizedEarningsOptimizer
from src.agents.GoalBasedShoppingAssistant import GoalBasedShoppingAssistant
from src.agents.TransactionTroubleshootingSupport import TransactionTroubleshootingSupport
from src.agents.CatalogDiscoveryTrendInsights import CatalogDiscoveryTrendInsights
from src.agents.BudgetManagerSpendingInsights import BudgetManagerSpendingInsights
from src.agents.ReferralProgramAssistant import ReferralProgramAssistant
from src.agents.CartAbandonmentRecovery import CartAbandonmentRecovery
from src.agents.xCoinExpiryManager import xCoinExpiryManager
from src.agents.GamifiedChallengesMissions import GamifiedChallengesMissions
from src.agents.QuestionNavigationAgent import QuestionNavigationAgent
from fastapi.middleware.cors import CORSMiddleware

async def get_pop_coin_balance(user_query: str, ctx: Context) -> str:
    """
    PopCoin Balance: Retrieve the user's current popCoin balance.
    
    Use this tool when the user wants to:
    - Check their current popCoin balance.
    - Understand how many popCoins they have available.
    - Understand how many are going to expire soon.
    """
    agent = SmartRedemptionAdvisor()
    print("SmartRedemptionAdvisor")
    try:
        user_query = 'Current User ID: U000001 | ' + user_query
        response = await agent.create_workflow().run(input=user_query, parent_ctx=ctx)
        print("SmartRedemptionAdvisor response", response)
        

        return response
    except Exception as e:
        print(f"Error in get_smart_recommendations: {e}")
        return str(e)


async def get_smart_recommendations(user_query: str, ctx: Context) -> str:
    """
    Smart Redemption Advisor: Guide users to maximize their popCoin value.
    
    Use this tool when the user wants to:
    - Find the best deals or optimal cash + popCoin combinations from the catalog.
    - Calculate real-time savings percentages for products.
    - Compare multiple redemption options.
    - Use the tool to retrieve the user's current popCoin balance.
    - Tool already knows how many popCoins the user has.
    - Decide whether to redeem now or accumulate more popCoins.
    - Check for limited-time high-value opportunities.
    """
    agent = SmartRedemptionAdvisor()
    print("SmartRedemptionAdvisor")
    try:
        user_query = f'Current User ID: {user_id} | ' + user_query
        response = await agent.create_workflow().run(input=user_query, parent_ctx=ctx)
        print("SmartRedemptionAdvisor response", response)
        return response
    except Exception as e:
        print(f"Error in get_smart_recommendations: {e}")
        return str(e)

async def get_personalized_earnings_advice(user_query: str, ctx: Context) -> str:
    """
    Personalized Earnings Optimizer: Help users earn popCoins faster.
    
    Use this tool when the user wants to:
    - Analyze transaction patterns to find earning opportunities.
    - Get recommendations on which payment methods (UPI, card, etc.) to use.
    - Learn about bonus popCoin events or multipliers.
    - Optimize spending habits for maximum popCoin accrual.
    """
    try:
        agent = PersonalizedEarningsOptimizer()
        user_query = f'Current User ID: {user_id} | ' + user_query
        response = await agent.create_workflow().run(input=user_query, parent_ctx=ctx)
        return response
    except Exception as e:
        print(f"Error in get_personalized_earnings_advice: {e}")
        return str(e)

async def get_goal_shopping_assistance(user_query: str, ctx: Context) -> str:
    """
    Goal-Based Shopping Assistant: Help users set and achieve product goals.
    
    Use this tool when the user wants to:
    - Set a specific product as a purchase goal.
    - Calculate how many transactions or days are needed to reach a target.
    - Track progress towards a goal.
    - Find alternative products that match their current balance.
    """
    try:
        agent = GoalBasedShoppingAssistant()
        user_query = f'Current User ID: {user_id} | ' + user_query
        response = await agent.create_workflow().run(input=user_query, parent_ctx=ctx)
        return response
    except Exception as e:
        print(f"Error in get_goal_shopping_assistance: {e}")
        return str(e)

async def get_transaction_support(user_query: str, ctx: Context) -> str:
    """
    Transaction Troubleshooting & Support: Resolve payment and popCoin issues.
    
    Use this tool when the user wants to:
    - Report or diagnose payment failures.
    - Investigate missing popCoin credits.
    - Resolve redemption problems.
    - Check the status of a specific transaction.
    """
    try:
        agent = TransactionTroubleshootingSupport()
        user_query = f'Current User ID: {user_id} | ' + user_query
        response = await agent.create_workflow().run(input=user_query, parent_ctx=ctx)
        return response
    except Exception as e:
        print(f"Error in get_transaction_support: {e}")
        return str(e)

async def get_catalog_insights(user_query: str, ctx: Context) -> str:
    """
    Catalog Discovery & Trend Insights: Discover products and trends.
    
    Use this tool ONLY when routed from Question Navigation Agent with specific product search queries.
    
    DO NOT use this tool directly for:
    - "Browse catalog" / "Explore products" → Use get_question_navigation instead
    - "Show me products" → Use get_question_navigation instead
    
    Use this tool when the user has SPECIFIC requests like:
    - "Show me trending products in Electronics"
    - "Compare these two products"
    - "Why is this product trending?"
    - Routed queries from Navigation Agent after catalog navigation completes
    """
    try:
        agent = CatalogDiscoveryTrendInsights()
        user_query = f'Current User ID: {user_id} | ' + user_query
        response = await agent.create_workflow().run(input=user_query, parent_ctx=ctx)
        return response
    except Exception as e:
        print(f"Error in get_catalog_insights: {e}")
        return str(e)

async def get_budget_insights(user_query: str, ctx: Context) -> str:
    """
    Budget Manager & Spending Insights: Track spending and budgets.
    
    Use this tool when the user wants to:
    - Analyze spending patterns by category.
    - Set or monitor monthly budgets.
    - See how popCoins are reducing their actual cash spending.
    - Get insights on where their money is going.
    """
    try:
        agent = BudgetManagerSpendingInsights()
        user_query = f'Current User ID: {user_id} | ' + user_query
        response = await agent.create_workflow().run(input=user_query, parent_ctx=ctx)
        return response
    except Exception as e:
        print(f"Error in get_budget_insights: {e}")
        return str(e)

async def get_referral_assistance(user_query: str, ctx: Context) -> str:
    """
    Referral Program Assistant: Manage referrals and rewards.
    
    Use this tool when the user wants to:
    - Understand referral program benefits.
    - Generate or share referral links.
    - Track the status of referred friends.
    - Check earned referral bonuses.
    """
    try:
        agent = ReferralProgramAssistant()
        user_query = f'Current User ID: {user_id} | ' + user_query
        response = await agent.create_workflow().run(input=user_query, parent_ctx=ctx)
        return response
    except Exception as e:
        print(f"Error in get_referral_assistance: {e}")
        return str(e)

async def get_cart_recovery_assistance(user_query: str, ctx: Context) -> str:
    """
    Cart Abandonment Recovery: Help with abandoned cart items.
    
    Use this tool when the user wants to:
    - Review items left in their shopping cart.
    - See popCoin incentives for completing a purchase.
    - Check if prices or availability have changed for cart items.
    """
    try:
        agent = CartAbandonmentRecovery()
        user_query = f'Current User ID: {user_id} | ' + user_query
        response = await agent.create_workflow().run(input=user_query, parent_ctx=ctx)
        return response
    except Exception as e:
        print(f"Error in get_cart_recovery_assistance: {e}")
        return str(e)

async def get_expiry_management_advice(user_query: str, ctx: Context) -> str:
    """
    popCoin Expiry Manager: Manage expiring popCoins.
    
    Use this tool ONLY when routed from Question Navigation Agent after user selects "Check expiring popCoins".
    
    DO NOT use this tool directly for:
    - "Will my popCoins expire?" → Use get_question_navigation instead
    - "Check my expiring popCoins" → Use get_question_navigation instead
    - "Please fetch my balance and expiry" → Use get_question_navigation instead
    
    Use this tool when:
    - Routed from Navigation Agent with specific expiry intent
    - User has already confirmed they want to focus on expiry management
    """
    try:
        agent = xCoinExpiryManager()
        user_query = f'Current User ID: {user_id} | ' + user_query
        response = await agent.create_workflow().run(input=user_query, parent_ctx=ctx)
        return response
    except Exception as e:
        print(f"Error in get_expiry_management_advice: {e}")
        return str(e)

async def get_gamified_challenges(user_query: str, ctx: Context) -> str:
    """
    Gamified Challenges & Missions: Engage with challenges.
    
    Use this tool when the user wants to:
    - Find available challenges or missions to earn bonus popCoins.
    - Track progress on active challenges.
    - Join new challenges.
    - Make the earning process more fun and game-like.
    """
    try:
        agent = GamifiedChallengesMissions()
        user_query = f'Current User ID: {user_id} | ' + user_query
        response = await agent.create_workflow().run(input=user_query, parent_ctx=ctx)
        return response
    except Exception as e:
        print(f"Error in get_gamified_challenges: {e}")
        return str(e)

async def get_question_navigation(user_query: str, ctx: Context) -> str:
    """
    Question Navigation Agent: Interactive question-based navigation with intent detection.
    
    **CRITICAL: This is the PRIMARY entry point for ALL exploratory and popCoin-related queries.**
    
    ALWAYS use this tool when the user asks about:
    
    POPCOINS & BALANCE QUERIES (Level 0 - Intent Detection):
    - "I have X popCoins, what can I do?"
    - "What should I do with my popCoins?"
    - "Please fetch my popCoins balance"
    - "Check my balance and expiry"
    - "How can I earn more popCoins?"
    - "Will my popCoins expire?"
    - "What can I do with my points?"
    - "Help me use my popCoins"
    
    CATALOG EXPLORATION QUERIES (Level 1-4 - Catalog Navigation):
    - "Explore catalog"
    - "Browse products"
    - "Help me find something"
    - "Show me products"
    - "I want to shop"
    - "Not sure what I want"
    
    This agent will:
    1. For popCoin queries: Show intent options (Spend, Earn, Check Expiry, Goals)
    2. For catalog queries: Navigate through product hierarchy (Ideal For → Category → Brand → Color)
    3. Route to appropriate specialist based on user's selection
    
    DO NOT use other agents directly for these queries - ALWAYS route through this agent first.
    """
    try:
        agent = QuestionNavigationAgent()
        user_query = f'Current User ID: {user_id} | ' + user_query
        response = await agent.create_workflow().run(input=user_query, parent_ctx=ctx)
        return response
    except Exception as e:
        print(f"Error in get_question_navigation: {e}")
        return str(e)


def should_route_to_navigation(query: str) -> bool:
    """
    Deterministic pre-router: Check if query should be routed to Navigation Agent.
    
    This bypasses LLM routing for specific keywords to ensure 100% consistency.
    
    Args:
        query: User's query string
        
    Returns:
        True if query should be routed to Navigation Agent, False otherwise
    """
    query_lower = query.lower()
    
    # Keywords that trigger Navigation Agent (Level 0 - Intent Detection)
    popcoin_keywords = [
        'popcoin', 'pop coin', 'balance', 'points', 'coins',
        'earn', 'earning', 'expir', 'expire', 'expiry',
        'what can i do', 'what should i do', 'help me use',
        'fetch my', 'check my', 'show my balance'
    ]
    
    # Keywords that trigger Navigation Agent (Catalog Exploration)
    catalog_keywords = [
        'explore catalog', 'browse catalog', 'browse product',
        'help me find', 'show me product', 'i want to shop',
        'not sure what', 'help me discover'
    ]
    
    # Check if any keyword matches
    all_keywords = popcoin_keywords + catalog_keywords
    for keyword in all_keywords:
        if keyword in query_lower:
            print(f"[PRE-ROUTER] Matched keyword '{keyword}' - routing to Navigation Agent")
            return True
    
    return False


# Wrapper for Navigation Agent with pre-routing
async def get_question_navigation_with_preroute(user_query: str, ctx: Context) -> str:
    """
    Wrapper that ensures deterministic routing to Navigation Agent.
    This is registered as the actual tool in the router.
    """
    return await get_question_navigation(user_query, ctx)


# Create the router with all 11 agents
agentic_chat_router = get_ag_ui_workflow_router(
    llm=OpenAI(model="gpt-4.1-mini",
    api_key=os.environ.get("OPENAI_API_KEY"),
    max_tokens=5000,
    temperature=0.4,
    parallel_tool_calls=False),
    backend_tools=[
        # FunctionTool.from_defaults(async_fn=get_pop_coin_balance),
        FunctionTool.from_defaults(async_fn=get_smart_recommendations, return_direct=True),
        FunctionTool.from_defaults(async_fn=get_personalized_earnings_advice, return_direct=True),
        FunctionTool.from_defaults(async_fn=get_goal_shopping_assistance, return_direct=True),
        FunctionTool.from_defaults(async_fn=get_transaction_support, return_direct=True),
        FunctionTool.from_defaults(async_fn=get_catalog_insights, return_direct=True),
        FunctionTool.from_defaults(async_fn=get_budget_insights, return_direct=True),
        FunctionTool.from_defaults(async_fn=get_referral_assistance, return_direct=True),
        FunctionTool.from_defaults(async_fn=get_cart_recovery_assistance, return_direct=True),
        FunctionTool.from_defaults(async_fn=get_expiry_management_advice, return_direct=True),
        FunctionTool.from_defaults(async_fn=get_gamified_challenges, return_direct=True),
        FunctionTool.from_defaults(async_fn=get_question_navigation, return_direct=False )
    ],
    system_prompt=dedent(
        """
        You are the PopCash Intelligence Orchestrator, the master AI agent responsible for coordinating 11 specialized agents to provide seamless, intelligent assistance to PopCash users. You are the user's single point of contact, but you leverage specialized expertise behind the scenes.
        
        The current logged in user_id = 'U000001'
        Always pass the current logged in user_id to any tools that you call.

        CORE RESPONSIBILITIES:
        1. Understand user intent from natural language queries
        2. Route conversations to the most appropriate specialized agent(s)
        3. Coordinate multi-agent workflows when user needs span multiple domains
        4. Maintain conversation context across agent handoffs
        5. Ensure smooth, unified user experience despite backend complexity
        6. Decide when to handle simple queries directly vs. delegating to specialists
        7. Each of Tool already knows how many popCoins the user has. You do not need to ask that to the user.

        YOUR SPECIALIZED AGENTS:
        1. Smart Redemption Advisor - Maximizing popCoin redemption value
        2. Personalized Earnings Optimizer - Earning popCoins faster
        3. Goal-Based Shopping Assistant - Setting and achieving product goals
        4. Transaction Troubleshooting & Support - Resolving payment/crediting issues
        5. Catalog Discovery & Trend Insights - Product discovery and recommendations
        6. Budget Manager & Spending Insights - Financial tracking and budgeting
        7. Referral Program Assistant - Managing referrals and rewards
        8. Cart Abandonment Recovery - Completing pending purchases
        9. popCoin Expiry Manager - Preventing popCoin expiration losses
        10. Gamified Challenges & Missions - Engaging with challenges
        11. Question Navigation Agent - Interactive question-based catalog exploration

        ═══════════════════════════════════════════════════════════════════
        ⚠️  MANDATORY PRE-CHECK - MUST BE PERFORMED BEFORE ANY ROUTING ⚠️
        ═══════════════════════════════════════════════════════════════════
        
        BEFORE making ANY routing decision, you MUST check if the user query contains ANY of these keywords:
        
        POPCOIN KEYWORDS (→ Route to Agent 11):
        - "popcoin", "pop coin", "balance", "points", "coins"
        - "earn", "earning", "expir", "expire", "expiry"
        - "what can i do", "what should i do", "help me use"
        - "fetch my", "check my", "show my balance"
        
        CATALOG KEYWORDS (→ Route to Agent 11):
        - "explore catalog", "browse", "help me find"
        - "show me product", "i want to shop", "not sure what"
        
        IF ANY KEYWORD MATCHES → IMMEDIATELY use Agent 11 (Question Navigation)
        IF NO KEYWORD MATCHES → Proceed with normal routing logic below
        
        This pre-check is NON-NEGOTIABLE and MUST be performed first.
        ═══════════════════════════════════════════════════════════════════

        ROUTING DECISION FRAMEWORK:

        PRIORITY ROUTING - Question Navigation Agent (Agent 11):
        Use Agent 11 (Question Navigation) as the PRIMARY handler for:
        - "I have X popCoins, what can I do?" → Agent 11 (shows intent options)
        - "What should I do with my popCoins?" → Agent 11 (shows intent options)
        - "Please fetch my popCoins balance" → Agent 11 (shows balance + intent options)
        - "How can I earn more popCoins?" → Agent 11 (shows intent options including earn)
        - "Will my popCoins expire?" → Agent 11 (shows intent options including expiry)
        - "Check my expiring popCoins" → Agent 11 (shows intent options)
        - "Explore catalog" / "Help me find something" / "Browse products" → Agent 11 (catalog navigation)
        - "Show me products" / "I want to shop" → Agent 11 (catalog navigation)
        
        Agent 11 will then:
        - Show Level 0 intent cards (Spend, Earn, Check Expiry, Goals)
        - Route to appropriate specialist based on user selection
        - OR continue to catalog navigation if user selects "Spend"

        DIRECT ROUTING - Specialized Agents (Only for specific, non-exploratory queries):
        - "What's a good deal right now?" → Agent 1 (Smart Redemption Advisor)
        - "My popCoins weren't credited" → Agent 4 (Transaction Support)
        - "I want to buy that perfume" → Agent 3 (Goal-Based Assistant)
        - "Show me trending products" → Agent 5 (Catalog Discovery)
        - "How much did I spend this month?" → Agent 6 (Budget Manager)
        - "How do I refer a friend?" → Agent 7 (Referral Assistant)
        - "I left items in my cart" → Agent 8 (Cart Recovery)
        - "What challenges can I do?" → Agent 10 (Challenges & Missions)

        MULTI-AGENT ORCHESTRATION SCENARIOS:
        - "I want to buy X but don't have enough popCoins" → Agent 3 (Goal) + Agent 2 (Earnings) + Agent 10 (Challenges)
        - "Should I buy now or wait?" → Agent 1 (Redemption) + Agent 9 (Expiry) + Agent 5 (Trends)
        - "Help me save money this month" → Agent 6 (Budget) + Agent 1 (Redemption) + Agent 2 (Earnings)
        - "I'm close to completing a challenge and want to spend popCoins" → Agent 10 (Challenges) + Agent 1 (Redemption)

        PROACTIVE AGENT ACTIVATION:
        You should proactively invoke agents when:
        - Agent 9: popCoins expiring within 7 days detected
        - Agent 8: Cart items older than 48 hours with price/availability changes
        - Agent 10: User close to completing a challenge (>80% progress)
        - Agent 1: High-value redemption opportunity matches user preferences
        - Agent 6: User approaching budget limit (>85% utilized)
        - Agent 2: Bonus popCoin multiplier event matches user transaction patterns
        - Agent 3: User achieved goal milestone (25%, 50%, 75%, 100%)

        CONVERSATION FLOW MANAGEMENT:

        HANDOFF PROTOCOL:
        1. Acknowledge user's request clearly
        2. Internally route to specialist agent(s)
        3. Present specialist's response naturally (don't say "Agent X says...")
        4. Maintain conversation continuity
        5. Offer related assistance from other specialists when relevant

        CONTEXT PRESERVATION:
        - Track current user_id across all agent interactions
        - Maintain conversation history for context
        - Remember user preferences stated in current session
        - Cache frequently accessed data (popCoin balance, recent transactions)

        RESPONSE SYNTHESIS:
        When coordinating multiple agents:
        1. Gather insights from all relevant specialists
        2. Synthesize into coherent, prioritized recommendations
        3. Present as unified advice, not separate agent outputs
        4. Sequence recommendations logically (quick wins first, then long-term)

        INTERACTION STYLE:
        - Be conversational: Users shouldn't know they're talking to an orchestrator
        - Be proactive: Anticipate needs and offer related assistance
        - Be efficient: Route quickly, don't overthink simple queries
        - Be contextual: Remember what user just said and build on it
        - Be helpful: When uncertain, ask clarifying questions rather than guessing

        ESCALATION RULES:
        - Delegate to Agent 4 (Support) for technical issues beyond your capability
        - Agent 4 escalates to human support with full context when necessary
        - Never fabricate information; admit limitations and offer alternatives

        TOOLS USAGE STRATEGY:
        1. Use lightweight context tools for routing decisions (get_xcoin_balance, get_user_profile)
        2. Delegate heavy analysis to specialized agents
        3. Cache results from agent calls to avoid redundant work
        4. Batch related queries when coordinating multiple agents

        EXAMPLE ORCHESTRATION FLOWS:

        User: "I have XXX popCoins, what should I do with them?"
        → Check expiry (Agent 9) → If expiring soon, recommend redemption (Agent 1)
        → If not urgent, present options: redeem now (Agent 1), save for goal (Agent 3), or see what you can afford (Agent 5)

        User: "Help me buy that ₹2000 headphone"
        → Get popCoin balance → Calculate gap (Agent 3)
        → Suggest earning strategies (Agent 2) + relevant challenges (Agent 10)
        → Show redemption value when goal reached (Agent 1)

        User: "I'm overspending this month"
        → Show budget insights (Agent 6)
        → Suggest using popCoins to reduce cash spending (Agent 1)
        → Recommend earning strategies to offset costs (Agent 2)

        REMEMBER: You are the invisible conductor of a specialist orchestra. Users experience one helpful AI, not a committee. Make agent coordination seamless and natural.

        """
    ),
)
