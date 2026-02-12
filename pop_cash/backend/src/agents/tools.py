
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from src.agents.crud_helper import (
    UserProfileHandler, BrowsingHistoryHandler, CatalogHandler,
    ChallengeHandler, NotificationHandler, ProductRecommendationHandler,
    ProductTrendHandler, PurchaseHistoryHandler, ReferralHandler,
    ShoppingCartHandler, TransactionHandler, BudgetInsightsHandler,
    ChallengeProgressHandler, UserGoalHandler, PopCoinBalanceHandler,
    PopCoinLedgerHandler
)
from src.agents.models import (
    UserProfile, BrowsingHistory, CatalogProduct, Challenge, Notification,
    ProductRecommendation, ProductTrend, PurchaseHistory, ReferralTracking,
    ShoppingCart, TransactionHistory, UserBudgetInsights, UserChallengeProgress,
    UserGoal, UserPopCoinBalance, PopCoinLedger
)
import json
from decimal import Decimal


# ============================================================================
# CORE DATA RETRIEVAL TOOLS (17 tools)
# ============================================================================

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve complete user profile information.
    
    Use this tool when you need to understand user demographics, preferences,
    account status, or contact information for personalization.
    
    Args:
        user_id: Unique identifier for the user (e.g., "U000001")
    
    Returns:
        Dictionary containing user profile data with fields:
        - user_id: User identifier
        - name: Full name
        - email: Email address
        - age: User age
        - gender: Gender
        - location: City/location
        - registration_date: Account creation date
        - preferred_categories: List of preferred product categories (stored as string)
        - account_status: "Active", "Inactive", "Suspended"
        - phone_number: Contact number
        
        Returns None if user not found.
    
    Example:
        profile = get_user_profile("U000001")
        # Returns: {"user_id": "U000001", "name": "John Doe", "email": "john@example.com", ...}
    """
    try:
        handler = UserProfileHandler()
        profile = handler.read_by_id(user_id)
        return profile.model_dump() if profile else None
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return None


def get_xcoin_balance(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user's current popCoin balance and statistics.
    
    Use this tool to check how many popCoins a user has available, their earning
    history, and coins at risk of expiring soon.
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        Dictionary containing popCoin balance information:
        - user_id: User identifier
        - total_popcoins_earned: Lifetime popCoins earned
        - total_popcoins_spent: Lifetime popCoins redeemed
        - current_balance: Available popCoins now
        - popcoins_expiring_soon: popCoins expiring within 30 days
        - last_earned_date: Most recent popCoin earning timestamp
        - last_updated: Last balance update timestamp
        
        Returns None if user not found.
    
    Example:
        balance = get_xcoin_balance("U000001")
        # Returns: {"current_balance": 536, "popcoins_expiring_soon": 88, ...}
    """
    try:
        handler = PopCoinBalanceHandler()
        balance = handler.read_by_id(user_id)
        return balance.model_dump() if balance else None
    except Exception as e:
        print(f"Error fetching popCoin balance: {e}")
        return None


def get_xcoin_ledger(user_id: str, limit: int = 50, active_only: bool = False) -> List[Dict[str, Any]]:
    """
    Retrieve detailed popCoin transaction ledger for a user.
    
    Use this tool to see the complete history of popCoin earnings and spendings,
    including expiry dates and current status of each popCoin batch.
    
    Args:
        user_id: Unique identifier for the user
        limit: Maximum number of ledger entries to return (default: 50)
        active_only: If True, return only active (not spent/expired) popCoins
    
    Returns:
        List of ledger entries, each containing:
        - ledger_id: Unique ledger entry identifier
        - user_id: User identifier
        - transaction_id: Associated transaction ID
        - popcoins_earned: popCoins earned in this transaction
        - popcoins_spent: popCoins spent from this batch
        - popcoins_balance: Remaining popCoins in this batch
        - earned_date: When popCoins were earned
        - expiry_date: When popCoins expire
        - spent_date: When popCoins were spent (if applicable)
        - is_expired: Whether popCoins have expired
        - status: "Active", "Spent", "Expired"
    
    Example:
        ledger = get_xcoin_ledger("U000001", limit=10, active_only=True)
        # Returns: [{"ledger_id": "LED00000001", "popcoins_balance": 29, ...}, ...]
    """
    try:
        handler = PopCoinLedgerHandler()
        ledger = handler.get_user_ledger(user_id)
        
        if active_only:
            ledger = [entry for entry in ledger if entry.status == "Active" and not entry.is_expired]
        
        return [entry.model_dump() for entry in ledger[:limit]]
    except Exception as e:
        print(f"Error fetching popCoin ledger: {e}")
        return []


def get_catalog_products(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    ideal_for: Optional[str] = None,
    color: Optional[str] = None,
    search_term: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    max_xcoin_required: Optional[int] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Search and filter products from the curated catalog.
    
    Use this tool to find products matching specific criteria like category,
    brand, ideal_for, color, price range, or popCoin requirements.
    
    Args:
        category: Filter by category name (e.g., "Fashion", "Electronics")
        brand: Filter by brand name (e.g., "Nike", "Samsung")
        ideal_for: Filter by target audience (e.g., "Men", "Women")
        color: Filter by product color
        search_term: Search in product titles (case-insensitive)
        min_price: Minimum selling price filter
        max_price: Maximum selling price filter
        max_xcoin_required: Maximum popCoins required for redemption
        limit: Maximum number of products to return (default: 20)
    
    Returns:
        List of product dictionaries, each containing:
        - id: Product unique identifier
        - title: Product name/title
        - category_name: Product category
        - brand_name: Product brand
        - sp: Selling price (with popCoins)
        - mrp: Maximum retail price
        - coins_earn: popCoins earned on purchase
        - coins_burn: popCoins required for redemption
        - (and 60+ other product attributes)
    
    Example:
        products = get_catalog_products(category="Fashion", max_price=1000, limit=5)
        # Returns: [{"id": 123, "title": "Cotton T-Shirt", "sp": 499, ...}, ...]
    """
    try:
        from difflib import get_close_matches
        
        handler = CatalogHandler()
        products = handler.read_all()
        
        # Apply ideal_for filter
        if ideal_for:
            products = [p for p in products if p.ideal_for and p.ideal_for.lower() == ideal_for.lower()]

        # Apply fuzzy category filter
        if category and products:
            import re
            from difflib import SequenceMatcher
            
            # Get all unique categories from products
            all_categories = list(set([p.category_name for p in products if p.category_name]))
            
            # Try exact match first (case-insensitive)
            category_lower = category.lower()
            exact_match = next((cat for cat in all_categories if cat.lower() == category_lower), None)
            
            if exact_match:
                # Use exact match if found
                products = [p for p in products if p.category_name == exact_match]
            else:
                # Score all categories and pick the best match
                category_scores = []
                
                for cat in all_categories:
                    cat_lower = cat.lower()
                    
                    # Calculate similarity score using SequenceMatcher
                    similarity = SequenceMatcher(None, category_lower, cat_lower).ratio()
                    
                    # Boost score for word-boundary matches (e.g., "inner wear" vs "innerwears")
                    # Remove spaces and special chars for comparison
                    cat_normalized = re.sub(r'[^a-z0-9]', '', cat_lower)
                    category_normalized = re.sub(r'[^a-z0-9]', '', category_lower)
                    
                    if category_normalized in cat_normalized or cat_normalized in category_normalized:
                        # Check if it's a meaningful match (not just a small substring)
                        overlap_ratio = len(category_normalized) / len(cat_normalized)
                        if overlap_ratio > 0.5:  # At least 50% overlap
                            similarity = max(similarity, 0.8)  # Boost score
                    
                    # Only consider matches above threshold
                    if similarity >= 0.6:
                        category_scores.append((cat, similarity))
                
                # Sort by score descending
                category_scores.sort(key=lambda x: x[1], reverse=True)
                
                if category_scores:
                    # Use the best match
                    matched_category = category_scores[0][0]
                    products = [p for p in products if p.category_name == matched_category]
                    print(f"Category match: '{category}' -> '{matched_category}' (score: {category_scores[0][1]:.2f})")
                else:
                    # No match found, return empty
                    print(f"No category match found for: '{category}'")
                    products = []
        
        # Apply fuzzy brand filter
        if brand and products:  # Only if we still have products
            import re
            from difflib import SequenceMatcher
            
            # Get all unique brands from remaining products
            all_brands = list(set([p.brand_name for p in products if p.brand_name]))
            
            # Try exact match first (case-insensitive)
            brand_lower = brand.lower()
            exact_match = next((b for b in all_brands if b.lower() == brand_lower), None)
            
            if exact_match:
                # Use exact match if found
                products = [p for p in products if p.brand_name == exact_match]
            else:
                # Score all brands and pick the best match
                brand_scores = []
                
                for b in all_brands:
                    b_lower = b.lower()
                    
                    # Calculate similarity score
                    similarity = SequenceMatcher(None, brand_lower, b_lower).ratio()
                    
                    # Boost score for normalized matches
                    brand_normalized = re.sub(r'[^a-z0-9]', '', b_lower)
                    search_normalized = re.sub(r'[^a-z0-9]', '', brand_lower)
                    
                    if search_normalized in brand_normalized or brand_normalized in search_normalized:
                        overlap_ratio = len(search_normalized) / len(brand_normalized)
                        if overlap_ratio > 0.5:
                            similarity = max(similarity, 0.8)
                    
                    if similarity >= 0.6:
                        brand_scores.append((b, similarity))
                
                # Sort by score descending
                brand_scores.sort(key=lambda x: x[1], reverse=True)
                
                if brand_scores:
                    matched_brand = brand_scores[0][0]
                    products = [p for p in products if p.brand_name == matched_brand]
                    print(f"Brand match: '{brand}' -> '{matched_brand}' (score: {brand_scores[0][1]:.2f})")
                else:
                    print(f"No brand match found for: '{brand}'")
                    products = []
        
        # Apply color filter
        if color and products:
            products = [p for p in products if p.color and p.color.lower() == color.lower()]

        # Apply search term filter (already works with partial matching)
        if search_term and len(products) == 0:
            search_lower = search_term.lower()
            products = [p for p in products if search_lower in p.title.lower() or (p.category_name and search_lower in p.category_name.lower()) or (p.brand_name and search_lower in p.brand_name.lower())]
        
        # Apply price filters
        if min_price is not None and products:
            products = [p for p in products if p.sp and p.sp >= min_price]
        
        if max_price is not None and products:
            products = [p for p in products if p.sp and p.sp <= max_price]
        
        # Apply popCoin filter
        if max_xcoin_required is not None and products:
            products = [p for p in products if p.coins_burn and p.coins_burn <= max_xcoin_required]
        
        return [p.model_dump() for p in products[:limit]]
    except Exception as e:
        print(f"Error fetching catalog products: {e}")
        return []


def get_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve complete details for a specific product.
    
    Use this tool when you need full information about a particular product
    identified by its ID.
    
    Args:
        product_id: Unique product identifier
    
    Returns:
        Dictionary with complete product information including:
        - All catalog fields (title, price, brand, category, etc.)
        - Product specifications and attributes
        - Returns None if product not found
    
    Example:
        product = get_product_by_id(41030)
        # Returns: {"id": 41030, "title": "Roasted Pistachio", "sp": 347.0, ...}
    """
    try:
        handler = CatalogHandler()
        product = handler.read_by_id(product_id)
        return product.model_dump() if product else None
    except Exception as e:
        print(f"Error fetching product: {e}")
        return None


def get_transaction_history(
    user_id: str,
    transaction_type: Optional[str] = None,
    payment_method: Optional[str] = None,
    status: Optional[str] = None,
    days: Optional[int] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Retrieve user's transaction history with optional filters.
    
    Use this tool to analyze user's payment patterns, transaction success rates,
    and popCoin earning history.
    
    Args:
        user_id: Unique identifier for the user
        transaction_type: Filter by type ("Purchase", "Bill Payment", "UPI", etc.)
        payment_method: Filter by method ("UPI", "Credit Card", "Debit Card", etc.)
        status: Filter by status ("Success", "Failed", "Pending")
        days: Only return transactions from last N days
        limit: Maximum number of transactions to return (default: 50)
    
    Returns:
        List of transaction dictionaries, each containing:
        - transaction_id: Unique transaction identifier
        - user_id: User identifier
        - transaction_type: Type of transaction
        - amount: Transaction amount in rupees
        - transaction_date: When transaction occurred
        - payment_method: Payment method used
        - status: Transaction status
        - popcoins_earned: popCoins earned from this transaction
        - vendor_name: Merchant/vendor name
        - category: Transaction category
    
    Example:
        txns = get_transaction_history("U000001", payment_method="UPI", days=30)
        # Returns: [{"transaction_id": "TXN001", "amount": 1450.75, ...}, ...]
    """
    try:
        handler = TransactionHandler()
        transactions = handler.get_user_transactions(user_id)
        
        # Apply filters
        if transaction_type:
            transactions = [t for t in transactions if t.transaction_type == transaction_type]
        
        if payment_method:
            transactions = [t for t in transactions if t.payment_method == payment_method]
        
        if status:
            transactions = [t for t in transactions if t.status == status]
        
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            transactions = [t for t in transactions if t.transaction_date >= cutoff]
        
        return [t.model_dump() for t in transactions[:limit]]
    except Exception as e:
        print(f"Error fetching transaction history: {e}")
        return []


def get_purchase_history(user_id: str, order_status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieve user's purchase order history from PopCash catalog.
    
    Use this tool to see what products the user has bought, delivery status,
    and popCoins used in purchases.
    
    Args:
        user_id: Unique identifier for the user
        order_status: Filter by status ("Delivered", "Shipped", "Processing", "Cancelled")
        limit: Maximum number of orders to return (default: 20)
    
    Returns:
        List of order dictionaries, each containing:
        - order_id: Unique order identifier
        - user_id: User identifier
        - order_date: When order was placed
        - num_items: Number of items in order
        - total_amount: Total order amount in rupees
        - popcoins_used: popCoins redeemed in this order
        - payment_method: Payment method used
        - order_status: Current order status
        - delivery_date: Expected/actual delivery date
        - items: JSON string with item details
    
    Example:
        orders = get_purchase_history("U000001", order_status="Delivered")
        # Returns: [{"order_id": "ORD001", "total_amount": 1299.50, ...}, ...]
    """
    try:
        handler = PurchaseHistoryHandler()
        orders = handler.get_user_orders(user_id)
        
        if order_status:
            orders = [o for o in orders if o.order_status == order_status]
        
        return [o.model_dump() for o in orders[:limit]]
    except Exception as e:
        print(f"Error fetching purchase history: {e}")
        return []


def get_browsing_history(user_id: str, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve user's product browsing history.
    
    Use this tool to understand user's interests, preferences, and shopping
    patterns based on what they've viewed.
    
    Args:
        user_id: Unique identifier for the user
        days: Only return browsing from last N days (default: 7)
        limit: Maximum number of browsing records to return (default: 50)
    
    Returns:
        List of browsing records, each containing:
        - browse_id: Unique browsing record identifier
        - user_id: User identifier
        - product_id: Product that was viewed
        - category: Product category
        - brand: Product brand
        - view_timestamp: When product was viewed
        - time_spent_seconds: Time spent viewing
        - added_to_cart: Whether product was added to cart
        - source: How user found product ("Search", "Recommendation", etc.)
    
    Example:
        history = get_browsing_history("U000001", days=7)
        # Returns: [{"browse_id": "BRW001", "product_id": 41030, ...}, ...]
    """
    try:
        handler = BrowsingHistoryHandler()
        history = handler.get_recently_viewed(user_id, days=days)
        return [h.model_dump() for h in history[:limit]]
    except Exception as e:
        print(f"Error fetching browsing history: {e}")
        return []


def get_shopping_cart(user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all items currently in user's shopping cart.
    
    Use this tool to see what products the user is considering purchasing,
    including pricing and popCoin requirements.
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        List of cart item dictionaries, each containing:
        - cart_id: Unique cart item identifier
        - user_id: User identifier
        - product_id: Product in cart
        - title: Product title
        - category: Product category
        - brand: Product brand
        - quantity: Quantity in cart
        - price: Current selling price
        - mrp: Maximum retail price
        - popcoins_required: popCoins needed for redemption
        - added_at: When item was added to cart
        - is_available: Whether product is still in stock
        - price_changed: Whether price changed since adding
    
    Example:
        cart = get_shopping_cart("U000001")
        # Returns: [{"cart_id": "CART001", "title": "Pistachio", "quantity": 2, ...}, ...]
    """
    try:
        handler = ShoppingCartHandler()
        cart_items = handler.get_user_cart(user_id)
        return [item.model_dump() for item in cart_items]
    except Exception as e:
        print(f"Error fetching shopping cart: {e}")
        return []


def get_user_goals(user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve user's product purchase goals.
    
    Use this tool to see what products the user is saving popCoins for,
    their progress, and timeline to achievement.
    
    Args:
        user_id: Unique identifier for the user
        status: Filter by goal status ("Active", "Completed", "Abandoned")
    
    Returns:
        List of goal dictionaries, each containing:
        - goal_id: Unique goal identifier
        - user_id: User identifier
        - product_id: Target product
        - product_title: Product name
        - target_popcoins: popCoins needed for goal
        - current_popcoins: User's current popCoin balance
        - popcoins_needed: Remaining popCoins to reach goal
        - target_price: Product price
        - estimated_days: Days to reach goal based on earning rate
        - created_at: When goal was created
        - target_date: Expected achievement date
        - status: Goal status
        - notification_enabled: Whether user wants progress updates
    
    Example:
        goals = get_user_goals("U000001", status="Active")
        # Returns: [{"goal_id": "GOAL001", "product_title": "Headphones", ...}, ...]
    """
    try:
        handler = UserGoalHandler()
        if status:
            goals = handler.search(lambda g: g.user_id == user_id and g.status == status)
        else:
            goals = handler.get_user_goals(user_id)
        
        return [g.model_dump() for g in goals]
    except Exception as e:
        print(f"Error fetching user goals: {e}")
        return []


def get_challenges(active_only: bool = True, difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve available challenges/missions for users.
    
    Use this tool to show users available challenges they can complete
    to earn bonus popCoins.
    
    Args:
        active_only: If True, return only currently active challenges (default: True)
        difficulty: Filter by difficulty ("Easy", "Medium", "Hard")
    
    Returns:
        List of challenge dictionaries, each containing:
        - challenge_id: Unique challenge identifier
        - challenge_name: Challenge name
        - description: What user needs to do
        - challenge_type: Type ("Transaction Count", "Spending Amount", etc.)
        - target_value: Goal to achieve (e.g., 3 transactions, ₹5000 spent)
        - reward_popcoins: popCoins earned upon completion
        - duration_days: Challenge duration in days
        - start_date: Challenge start date
        - end_date: Challenge end date
        - is_active: Whether challenge is currently active
        - difficulty: Challenge difficulty level
    
    Example:
        challenges = get_challenges(active_only=True, difficulty="Easy")
        # Returns: [{"challenge_id": "CH001", "challenge_name": "Weekend Warrior", ...}, ...]
    """
    try:
        handler = ChallengeHandler()
        
        if active_only:
            challenges = handler.get_active_challenges()
        else:
            challenges = handler.read_all()
        
        if difficulty:
            challenges = [c for c in challenges if c.difficulty == difficulty]
        
        return [c.model_dump() for c in challenges]
    except Exception as e:
        print(f"Error fetching challenges: {e}")
        return []


def get_challenge_progress(user_id: str, include_completed: bool = False) -> List[Dict[str, Any]]:
    """
    Retrieve user's progress on enrolled challenges.
    
    Use this tool to see which challenges the user is working on and
    how close they are to completion.
    
    Args:
        user_id: Unique identifier for the user
        include_completed: If True, include completed challenges (default: False)
    
    Returns:
        List of challenge progress dictionaries, each containing:
        - progress_id: Unique progress record identifier
        - user_id: User identifier
        - challenge_id: Associated challenge
        - challenge_name: Challenge name
        - current_progress: Current progress value
        - target_value: Target to achieve
        - progress_percentage: Completion percentage
        - is_completed: Whether challenge is completed
        - popcoins_earned: popCoins earned (if completed)
        - started_at: When user started challenge
        - completed_at: When challenge was completed (if applicable)
        - last_updated: Last progress update timestamp
    
    Example:
        progress = get_challenge_progress("U000001")
        # Returns: [{"progress_id": "PROG001", "progress_percentage": 67.5, ...}, ...]
    """
    try:
        handler = ChallengeProgressHandler()
        progress = handler.get_user_progress(user_id)
        
        if not include_completed:
            progress = [p for p in progress if not p.is_completed]
        
        return [p.model_dump() for p in progress]
    except Exception as e:
        print(f"Error fetching challenge progress: {e}")
        return []


def get_product_recommendations(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve personalized product recommendations for a user.
    
    Use this tool to suggest products the user might like based on their
    browsing history, preferences, and behavior.
    
    Args:
        user_id: Unique identifier for the user
        limit: Maximum number of recommendations to return (default: 10)
    
    Returns:
        List of recommendation dictionaries, each containing:
        - recommendation_id: Unique recommendation identifier
        - user_id: User identifier
        - product_id: Recommended product
        - product_title: Product name
        - category: Product category
        - brand: Product brand
        - recommendation_score: Confidence score (0-1)
        - recommendation_reason: Why product is recommended
        - recommended_at: When recommendation was generated
        - clicked: Whether user clicked on recommendation
        - purchased: Whether user purchased recommended product
    
    Example:
        recs = get_product_recommendations("U000001", limit=5)
        # Returns: [{"product_id": 123, "recommendation_score": 0.92, ...}, ...]
    """
    try:
        handler = ProductRecommendationHandler()
        recommendations = handler.get_user_recommendations(user_id, limit=limit)
        return [r.model_dump() for r in recommendations]
    except Exception as e:
        print(f"Error fetching recommendations: {e}")
        return []


def get_product_trends(category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieve trending products based on views, purchases, and ratings.
    
    Use this tool to show users what's popular right now in the catalog.
    
    Args:
        category: Filter trends by category (optional)
        limit: Maximum number of trending products to return (default: 20)
    
    Returns:
        List of product trend dictionaries, each containing:
        - product_id: Product identifier
        - product_title: Product name
        - category: Product category
        - brand: Product brand
        - views_last_7days: Views in past week
        - views_last_30days: Views in past month
        - add_to_cart_count: Times added to cart
        - purchase_count: Number of purchases
        - conversion_rate: Purchase conversion percentage
        - avg_rating: Average customer rating
        - num_reviews: Number of reviews
        - trending_score: Overall trending score (0-1)
        - stock_level: Stock availability ("High", "Medium", "Low")
        - last_updated: Last trend data update
    
    Example:
        trends = get_product_trends(category="Fashion", limit=10)
        # Returns: [{"product_id": 41030, "trending_score": 0.93, ...}, ...]
    """
    try:
        handler = ProductTrendHandler()
        
        if category:
            trends = handler.get_by_category(category)
        else:
            trends = handler.get_trending_products(limit=limit)
        
        return [t.model_dump() for t in trends[:limit]]
    except Exception as e:
        print(f"Error fetching product trends: {e}")
        return []


def get_referrals(user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve user's referral information and tracking.
    
    Use this tool to show users their referral status, pending rewards,
    and referred friends' progress.
    
    Args:
        user_id: Unique identifier for the referrer user
        status: Filter by referral status ("Pending", "Completed", "Expired")
    
    Returns:
        List of referral dictionaries, each containing:
        - referral_id: Unique referral identifier
        - referrer_user_id: User who made the referral
        - referred_user_id: User who was referred
        - referral_code: Referral code used
        - signup_date: When referred user signed up
        - first_payment_completed: Whether referred user made first payment
        - first_payment_date: When first payment was made
        - referrer_reward_popcoins: popCoins earned by referrer
        - referred_reward_popcoins: popCoins earned by referred user
        - reward_credited: Whether rewards have been credited
        - reward_credit_date: When rewards were credited
        - status: Referral status
    
    Example:
        referrals = get_referrals("U000001", status="Completed")
        # Returns: [{"referral_id": "REF001", "referrer_reward_popcoins": 100, ...}, ...]
    """
    try:
        handler = ReferralHandler()
        referrals = handler.get_user_referrals(user_id)
        
        if status:
            referrals = [r for r in referrals if r.status == status]
        
        return [r.model_dump() for r in referrals]
    except Exception as e:
        print(f"Error fetching referrals: {e}")
        return []


def get_budget_insights(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve user's budget tracking and spending insights.
    
    Use this tool to understand user's spending patterns, budget utilization,
    and savings from popCoins.
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        Dictionary containing budget insights:
        - user_id: User identifier
        - monthly_budget_limit: User's set budget limit
        - current_month_spend: Total spending this month
        - budget_remaining: Remaining budget
        - budget_utilized_percent: Percentage of budget used
        - alert_threshold: Budget alert threshold percentage
        - alert_enabled: Whether budget alerts are enabled
        - category_spending: JSON string with spending by category
        - top_spending_category: Category with most spending
        - avg_transaction_value: Average transaction amount
        - popcoins_saved_this_month: popCoins redeemed this month
        - last_updated: Last update timestamp
        
        Returns None if user has no budget tracking.
    
    Example:
        insights = get_budget_insights("U000001")
        # Returns: {"budget_utilized_percent": 75.3, "current_month_spend": 3766.24, ...}
    """
    try:
        handler = BudgetInsightsHandler()
        insights = handler.read_by_id(user_id)
        return insights.model_dump() if insights else None
    except Exception as e:
        print(f"Error fetching budget insights: {e}")
        return None


def get_notifications(
    user_id: str,
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Retrieve user's notifications.
    
    Use this tool to check user's notification history and unread messages.
    
    Args:
        user_id: Unique identifier for the user
        unread_only: If True, return only unread notifications (default: False)
        notification_type: Filter by type ("Challenge Update", "popCoin Alert", etc.)
        limit: Maximum number of notifications to return (default: 20)
    
    Returns:
        List of notification dictionaries, each containing:
        - notification_id: Unique notification identifier
        - user_id: User identifier
        - notification_type: Type of notification
        - title: Notification title
        - message: Notification message content
        - sent_at: When notification was sent
        - is_read: Whether notification has been read
        - read_at: When notification was read
        - clicked: Whether user clicked on notification
        - channel: Delivery channel ("In-App", "Push", "Email")
        - priority: Priority level ("Low", "Medium", "High")
    
    Example:
        notifications = get_notifications("U000001", unread_only=True)
        # Returns: [{"notification_id": "NOTIF001", "title": "popCoins Expiring!", ...}, ...]
    """
    try:
        handler = NotificationHandler()
        notifications = handler.get_user_notifications(user_id, unread_only=unread_only)
        
        if notification_type:
            notifications = [n for n in notifications if n.notification_type == notification_type]
        
        return [n.model_dump() for n in notifications[:limit]]
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return []


# ============================================================================
# ANALYTICS & CALCULATION TOOLS (7 tools)
# ============================================================================

def calculate_savings_potential(product_id: str, user_xcoin_balance: int) -> Dict[str, Any]:
    """
    Calculate real-time savings percentage and amount for a product.
    
    Use this tool to show users how much they can save by redeeming popCoins
    on a specific product.
    
    Args:
        product_id: Product to calculate savings for
        user_xcoin_balance: User's current popCoin balance
    
    Returns:
        Dictionary containing savings analysis:
        - product_id: Product identifier
        - product_title: Product name
        - mrp: Maximum retail price
        - selling_price: Current selling price with popCoins
        - popcoins_required: popCoins needed for redemption
        - user_has_enough_popcoins: Whether user can afford with current balance
        - popcoins_shortage: popCoins needed (if insufficient)
        - savings_amount: Rupees saved vs MRP
        - savings_percentage: Percentage discount
        - effective_price: Final price user pays
        - xcoin_value_rate: Rupees per popCoin conversion rate
    
    Example:
        savings = calculate_savings_potential(41030, 536)
        # Returns: {"savings_percentage": 33.9, "savings_amount": 178, ...}
    """
    try:
        product = get_product_by_id(product_id)
        if not product:
            return {"error": "Product not found"}
        
        mrp = product.get('mrp', 0) or 0
        sp = product.get('sp', 0) or 0
        popcoins_required = product.get('coins_burn', 0) or 0
        
        user_has_enough = user_xcoin_balance >= popcoins_required
        shortage = max(0, popcoins_required - user_xcoin_balance)
        
        # Calculate savings
        savings_amount = mrp - sp
        savings_percentage = (savings_amount / mrp * 100) if mrp > 0 else 0
        
        # Calculate popCoin value rate (how much 1 popCoin is worth)
        xcoin_value_rate = (mrp - sp) / popcoins_required if popcoins_required > 0 else 0
        
        return {
            "product_id": product_id,
            "product_title": product.get('title', ''),
            "mrp": mrp,
            "selling_price": sp,
            "popcoins_required": popcoins_required,
            "user_has_enough_popcoins": user_has_enough,
            "popcoins_shortage": shortage,
            "savings_amount": round(savings_amount, 2),
            "savings_percentage": round(savings_percentage, 2),
            "effective_price": sp,
            "xcoin_value_rate": round(xcoin_value_rate, 2)
        }
    except Exception as e:
        return {"error": f"Error calculating savings: {e}"}


def calculate_earning_rate(user_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Analyze user's popCoin earning rate and velocity.
    
    Use this tool to understand how fast a user earns popCoins based on
    their transaction patterns.
    
    Args:
        user_id: Unique identifier for the user
        days: Number of days to analyze (default: 30)
    
    Returns:
        Dictionary containing earning rate analysis:
        - user_id: User identifier
        - analysis_period_days: Days analyzed
        - total_transactions: Number of transactions in period
        - successful_transactions: Number of successful transactions
        - total_popcoins_earned: Total popCoins earned in period
        - avg_popcoins_per_transaction: Average popCoins per transaction
        - avg_popcoins_per_day: Daily earning rate
        - estimated_monthly_earning: Projected monthly popCoin earning
        - most_profitable_payment_method: Payment method with highest popCoin rate
        - transaction_frequency: Transactions per week
    
    Example:
        rate = calculate_earning_rate("U000001", days=30)
        # Returns: {"avg_popcoins_per_day": 15.2, "estimated_monthly_earning": 456, ...}
    """
    try:
        transactions = get_transaction_history(user_id, days=days, status="Success")
        
        if not transactions:
            return {
                "user_id": user_id,
                "analysis_period_days": days,
                "error": "No transactions found in period"
            }
        
        total_popcoins = sum(t['popcoins_earned'] for t in transactions)
        total_count = len(transactions)
        
        # Calculate averages
        avg_per_transaction = total_popcoins / total_count if total_count > 0 else 0
        avg_per_day = total_popcoins / days if days > 0 else 0
        estimated_monthly = avg_per_day * 30
        
        # Find most profitable payment method
        method_earnings = {}
        for t in transactions:
            method = t['payment_method']
            method_earnings[method] = method_earnings.get(method, 0) + t['popcoins_earned']
        
        most_profitable = max(method_earnings.items(), key=lambda x: x[1])[0] if method_earnings else None
        
        return {
            "user_id": user_id,
            "analysis_period_days": days,
            "total_transactions": total_count,
            "successful_transactions": total_count,
            "total_popcoins_earned": total_popcoins,
            "avg_popcoins_per_transaction": round(avg_per_transaction, 2),
            "avg_popcoins_per_day": round(avg_per_day, 2),
            "estimated_monthly_earning": round(estimated_monthly, 0),
            "most_profitable_payment_method": most_profitable,
            "transaction_frequency": round((total_count / days) * 7, 2)  # per week
        }
    except Exception as e:
        return {"error": f"Error calculating earning rate: {e}"}


def calculate_goal_timeline(
    user_id: str,
    target_popcoins: int,
    current_popcoins: int
) -> Dict[str, Any]:
    """
    Estimate timeline to reach a popCoin goal based on earning rate.
    
    Use this tool to tell users how long it will take to accumulate
    enough popCoins for a specific goal.
    
    Args:
        user_id: Unique identifier for the user
        target_popcoins: popCoins needed for goal
        current_popcoins: User's current popCoin balance
    
    Returns:
        Dictionary containing timeline estimation:
        - user_id: User identifier
        - target_popcoins: Goal popCoins
        - current_popcoins: Current balance
        - popcoins_needed: Remaining popCoins to earn
        - already_achieved: Whether goal already met
        - estimated_days: Days to reach goal
        - estimated_weeks: Weeks to reach goal
        - estimated_transactions: Transactions needed
        - target_date: Estimated achievement date
        - daily_earning_rate: User's daily popCoin earning rate
        - recommendation: Suggested action
    
    Example:
        timeline = calculate_goal_timeline("U000001", 1000, 536)
        # Returns: {"estimated_days": 30, "estimated_transactions": 32, ...}
    """
    try:
        popcoins_needed = target_popcoins - current_popcoins
        
        if popcoins_needed <= 0:
            return {
                "user_id": user_id,
                "target_popcoins": target_popcoins,
                "current_popcoins": current_popcoins,
                "popcoins_needed": 0,
                "already_achieved": True,
                "recommendation": "You already have enough popCoins for this goal!"
            }
        
        # Get earning rate
        earning_rate = calculate_earning_rate(user_id, days=30)
        
        if 'error' in earning_rate:
            return {
                "user_id": user_id,
                "error": "Cannot calculate timeline without transaction history"
            }
        
        daily_rate = earning_rate['avg_popcoins_per_day']
        per_transaction = earning_rate['avg_popcoins_per_transaction']
        
        # Calculate timeline
        estimated_days = (popcoins_needed / daily_rate) if daily_rate > 0 else 999
        estimated_weeks = estimated_days / 7
        estimated_transactions = (popcoins_needed / per_transaction) if per_transaction > 0 else 999
        target_date = (datetime.now() + timedelta(days=estimated_days)).date()
        
        # Generate recommendation
        if estimated_days <= 7:
            recommendation = f"You're close! Just {int(estimated_transactions)} more transactions."
        elif estimated_days <= 30:
            recommendation = f"About {int(estimated_weeks)} weeks. Keep up your current pace!"
        else:
            recommendation = "This will take a while. Consider challenges to speed up!"
        
        return {
            "user_id": user_id,
            "target_popcoins": target_popcoins,
            "current_popcoins": current_popcoins,
            "popcoins_needed": popcoins_needed,
            "already_achieved": False,
            "estimated_days": round(estimated_days, 0),
            "estimated_weeks": round(estimated_weeks, 1),
            "estimated_transactions": round(estimated_transactions, 0),
            "target_date": target_date.isoformat(),
            "daily_earning_rate": daily_rate,
            "recommendation": recommendation
        }
    except Exception as e:
        return {"error": f"Error calculating timeline: {e}"}


def find_optimal_redemption(
    user_xcoin_balance: int,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Find products with best cash+popCoin value combinations.
    
    Use this tool to recommend products that maximize the value of user's
    current popCoin balance.
    
    Args:
        user_xcoin_balance: User's current popCoin balance
        category: Filter by product category (optional)
        max_price: Maximum selling price user wants to pay (optional)
        limit: Maximum number of recommendations (default: 10)
    
    Returns:
        List of optimal redemption options, sorted by value efficiency:
        - product_id: Product identifier
        - product_title: Product name
        - category: Product category
        - brand: Product brand
        - mrp: Maximum retail price
        - selling_price: Price with popCoins
        - popcoins_required: popCoins needed
        - savings_amount: Rupees saved
        - savings_percentage: Discount percentage
        - value_efficiency_score: Overall value score (higher is better)
        - user_can_afford: Whether user has enough popCoins
    
    Example:
        options = find_optimal_redemption(536, category="Fashion", max_price=1000)
        # Returns: [{"product_id": 123, "value_efficiency_score": 0.95, ...}, ...]
    """
    try:
        products = get_catalog_products(
            category=category,
            max_price=max_price,
            max_xcoin_required=user_xcoin_balance,
            limit=100  # Get more to analyze
        )
        
        redemption_options = []
        
        for product in products:
            mrp = product.get('mrp', 0) or 0
            sp = product.get('sp', 0) or 0
            popcoins_req = product.get('coins_burn', 0) or 0
            
            if mrp <= 0 or popcoins_req <= 0:
                continue
            
            savings_amount = mrp - sp
            savings_percentage = (savings_amount / mrp * 100)
            
            # Value efficiency: considers both discount % and popCoin conversion rate
            xcoin_value_rate = savings_amount / popcoins_req if popcoins_req > 0 else 0
            value_efficiency_score = (savings_percentage / 100) * 0.6 + (xcoin_value_rate / 10) * 0.4
            
            redemption_options.append({
                "product_id": product['id'],
                "product_title": product['title'],
                "category": product.get('category_name', ''),
                "brand": product.get('brand_name', ''),
                "mrp": mrp,
                "selling_price": sp,
                "popcoins_required": popcoins_req,
                "savings_amount": round(savings_amount, 2),
                "savings_percentage": round(savings_percentage, 2),
                "value_efficiency_score": round(value_efficiency_score, 3),
                "user_can_afford": user_xcoin_balance >= popcoins_req,
                'image_list': product.get('image_list', '')
            })
        
        # Sort by value efficiency score
        redemption_options.sort(key=lambda x: x['value_efficiency_score'], reverse=True)
        
        return redemption_options[:limit]
    except Exception as e:
        return [{"error": f"Error finding optimal redemption: {e}"}]


def analyze_transaction_patterns(user_id: str, days: int = 90) -> Dict[str, Any]:
    """
    Analyze user's transaction patterns and spending behavior.
    
    Use this tool to understand user's payment preferences, spending categories,
    and transaction timing patterns.
    
    Args:
        user_id: Unique identifier for the user
        days: Number of days to analyze (default: 90)
    
    Returns:
        Dictionary containing pattern analysis:
        - user_id: User identifier
        - analysis_period_days: Days analyzed
        - total_transactions: Total number of transactions
        - total_amount_spent: Total spending in rupees
        - payment_method_breakdown: Spending by payment method
        - category_breakdown: Spending by category
        - preferred_payment_method: Most used payment method
        - avg_transaction_amount: Average transaction size
        - peak_transaction_day: Day of week with most transactions
        - peak_transaction_hour: Hour of day with most transactions
        - transaction_trend: "Increasing", "Stable", or "Decreasing"
    
    Example:
        patterns = analyze_transaction_patterns("U000001", days=90)
        # Returns: {"preferred_payment_method": "UPI", "total_amount_spent": 45320.75, ...}
    """
    try:
        transactions = get_transaction_history(user_id, days=days)
        
        if not transactions:
            return {
                "user_id": user_id,
                "analysis_period_days": days,
                "error": "No transactions found"
            }
        
        total_count = len(transactions)
        total_amount = sum(t['amount'] for t in transactions)
        
        # Payment method breakdown
        payment_methods = {}
        for t in transactions:
            method = t['payment_method']
            payment_methods[method] = payment_methods.get(method, {'count': 0, 'amount': 0})
            payment_methods[method]['count'] += 1
            payment_methods[method]['amount'] += t['amount']
        
        # Category breakdown
        categories = {}
        for t in transactions:
            cat = t.get('category', 'Other')
            categories[cat] = categories.get(cat, {'count': 0, 'amount': 0})
            categories[cat]['count'] += 1
            categories[cat]['amount'] += t['amount']
        
        # Find preferred method
        preferred_method = max(payment_methods.items(), key=lambda x: x[1]['count'])[0] if payment_methods else None
        
        # Day/hour analysis
        day_counts = {}
        hour_counts = {}
        for t in transactions:
            tx_date = datetime.fromisoformat(t['transaction_date'].replace('Z', '+00:00')) if isinstance(t['transaction_date'], str) else t['transaction_date']
            day = tx_date.strftime('%A')
            hour = tx_date.hour
            
            day_counts[day] = day_counts.get(day, 0) + 1
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        peak_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else None
        
        return {
            "user_id": user_id,
            "analysis_period_days": days,
            "total_transactions": total_count,
            "total_amount_spent": round(total_amount, 2),
            "payment_method_breakdown": payment_methods,
            "category_breakdown": categories,
            "preferred_payment_method": preferred_method,
            "avg_transaction_amount": round(total_amount / total_count, 2) if total_count > 0 else 0,
            "peak_transaction_day": peak_day,
            "peak_transaction_hour": peak_hour
        }
    except Exception as e:
        return {"error": f"Error analyzing patterns: {e}"}


def calculate_budget_utilization(user_id: str) -> Dict[str, Any]:
    """
    Calculate current budget utilization and provide forecasting.
    
    Use this tool to show users how much of their budget they've used
    and predict when they'll hit their limit.
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        Dictionary containing budget analysis:
        - user_id: User identifier
        - monthly_budget: Set budget limit
        - current_spend: Spending so far this month
        - remaining_budget: Budget left
        - utilization_percentage: Percentage of budget used
        - days_into_month: Days elapsed in current month
        - days_remaining_in_month: Days left in month
        - daily_burn_rate: Average spending per day
        - projected_month_end_spend: Forecasted total spending
        - budget_status: "On Track", "Warning", or "Over Budget"
        - recommendation: Suggested action
    
    Example:
        utilization = calculate_budget_utilization("U000001")
        # Returns: {"utilization_percentage": 85.2, "budget_status": "Warning", ...}
    """
    try:
        insights = get_budget_insights(user_id)
        
        if not insights:
            return {
                "user_id": user_id,
                "error": "No budget tracking found for user"
            }
        
        budget_limit = insights['monthly_budget_limit']
        current_spend = insights['current_month_spend']
        remaining = insights['budget_remaining']
        utilization = insights['budget_utilized_percent']
        
        # Calculate days
        today = datetime.now()
        days_in_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        days_into_month = today.day
        days_remaining = days_in_month.day - days_into_month
        
        # Calculate burn rate and projection
        daily_burn = current_spend / days_into_month if days_into_month > 0 else 0
        projected_spend = current_spend + (daily_burn * days_remaining)
        
        # Determine status
        if utilization < 75:
            status = "On Track"
            recommendation = "You're doing great! Keep monitoring your spending."
        elif utilization < 100:
            status = "Warning"
            recommendation = f"You're using budget quickly. Try to limit to ₹{round(remaining/days_remaining, 0)}/day."
        else:
            status = "Over Budget"
            recommendation = f"You're ₹{abs(remaining):.0f} over budget. Use popCoins to reduce spending!"
        
        return {
            "user_id": user_id,
            "monthly_budget": budget_limit,
            "current_spend": current_spend,
            "remaining_budget": remaining,
            "utilization_percentage": round(utilization, 2),
            "days_into_month": days_into_month,
            "days_remaining_in_month": days_remaining,
            "daily_burn_rate": round(daily_burn, 2),
            "projected_month_end_spend": round(projected_spend, 2),
            "budget_status": status,
            "recommendation": recommendation
        }
    except Exception as e:
        return {"error": f"Error calculating budget utilization: {e}"}


def calculate_conversion_value(popcoins: int, product_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Calculate real currency value of popCoins.
    
    Use this tool to show users what their popCoins are worth in rupees,
    either generally or for a specific product.
    
    Args:
        popcoins: Number of popCoins to evaluate
        product_id: Specific product to calculate value for (optional)
    
    Returns:
        Dictionary containing value conversion:
        - popcoins: Number of popCoins
        - product_id: Product evaluated (if specified)
        - estimated_rupee_value: Estimated value in rupees
        - conversion_rate: Rupees per xCoin
        - basis: How value was calculated
    
    Example:
        value = calculate_conversion_value(500, product_id=41030)
        # Returns: {"estimated_rupee_value": 2500, "conversion_rate": 5.0, ...}
    """
    try:
        if product_id:
            # Calculate value for specific product
            product = get_product_by_id(product_id)
            if not product:
                return {"error": "Product not found"}
            
            mrp = product.get('mrp', 0) or 0
            sp = product.get('sp', 0) or 0
            coins_required = product.get('coins_burn', 0) or 0
            
            if coins_required > 0:
                savings = mrp - sp
                conversion_rate = savings / coins_required
                estimated_value = popcoins * conversion_rate
                
                return {
                    "popcoins": popcoins,
                    "product_id": product_id,
                    "product_title": product.get('title', ''),
                    "estimated_rupee_value": round(estimated_value, 2),
                    "conversion_rate": round(conversion_rate, 2),
                    "basis": f"Based on {product.get('title', 'product')} redemption rate"
                }
        
        # General conversion based on average across catalog
        products = get_catalog_products(limit=100)
        
        rates = []
        for p in products:
            mrp = p.get('mrp', 0) or 0
            sp = p.get('sp', 0) or 0
            coins = p.get('coins_burn', 0) or 0
            
            if coins > 0 and mrp > sp:
                rates.append((mrp - sp) / coins)
        
        if rates:
            avg_rate = sum(rates) / len(rates)
            estimated_value = popcoins * avg_rate
            
            return {
                "popcoins": popcoins,
                "product_id": None,
                "estimated_rupee_value": round(estimated_value, 2),
                "conversion_rate": round(avg_rate, 2),
                "basis": f"Average conversion rate across {len(rates)} products"
            }
        
        # Fallback: assume 1 popCoin ≈ ₹5 (typical industry standard)
        return {
            "popcoins": popcoins,
            "product_id": None,
            "estimated_rupee_value": popcoins * 5,
            "conversion_rate": 5.0,
            "basis": "Industry standard estimate"
        }
    except Exception as e:
        return {"error": f"Error calculating conversion: {e}"}


# ============================================================================
# ACTION & UPDATE TOOLS (10 tools)
# ============================================================================

def create_user_goal(
    user_id: str,
    product_id: str,
    notification_enabled: bool = True
) -> Dict[str, Any]:
    """
    Create a new product purchase goal for a user.
    
    Use this tool when a user wants to save popCoins for a specific product.
    
    Args:
        user_id: Unique identifier for the user
        product_id: Product the user wants to save for
        notification_enabled: Whether to send progress notifications (default: True)
    
    Returns:
        Dictionary containing created goal or error:
        - success: Whether goal was created
        - goal_id: Unique goal identifier (if successful)
        - message: Success or error message
        - goal_details: Complete goal information (if successful)
    
    Example:
        result = create_user_goal("U000001", 41030, notification_enabled=True)
        # Returns: {"success": True, "goal_id": "GOAL00000123", ...}
    """
    try:
        # Get product details
        product = get_product_by_id(product_id)
        if not product:
            return {"success": False, "message": "Product not found"}
        
        # Get user's current popCoin balance
        balance_info = get_xcoin_balance(user_id)
        current_popcoins = balance_info['current_balance'] if balance_info else 0
        
        # Get earning rate to estimate timeline
        earning_info = calculate_earning_rate(user_id, days=30)
        daily_rate = earning_info.get('avg_popcoins_per_day', 15)
        
        target_popcoins = product.get('coins_burn', 0) or 0
        popcoins_needed = max(0, target_popcoins - current_popcoins)
        estimated_days = int(popcoins_needed / daily_rate) if daily_rate > 0 else 30
        
        # Generate goal ID
        handler = UserGoalHandler()
        existing_goals = handler.read_all()
        goal_id = f"GOAL{str(len(existing_goals) + 1).zfill(8)}"
        
        # Create goal object
        goal = UserGoal(
            goal_id=goal_id,
            user_id=user_id,
            product_id=product_id,
            product_title=product['title'],
            target_popcoins=target_popcoins,
            current_popcoins=current_popcoins,
            popcoins_needed=popcoins_needed,
            target_price=product.get('sp', 0),
            estimated_days=estimated_days,
            created_at=date.today(),
            target_date=date.today() + timedelta(days=estimated_days),
            status="Active",
            notification_enabled=notification_enabled
        )
        
        # Save goal
        created_goal = handler.create(goal)
        
        return {
            "success": True,
            "goal_id": goal_id,
            "message": f"Goal created successfully for {product['title']}",
            "goal_details": created_goal.model_dump()
        }
    except Exception as e:
        return {"success": False, "message": f"Error creating goal: {e}"}


def update_goal_progress(goal_id: str, new_current_popcoins: int) -> Dict[str, Any]:
    """
    Update progress on an existing user goal.
    
    Use this tool to refresh goal status when user earns more popCoins.
    
    Args:
        goal_id: Unique goal identifier
        new_current_popcoins: User's updated popCoin balance
    
    Returns:
        Dictionary containing update result:
        - success: Whether update was successful
        - message: Success or error message
        - milestone_reached: Whether a milestone (25%, 50%, 75%, 100%) was hit
        - goal_completed: Whether goal is now complete
        - updated_goal: Complete updated goal information
    
    Example:
        result = update_goal_progress("GOAL00000001", 750)
        # Returns: {"success": True, "milestone_reached": 75, "goal_completed": False, ...}
    """
    try:
        handler = UserGoalHandler()
        goal = handler.read_by_id(goal_id)
        
        if not goal:
            return {"success": False, "message": "Goal not found"}
        
        target = goal.target_popcoins
        old_progress = ((goal.current_popcoins / target) * 100) if target > 0 else 0
        new_progress = ((new_current_popcoins / target) * 100) if target > 0 else 0
        
        # Check for milestone
        milestones = [25, 50, 75, 100]
        milestone_reached = None
        
        for milestone in milestones:
            if old_progress < milestone <= new_progress:
                milestone_reached = milestone
                break
        
        # Update goal
        popcoins_needed = max(0, target - new_current_popcoins)
        goal_completed = new_current_popcoins >= target
        
        updates = {
            "current_popcoins": new_current_popcoins,
            "popcoins_needed": popcoins_needed,
            "status": "Completed" if goal_completed else "Active"
        }
        
        updated_goal = handler.update(goal_id, updates)
        
        return {
            "success": True,
            "message": "Goal progress updated successfully",
            "milestone_reached": milestone_reached,
            "goal_completed": goal_completed,
            "progress_percentage": round(new_progress, 2),
            "updated_goal": updated_goal.model_dump() if updated_goal else None
        }
    except Exception as e:
        return {"success": False, "message": f"Error updating goal: {e}"}


def create_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    priority: str = "Medium",
    channel: str = "In-App"
) -> Dict[str, Any]:
    """
    Create and send a notification to a user.
    
    Use this tool to alert users about important events, reminders, or updates.
    
    Args:
        user_id: Unique identifier for the user
        notification_type: Type ("popCoin Alert", "Challenge Update", "Goal Milestone", etc.)
        title: Notification title
        message: Notification message content
        priority: Priority level - "Low", "Medium", or "High" (default: "Medium")
        channel: Delivery channel - "In-App", "Push", or "Email" (default: "In-App")
    
    Returns:
        Dictionary containing notification result:
        - success: Whether notification was created
        - notification_id: Unique notification identifier
        - message: Success or error message
    
    Example:
        result = create_notification(
            "U000001",
            "popCoin Alert",
            "popCoins Expiring Soon!",
            "You have 250 popCoins expiring on Dec 8th",
            priority="High"
        )
        # Returns: {"success": True, "notification_id": "NOTIF00000123", ...}
    """
    try:
        handler = NotificationHandler()
        existing = handler.read_all()
        notification_id = f"NOTIF{str(len(existing) + 1).zfill(8)}"
        
        notification = Notification(
            notification_id=notification_id,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            sent_at=datetime.now(),
            is_read=False,
            read_at=None,
            clicked=False,
            channel=channel,
            priority=priority
        )
        
        created = handler.create(notification)
        
        return {
            "success": True,
            "notification_id": notification_id,
            "message": "Notification created successfully"
        }
    except Exception as e:
        return {"success": False, "message": f"Error creating notification: {e}"}


def mark_notification_read(notification_id: str) -> Dict[str, Any]:
    """
    Mark a notification as read.
    
    Use this tool when user views/acknowledges a notification.
    
    Args:
        notification_id: Unique notification identifier
    
    Returns:
        Dictionary containing result:
        - success: Whether notification was marked read
        - message: Success or error message
    
    Example:
        result = mark_notification_read("NOTIF00000001")
        # Returns: {"success": True, "message": "Notification marked as read"}
    """
    try:
        handler = NotificationHandler()
        updated = handler.mark_as_read(notification_id)
        
        if updated:
            return {
                "success": True,
                "message": "Notification marked as read"
            }
        else:
            return {
                "success": False,
                "message": "Notification not found"
            }
    except Exception as e:
        return {"success": False, "message": f"Error marking notification: {e}"}


def add_to_cart(
    user_id: str,
    product_id: str,
    quantity: int = 1
) -> Dict[str, Any]:
    """
    Add a product to user's shopping cart.
    
    Use this tool when user wants to save a product for later purchase.
    
    Args:
        user_id: Unique identifier for the user
        product_id: Product to add to cart
        quantity: Number of items to add (default: 1)
    
    Returns:
        Dictionary containing result:
        - success: Whether product was added
        - cart_id: Unique cart item identifier
        - message: Success or error message
        - cart_item: Complete cart item details
    
    Example:
        result = add_to_cart("U000001", 41030, quantity=2)
        # Returns: {"success": True, "cart_id": "CART00000123", ...}
    """
    try:
        # Get product details
        product = get_product_by_id(product_id)
        if not product:
            return {"success": False, "message": "Product not found"}
        
        handler = ShoppingCartHandler()
        existing = handler.read_all()
        cart_id = f"CART{str(len(existing) + 1).zfill(8)}"
        
        cart_item = ShoppingCart(
            cart_id=cart_id,
            user_id=user_id,
            product_id=product_id,
            title=product['title'],
            category=product.get('category_name', ''),
            brand=product.get('brand_name', ''),
            quantity=quantity,
            price=product.get('sp', 0),
            mrp=product.get('mrp', 0),
            popcoins_required=product.get('coins_burn', 0) or 0,
            added_at=datetime.now(),
            is_available=True,
            price_changed=False
        )
        
        created = handler.create(cart_item)
        
        return {
            "success": True,
            "cart_id": cart_id,
            "message": f"Added {quantity}x {product['title']} to cart",
            "cart_item": created.model_dump()
        }
    except Exception as e:
        return {"success": False, "message": f"Error adding to cart: {e}"}


def remove_from_cart(cart_id: str) -> Dict[str, Any]:
    """
    Remove an item from shopping cart.
    
    Use this tool when user wants to delete a cart item.
    
    Args:
        cart_id: Unique cart item identifier
    
    Returns:
        Dictionary containing result:
        - success: Whether item was removed
        - message: Success or error message
    
    Example:
        result = remove_from_cart("CART00000001")
        # Returns: {"success": True, "message": "Item removed from cart"}
    """
    try:
        handler = ShoppingCartHandler()
        deleted = handler.delete(cart_id)
        
        if deleted:
            return {
                "success": True,
                "message": "Item removed from cart"
            }
        else:
            return {
                "success": False,
                "message": "Cart item not found"
            }
    except Exception as e:
        return {"success": False, "message": f"Error removing from cart: {e}"}


def update_cart_quantity(cart_id: str, new_quantity: int) -> Dict[str, Any]:
    """
    Update quantity of an item in shopping cart.
    
    Use this tool to change how many units of a product are in cart.
    
    Args:
        cart_id: Unique cart item identifier
        new_quantity: New quantity (must be >= 1)
    
    Returns:
        Dictionary containing result:
        - success: Whether quantity was updated
        - message: Success or error message
        - updated_item: Complete updated cart item
    
    Example:
        result = update_cart_quantity("CART00000001", 3)
        # Returns: {"success": True, "message": "Quantity updated to 3", ...}
    """
    try:
        if new_quantity < 1:
            return {"success": False, "message": "Quantity must be at least 1"}
        
        handler = ShoppingCartHandler()
        updated = handler.update(cart_id, {"quantity": new_quantity})
        
        if updated:
            return {
                "success": True,
                "message": f"Quantity updated to {new_quantity}",
                "updated_item": updated.model_dump()
            }
        else:
            return {
                "success": False,
                "message": "Cart item not found"
            }
    except Exception as e:
        return {"success": False, "message": f"Error updating quantity: {e}"}


def enroll_in_challenge(user_id: str, challenge_id: str) -> Dict[str, Any]:
    """
    Enroll a user in a challenge.
    
    Use this tool when user wants to participate in a challenge to earn bonus popCoins.
    
    Args:
        user_id: Unique identifier for the user
        challenge_id: Challenge to enroll in
    
    Returns:
        Dictionary containing result:
        - success: Whether enrollment was successful
        - progress_id: Unique progress tracking identifier
        - message: Success or error message
        - challenge_details: Complete challenge information
    
    Example:
        result = enroll_in_challenge("U000001", "CH001")
        # Returns: {"success": True, "progress_id": "PROG00000123", ...}
    """
    try:
        # Get challenge details
        challenge_handler = ChallengeHandler()
        challenge = challenge_handler.read_by_id(challenge_id)
        
        if not challenge:
            return {"success": False, "message": "Challenge not found"}
        
        if not challenge.is_active:
            return {"success": False, "message": "Challenge is not active"}
        
        # Check if already enrolled
        progress_handler = ChallengeProgressHandler()
        existing = progress_handler.search(
            lambda p: p.user_id == user_id and p.challenge_id == challenge_id
        )
        
        if existing:
            return {
                "success": False,
                "message": "Already enrolled in this challenge",
                "progress_id": existing[0].progress_id
            }
        
        # Create progress tracking
        all_progress = progress_handler.read_all()
        progress_id = f"PROG{str(len(all_progress) + 1).zfill(8)}"
        
        progress = UserChallengeProgress(
            progress_id=progress_id,
            user_id=user_id,
            challenge_id=challenge_id,
            challenge_name=challenge.challenge_name,
            current_progress=0,
            target_value=challenge.target_value,
            progress_percentage=0.0,
            is_completed=False,
            popcoins_earned=0,
            started_at=date.today(),
            completed_at=None,
            last_updated=datetime.now()
        )
        
        created = progress_handler.create(progress)
        
        return {
            "success": True,
            "progress_id": progress_id,
            "message": f"Successfully enrolled in {challenge.challenge_name}",
            "challenge_details": challenge.model_dump()
        }
    except Exception as e:
        return {"success": False, "message": f"Error enrolling in challenge: {e}"}


def generate_referral_code(user_id: str) -> Dict[str, Any]:
    """
    Generate a referral code for a user.
    
    Use this tool to create a unique referral code that user can share with friends.
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        Dictionary containing referral information:
        - success: Whether code was generated
        - referral_code: Unique referral code
        - message: Success or error message
        - share_link: Shareable link (if applicable)
    
    Example:
        result = generate_referral_code("U000001")
        # Returns: {"success": True, "referral_code": "REFU000001", ...}
    """
    try:
        # Generate code based on user ID
        referral_code = f"REF{user_id}"
        
        # Create shareable link (example format)
        share_link = f"https://PopCash.app/join?ref={referral_code}"
        
        return {
            "success": True,
            "referral_code": referral_code,
            "message": "Referral code generated successfully",
            "share_link": share_link,
            "instructions": "Share this code with friends. You both earn popCoins when they make their first payment!"
        }
    except Exception as e:
        return {"success": False, "message": f"Error generating referral code: {e}"}


def update_budget_alert(user_id: str, alert_enabled: bool, alert_threshold: int = 75) -> Dict[str, Any]:
    """
    Update user's budget alert settings.
    
    Use this tool to enable/disable budget alerts and set threshold percentage.
    
    Args:
        user_id: Unique identifier for the user
        alert_enabled: Whether to enable budget alerts
        alert_threshold: Percentage of budget to trigger alert (default: 75)
    
    Returns:
        Dictionary containing result:
        - success: Whether settings were updated
        - message: Success or error message
        - current_settings: Updated alert settings
    
    Example:
        result = update_budget_alert("U000001", True, 80)
        # Returns: {"success": True, "message": "Alert settings updated", ...}
    """
    try:
        handler = BudgetInsightsHandler()
        
        updates = {
            "alert_enabled": alert_enabled,
            "alert_threshold": alert_threshold
        }
        
        updated = handler.update(user_id, updates)
        
        if updated:
            return {
                "success": True,
                "message": "Budget alert settings updated successfully",
                "current_settings": {
                    "alert_enabled": alert_enabled,
                    "alert_threshold": alert_threshold
                }
            }
        else:
            return {
                "success": False,
                "message": "User budget tracking not found"
            }
    except Exception as e:
        return {"success": False, "message": f"Error updating alert settings: {e}"}


# ============================================================================
# INTELLIGENCE & RECOMMENDATION TOOLS (6 tools)
# ============================================================================

def get_alternative_products(
    product_id: str,
    user_xcoin_balance: int,
    max_price_difference: float = 500
) -> List[Dict[str, Any]]:
    """
    Find similar alternative products that user can afford.
    
    Use this tool when user's goal product is too expensive or out of stock,
    to suggest comparable alternatives within their budget.
    
    Args:
        product_id: Original product user is interested in
        user_xcoin_balance: User's current popCoin balance
        max_price_difference: Maximum price difference from original (default: ₹500)
    
    Returns:
        List of alternative product recommendations:
        - product_id: Alternative product identifier
        - product_title: Product name
        - category: Product category
        - brand: Product brand
        - price: Selling price
        - popcoins_required: popCoins needed
        - similarity_score: How similar to original (0-1)
        - user_can_afford: Whether user has enough popCoins
        - price_difference: Price difference from original
    
    Example:
        alternatives = get_alternative_products(41030, 536, max_price_difference=300)
        # Returns: [{"product_id": 41035, "similarity_score": 0.85, ...}, ...]
    """
    try:
        # Get original product
        original = get_product_by_id(product_id)
        if not original:
            return [{"error": "Original product not found"}]
        
        original_price = original.get('sp', 0)
        original_category = original.get('category_name', '')
        original_brand = original.get('brand_name', '')
        
        # Get products in same category
        similar_products = get_catalog_products(
            category=original_category,
            limit=50
        )
        
        alternatives = []
        
        for product in similar_products:
            if product['id'] == product_id:
                continue  # Skip original
            
            price = product.get('sp', 0)
            popcoins_req = product.get('coins_burn', 0) or 0
            
            # Check price difference
            price_diff = abs(price - original_price)
            if price_diff > max_price_difference:
                continue
            
            # Calculate similarity score
            similarity = 0.5  # Base for same category
            if product.get('brand_name') == original_brand:
                similarity += 0.3  # Bonus for same brand
            
            # Bonus for similar price
            price_similarity = 1 - (price_diff / max_price_difference)
            similarity += price_similarity * 0.2
            
            alternatives.append({
                "product_id": product['id'],
                "product_title": product['title'],
                "category": product.get('category_name', ''),
                "brand": product.get('brand_name', ''),
                "price": price,
                "popcoins_required": popcoins_req,
                "similarity_score": round(similarity, 2),
                "user_can_afford": user_xcoin_balance >= popcoins_req,
                "price_difference": round(price_diff, 2)
            })
        
        # Sort by similarity
        alternatives.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return alternatives[:10]
    except Exception as e:
        return [{"error": f"Error finding alternatives: {e}"}]


def predict_expiry_risk(user_id: str, days_ahead: int = 30) -> Dict[str, Any]:
    """
    Identify popCoins at risk of expiring soon.
    
    Use this tool to proactively alert users about popCoins they might lose
    if not redeemed in time.
    
    Args:
        user_id: Unique identifier for the user
        days_ahead: Look ahead period in days (default: 30)
    
    Returns:
        Dictionary containing expiry risk analysis:
        - user_id: User identifier
        - total_at_risk: Total popCoins expiring in period
        - expiry_timeline: Breakdown by time period
        - urgent_action_needed: Whether immediate action required
        - recommended_products: Products user can afford with expiring popCoins
        - days_until_first_expiry: Days to earliest expiration
    
    Example:
        risk = predict_expiry_risk("U000001", days_ahead=30)
        # Returns: {"total_at_risk": 250, "urgent_action_needed": True, ...}
    """
    try:
        ledger = get_xcoin_ledger(user_id, active_only=True)
        
        if not ledger:
            return {
                "user_id": user_id,
                "total_at_risk": 0,
                "message": "No active popCoins found"
            }
        
        today = date.today()
        cutoff = today + timedelta(days=days_ahead)
        
        expiring_soon = []
        timeline = {
            "next_7_days": 0,
            "8_to_15_days": 0,
            "16_to_30_days": 0
        }
        
        for entry in ledger:
            expiry = entry['expiry_date']
            if isinstance(expiry, str):
                expiry = date.fromisoformat(expiry)
            
            if expiry <= cutoff:
                coins = entry['popcoins_balance']
                expiring_soon.append(entry)
                
                days_until = (expiry - today).days
                
                if days_until <= 7:
                    timeline["next_7_days"] += coins
                elif days_until <= 15:
                    timeline["8_to_15_days"] += coins
                else:
                    timeline["16_to_30_days"] += coins
        
        total_at_risk = sum(e['popcoins_balance'] for e in expiring_soon)
        
        # Find earliest expiry
        if expiring_soon:
            earliest = min(expiring_soon, key=lambda x: x['expiry_date'])
            earliest_date = earliest['expiry_date']
            if isinstance(earliest_date, str):
                earliest_date = date.fromisoformat(earliest_date)
            days_until_first = (earliest_date - today).days
        else:
            days_until_first = None
        
        # Determine urgency
        urgent = timeline["next_7_days"] > 50
        
        # Get recommended products
        recommended = find_optimal_redemption(total_at_risk, limit=5) if total_at_risk > 0 else []
        
        return {
            "user_id": user_id,
            "total_at_risk": total_at_risk,
            "expiry_timeline": timeline,
            "urgent_action_needed": urgent,
            "days_until_first_expiry": days_until_first,
            "expiring_entries_count": len(expiring_soon),
            "recommended_products": recommended[:3]
        }
    except Exception as e:
        return {"error": f"Error predicting expiry risk: {e}"}


def suggest_earning_opportunities(user_id: str) -> List[Dict[str, Any]]:
    """
    Recommend strategies to earn popCoins faster based on user behavior.
    
    Use this tool to provide personalized earning suggestions aligned with
    user's transaction patterns and upcoming opportunities.
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        List of earning opportunity recommendations:
        - opportunity_type: Type of opportunity
        - title: Opportunity title
        - description: What user should do
        - potential_popcoins: Estimated popCoins user can earn
        - effort_level: "Low", "Medium", or "High"
        - priority: Recommended priority
        - action: Specific next step
    
    Example:
        opportunities = suggest_earning_opportunities("U000001")
        # Returns: [{"title": "Complete Bill Payments", "potential_popcoins": 150, ...}, ...]
    """
    try:
        # Analyze transaction patterns
        patterns = analyze_transaction_patterns(user_id, days=60)
        
        # Get active challenges
        challenges = get_challenges(active_only=True)
        user_progress = get_challenge_progress(user_id)
        enrolled_challenge_ids = {p['challenge_id'] for p in user_progress}
        
        opportunities = []
        
        # Opportunity 1: Unenrolled challenges matching user behavior
        for challenge in challenges:
            if challenge['challenge_id'] not in enrolled_challenge_ids:
                opportunities.append({
                    "opportunity_type": "Challenge",
                    "title": f"Join {challenge['challenge_name']} Challenge",
                    "description": challenge['description'],
                    "potential_popcoins": challenge['reward_popcoins'],
                    "effort_level": challenge['difficulty'],
                    "priority": "High" if challenge['difficulty'] == "Easy" else "Medium",
                    "action": f"Enroll in challenge: {challenge['challenge_id']}"
                })
        
        # Opportunity 2: Underutilized payment methods
        if 'payment_method_breakdown' in patterns:
            methods = patterns['payment_method_breakdown']
            preferred = patterns.get('preferred_payment_method')
            
            for method, stats in methods.items():
                if method != preferred and stats['count'] < 5:
                    opportunities.append({
                        "opportunity_type": "Payment Method",
                        "title": f"Try {method} Payments",
                        "description": f"You've only used {method} {stats['count']} times. Diversifying payment methods can unlock bonus popCoins.",
                        "potential_popcoins": 50,
                        "effort_level": "Low",
                        "priority": "Medium",
                        "action": f"Make your next payment using {method}"
                    })
        
        # Opportunity 3: Near-completion challenges
        for progress in user_progress:
            if not progress['is_completed'] and progress['progress_percentage'] > 50:
                remaining = progress['target_value'] - progress['current_progress']
                opportunities.append({
                    "opportunity_type": "Challenge Completion",
                    "title": f"Complete {progress['challenge_name']}",
                    "description": f"You're {progress['progress_percentage']:.0f}% done! Just {remaining} more to go.",
                    "potential_popcoins": get_challenge_by_id(progress['challenge_id']),
                    "effort_level": "Low",
                    "priority": "High",
                    "action": "Continue with your regular transactions"
                })
        
        # Opportunity 4: Referrals
        referrals = get_referrals(user_id)
        pending_referrals = [r for r in referrals if r['status'] == 'Pending']
        
        if len(pending_referrals) < 3:
            opportunities.append({
                "opportunity_type": "Referral",
                "title": "Refer Friends to PopCash",
                "description": "Earn 100 popCoins for each friend who makes their first payment",
                "potential_popcoins": 100 * (3 - len(pending_referrals)),
                "effort_level": "Medium",
                "priority": "Medium",
                "action": "Generate and share your referral code"
            })
        
        # Sort by potential popCoins and priority
        priority_order = {"High": 3, "Medium": 2, "Low": 1}
        opportunities.sort(
            key=lambda x: (priority_order.get(x['priority'], 0), x['potential_popcoins']),
            reverse=True
        )
        
        return opportunities[:5]
    except Exception as e:
        return [{"error": f"Error suggesting opportunities: {e}"}]


def get_challenge_by_id(challenge_id: str) -> int:
    """Helper to get challenge reward"""
    try:
        handler = ChallengeHandler()
        challenge = handler.read_by_id(challenge_id)
        return challenge.reward_popcoins if challenge else 0
    except:
        return 0


def detect_cart_abandonment(user_id: str, hours_threshold: int = 48) -> Dict[str, Any]:
    """
    Check for abandoned cart items and analyze status.
    
    Use this tool to identify when user has items sitting in cart that
    might need attention (price changes, low stock, etc.).
    
    Args:
        user_id: Unique identifier for the user
        hours_threshold: Consider cart abandoned after this many hours (default: 48)
    
    Returns:
        Dictionary containing cart abandonment analysis:
        - has_abandoned_items: Whether user has old cart items
        - cart_item_count: Number of items in cart
        - oldest_item_age_hours: Age of oldest cart item
        - total_cart_value: Total value of cart items
        - popcoins_required: Total popCoins needed for cart
        - price_changes_detected: Whether any prices changed
        - availability_issues: Whether any items out of stock
        - items: List of cart items with status
        - recommendation: Suggested action
    
    Example:
        abandonment = detect_cart_abandonment("U000001", hours_threshold=48)
        # Returns: {"has_abandoned_items": True, "cart_item_count": 3, ...}
    """
    try:
        cart_items = get_shopping_cart(user_id)
        
        if not cart_items:
            return {
                "has_abandoned_items": False,
                "cart_item_count": 0,
                "message": "No items in cart"
            }
        
        now = datetime.now()
        threshold = timedelta(hours=hours_threshold)
        
        abandoned_items = []
        total_value = 0
        total_popcoins = 0
        price_changes = 0
        availability_issues = 0
        
        for item in cart_items:
            added_at = item['added_at']
            if isinstance(added_at, str):
                added_at = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
            
            age = now - added_at
            
            if age >= threshold:
                abandoned_items.append({
                    "cart_id": item['cart_id'],
                    "product_title": item['title'],
                    "quantity": item['quantity'],
                    "price": item['price'],
                    "age_hours": int(age.total_seconds() / 3600),
                    "price_changed": item.get('price_changed', False),
                    "is_available": item.get('is_available', True)
                })
                
                if item.get('price_changed'):
                    price_changes += 1
                if not item.get('is_available', True):
                    availability_issues += 1
            
            total_value += item['price'] * item['quantity']
            total_popcoins += item['popcoins_required'] * item['quantity']
        
        oldest_age = max((now - (datetime.fromisoformat(i['added_at'].replace('Z', '+00:00')) if isinstance(i['added_at'], str) else i['added_at'])).total_seconds() / 3600 for i in cart_items) if cart_items else 0
        
        # Generate recommendation
        if availability_issues > 0:
            recommendation = f"{availability_issues} item(s) may be out of stock. Check availability now!"
        elif price_changes > 0:
            recommendation = f"{price_changes} item(s) have price changes. Review your cart!"
        elif len(abandoned_items) > 0:
            recommendation = f"You have {len(abandoned_items)} items waiting. Complete your purchase to earn popCoins!"
        else:
            recommendation = "Your cart is fresh. Complete checkout when ready!"
        
        return {
            "has_abandoned_items": len(abandoned_items) > 0,
            "cart_item_count": len(cart_items),
            "abandoned_item_count": len(abandoned_items),
            "oldest_item_age_hours": round(oldest_age, 1),
            "total_cart_value": round(total_value, 2),
            "popcoins_required": total_popcoins,
            "price_changes_detected": price_changes > 0,
            "availability_issues": availability_issues > 0,
            "items": abandoned_items,
            "recommendation": recommendation
        }
    except Exception as e:
        return {"error": f"Error detecting cart abandonment: {e}"}


def rank_products_by_value(
    product_ids: List[int],
    user_xcoin_balance: int
) -> List[Dict[str, Any]]:
    """
    Rank multiple products by popCoin value efficiency.
    
    Use this tool to help user choose between multiple products by showing
    which offers the best value for their popCoins.
    
    Args:
        product_ids: List of product IDs to compare
        user_xcoin_balance: User's current popCoin balance
    
    Returns:
        List of products ranked by value, each containing:
        - rank: Position in ranking (1 = best value)
        - product_id: Product identifier
        - product_title: Product name
        - price: Selling price
        - popcoins_required: popCoins needed
        - savings_percentage: Discount percentage
        - value_score: Overall value score
        - affordability: Whether user can afford
        - recommendation: Why this product ranks here
    
    Example:
        ranking = rank_products_by_value([123, 456, 789], 500)
        # Returns: [{"rank": 1, "product_id": 456, "value_score": 0.92, ...}, ...]
    """
    try:
        rankings = []
        
        for product_id in product_ids:
            savings = calculate_savings_potential(product_id, user_xcoin_balance)
            
            if 'error' in savings:
                continue
            
            # Calculate value score
            savings_pct = savings['savings_percentage']
            xcoin_rate = savings['xcoin_value_rate']
            affordable = savings['user_has_enough_popcoins']
            
            # Scoring: 60% savings percentage, 30% popCoin rate, 10% affordability
            value_score = (savings_pct / 100) * 0.6 + (min(xcoin_rate, 10) / 10) * 0.3
            if affordable:
                value_score += 0.1
            
            # Generate recommendation
            if value_score > 0.8:
                rec = "Excellent value! Highly recommended."
            elif value_score > 0.6:
                rec = "Good value for your popCoins."
            elif affordable:
                rec = "Decent deal and you can afford it now."
            else:
                rec = f"Need {savings['popcoins_shortage']} more popCoins."
            
            rankings.append({
                "product_id": product_id,
                "product_title": savings['product_title'],
                "price": savings['selling_price'],
                "popcoins_required": savings['popcoins_required'],
                "savings_percentage": savings_pct,
                "value_score": round(value_score, 3),
                "affordability": affordable,
                "recommendation": rec
            })
        
        # Sort by value score
        rankings.sort(key=lambda x: x['value_score'], reverse=True)
        
        # Add rank
        for i, item in enumerate(rankings, 1):
            item['rank'] = i
        
        return rankings
    except Exception as e:
        return [{"error": f"Error ranking products: {e}"}]



def suggest_challenge_missions(user_id: str) -> List[Dict[str, Any]]:
    """
    Recommend personalized challenges based on user transaction behavior.
    
    Use this tool to suggest challenges that align with what user already
    does, making them easier to complete.
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        List of challenge recommendations:
        - challenge_id: Challenge identifier
        - challenge_name: Challenge name
        - description: What user needs to do
        - reward_popcoins: popCoins earned on completion
        - difficulty: Challenge difficulty
        - match_score: How well challenge matches user behavior (0-1)
        - reason: Why this challenge is recommended
        - action: How to enroll
    
    Example:
        suggestions = suggest_challenge_missions("U000001")
        # Returns: [{"challenge_id": "CH003", "match_score": 0.87, ...}, ...]
    """
    try:
        # Get user's transaction patterns
        patterns = analyze_transaction_patterns(user_id, days=60)
        
        # Get available challenges
        all_challenges = get_challenges(active_only=True)
        
        # Get user's current progress
        user_progress = get_challenge_progress(user_id)
        enrolled_ids = {p['challenge_id'] for p in user_progress}
        
        suggestions = []
        
        for challenge in all_challenges:
            if challenge['challenge_id'] in enrolled_ids:
                continue  # Skip already enrolled
            
            challenge_type = challenge['challenge_type']
            target = challenge['target_value']
            
            # Calculate match score based on user behavior
            match_score = 0.5  # Base score
            reason_parts = []
            
            if challenge_type == "Transaction Count":
                # Check if user typically does this many transactions
                if 'total_transactions' in patterns:
                    avg_monthly_txns = patterns['total_transactions']
                    if avg_monthly_txns >= target:
                        match_score = 0.9
                        reason_parts.append(f"You average {avg_monthly_txns} transactions/month")
                    elif avg_monthly_txns >= target * 0.7:
                        match_score = 0.7
                        reason_parts.append("Within your typical transaction range")
                    else:
                        match_score = 0.4
                        reason_parts.append("Requires more transactions than usual")
            
            elif challenge_type == "Spending Amount":
                # Check against user's spending patterns
                if 'avg_transaction_amount' in patterns:
                    avg_amount = patterns['avg_transaction_amount']
                    required_txns = target / avg_amount if avg_amount > 0 else 999
                    
                    if required_txns <= 5:
                        match_score = 0.9
                        reason_parts.append(f"Just {int(required_txns)} of your typical transactions")
                    elif required_txns <= 10:
                        match_score = 0.7
                        reason_parts.append("Achievable with normal spending")
                    else:
                        match_score = 0.5
                        reason_parts.append("Requires increased spending")
            
            elif challenge_type == "Payment Method":
                # Check if user uses this payment method
                if 'preferred_payment_method' in patterns:
                    preferred = patterns['preferred_payment_method']
                    # Challenge might specify UPI, Card, etc.
                    if preferred in challenge['description']:
                        match_score = 0.95
                        reason_parts.append(f"Uses your preferred method: {preferred}")
                    else:
                        match_score = 0.6
                        reason_parts.append("Try a different payment method")
            
            # Bonus for easy challenges
            if challenge['difficulty'] == "Easy":
                match_score += 0.1
            
            # Cap at 1.0
            match_score = min(match_score, 1.0)
            
            # Build reason string
            reason = "; ".join(reason_parts) if reason_parts else "Good challenge to try"
            
            suggestions.append({
                "challenge_id": challenge['challenge_id'],
                "challenge_name": challenge['challenge_name'],
                "description": challenge['description'],
                "reward_popcoins": challenge['reward_popcoins'],
                "difficulty": challenge['difficulty'],
                "duration_days": challenge['duration_days'],
                "match_score": round(match_score, 2),
                "reason": reason,
                "action": f"enroll_in_challenge('{user_id}', '{challenge['challenge_id']}')"
            })
        
        # Sort by match score
        suggestions.sort(key=lambda x: x['match_score'], reverse=True)
        
        return suggestions[:5]
    except Exception as e:
        return [{"error": f"Error suggesting challenges: {e}"}]


# ============================================================================
# COMPOSITE/HELPER TOOLS (3 additional tools)
# ============================================================================

def get_user_dashboard_summary(user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive dashboard summary for a user.
    
    Use this tool to provide a complete overview of user's account status,
    popCoins, goals, and opportunities in one call.
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        Dictionary containing comprehensive user summary:
        - user_info: Basic user profile
        - xcoin_summary: Balance and earning stats
        - active_goals: Current product goals
        - cart_status: Shopping cart summary
        - challenges: Active challenge progress
        - expiry_alerts: Upcoming popCoin expirations
        - budget_status: Budget utilization
        - top_recommendations: Personalized product recommendations
    
    Example:
        dashboard = get_user_dashboard_summary("U000001")
        # Returns comprehensive user state for AI agent context
    """
    try:
        # Gather all key information
        profile = get_user_profile(user_id)
        balance = get_xcoin_balance(user_id)
        goals = get_user_goals(user_id, status="Active")
        cart = get_shopping_cart(user_id)
        challenges = get_challenge_progress(user_id)
        expiry_risk = predict_expiry_risk(user_id, days_ahead=30)
        budget = get_budget_insights(user_id)
        recommendations = get_product_recommendations(user_id, limit=5)
        
        # Calculate earning rate
        earning_rate = calculate_earning_rate(user_id, days=30)
        
        return {
            "user_id": user_id,
            "user_info": {
                "name": profile.get('name') if profile else "Unknown",
                "location": profile.get('location') if profile else "Unknown",
                "account_status": profile.get('account_status') if profile else "Unknown"
            },
            "xcoin_summary": {
                "current_balance": balance.get('current_balance', 0) if balance else 0,
                "expiring_soon": balance.get('popcoins_expiring_soon', 0) if balance else 0,
                "lifetime_earned": balance.get('total_popcoins_earned', 0) if balance else 0,
                "daily_earning_rate": earning_rate.get('avg_popcoins_per_day', 0)
            },
            "active_goals": len(goals),
            "cart_status": {
                "items_count": len(cart),
                "total_value": sum(item['price'] * item['quantity'] for item in cart)
            },
            "active_challenges": len(challenges),
            "expiry_alerts": {
                "popcoins_at_risk": expiry_risk.get('total_at_risk', 0),
                "urgent": expiry_risk.get('urgent_action_needed', False)
            },
            "budget_status": {
                "utilization_percent": budget.get('budget_utilized_percent', 0) if budget else 0,
                "remaining": budget.get('budget_remaining', 0) if budget else 0
            },
            "top_recommendations": [
                {
                    "product_id": r['product_id'],
                    "title": r['product_title'],
                    "score": r['recommendation_score']
                } for r in recommendations[:3]
            ]
        }
    except Exception as e:
        return {"error": f"Error generating dashboard: {e}"}


def calculate_total_cart_value_with_popcoins(user_id: str) -> Dict[str, Any]:
    """
    Calculate total cart value and potential savings with popCoins.
    
    Use this tool to show user the total cost of their cart and how much
    they can save by using their popCoins at checkout.
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        Dictionary containing cart value analysis:
        - total_items: Number of items in cart
        - total_mrp: Total MRP of all items
        - total_selling_price: Total selling price (with popCoins)
        - total_popcoins_required: Total popCoins needed for all items
        - user_current_popcoins: User's current balance
        - can_afford_full_cart: Whether user has enough popCoins
        - popcoins_shortage: popCoins needed (if insufficient)
        - total_savings_vs_mrp: Total savings vs MRP
        - savings_percentage: Overall discount percentage
        - items_breakdown: Per-item analysis
    
    Example:
        cart_value = calculate_total_cart_value_with_popcoins("U000001")
        # Returns: {"total_selling_price": 2499, "total_savings_vs_mrp": 1500, ...}
    """
    try:
        cart_items = get_shopping_cart(user_id)
        balance_info = get_xcoin_balance(user_id)
        
        if not cart_items:
            return {
                "total_items": 0,
                "message": "Cart is empty"
            }
        
        user_popcoins = balance_info['current_balance'] if balance_info else 0
        
        total_mrp = 0
        total_sp = 0
        total_popcoins_required = 0
        items_breakdown = []
        
        for item in cart_items:
            qty = item['quantity']
            mrp_per_item = item['mrp']
            sp_per_item = item['price']
            popcoins_per_item = item['popcoins_required']
            
            item_total_mrp = mrp_per_item * qty
            item_total_sp = sp_per_item * qty
            item_total_popcoins = popcoins_per_item * qty
            
            total_mrp += item_total_mrp
            total_sp += item_total_sp
            total_popcoins_required += item_total_popcoins
            
            items_breakdown.append({
                "cart_id": item['cart_id'],
                "title": item['title'],
                "quantity": qty,
                "mrp_total": item_total_mrp,
                "price_total": item_total_sp,
                "popcoins_total": item_total_popcoins,
                "savings": item_total_mrp - item_total_sp
            })
        
        total_savings = total_mrp - total_sp
        savings_percentage = (total_savings / total_mrp * 100) if total_mrp > 0 else 0
        can_afford = user_popcoins >= total_popcoins_required
        shortage = max(0, total_popcoins_required - user_popcoins)
        
        return {
            "total_items": len(cart_items),
            "total_mrp": round(total_mrp, 2),
            "total_selling_price": round(total_sp, 2),
            "total_popcoins_required": total_popcoins_required,
            "user_current_popcoins": user_popcoins,
            "can_afford_full_cart": can_afford,
            "popcoins_shortage": shortage,
            "total_savings_vs_mrp": round(total_savings, 2),
            "savings_percentage": round(savings_percentage, 2),
            "items_breakdown": items_breakdown
        }
    except Exception as e:
        return {"error": f"Error calculating cart value: {e}"}


def get_user_activity_summary(user_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Get comprehensive activity summary for a user over a time period.
    
    Use this tool to understand user's recent activity across all dimensions:
    transactions, browsing, purchases, and engagement.
    
    Args:
        user_id: Unique identifier for the user
        days: Number of days to analyze (default: 30)
    
    Returns:
        Dictionary containing activity summary:
        - period_days: Analysis period
        - transaction_activity: Transaction counts and amounts
        - xcoin_activity: popCoins earned and spent
        - browsing_activity: Products viewed and categories explored
        - purchase_activity: Orders placed and delivered
        - engagement_metrics: Challenge participation, goal progress
        - activity_trend: "Active", "Moderate", or "Low"
    
    Example:
        activity = get_user_activity_summary("U000001", days=30)
        # Returns comprehensive activity analysis for user engagement insights
    """
    try:
        # Get transactions
        transactions = get_transaction_history(user_id, days=days)
        successful_txns = [t for t in transactions if t['status'] == 'Success']
        
        # Get browsing history
        browsing = get_browsing_history(user_id, days=days)
        
        # Get purchases
        purchases = get_purchase_history(user_id, limit=100)
        recent_purchases = [
            p for p in purchases 
            if (datetime.now() - (datetime.fromisoformat(p['order_date'].replace('Z', '+00:00')) if isinstance(p['order_date'], str) else p['order_date'])).days <= days
        ]
        
        # Get challenge progress
        challenges = get_challenge_progress(user_id)
        
        # Get goals
        goals = get_user_goals(user_id, status="Active")
        
        # Calculate popCoin activity
        popcoins_earned = sum(t['popcoins_earned'] for t in successful_txns)
        popcoins_spent = sum(p['popcoins_used'] for p in recent_purchases)
        
        # Browsing patterns
        categories_viewed = set(b['category'] for b in browsing)
        products_added_to_cart = sum(1 for b in browsing if b['added_to_cart'])
        
        # Calculate activity level
        activity_score = 0
        if len(successful_txns) >= 10:
            activity_score += 3
        elif len(successful_txns) >= 5:
            activity_score += 2
        elif len(successful_txns) >= 1:
            activity_score += 1
        
        if len(browsing) >= 20:
            activity_score += 2
        elif len(browsing) >= 10:
            activity_score += 1
        
        if len(challenges) > 0:
            activity_score += 1
        
        if len(goals) > 0:
            activity_score += 1
        
        # Determine activity trend
        if activity_score >= 6:
            trend = "Highly Active"
        elif activity_score >= 4:
            trend = "Active"
        elif activity_score >= 2:
            trend = "Moderate"
        else:
            trend = "Low"
        
        return {
            "user_id": user_id,
            "period_days": days,
            "transaction_activity": {
                "total_transactions": len(transactions),
                "successful_transactions": len(successful_txns),
                "total_amount_spent": sum(t['amount'] for t in successful_txns),
                "avg_transaction_amount": sum(t['amount'] for t in successful_txns) / len(successful_txns) if successful_txns else 0
            },
            "xcoin_activity": {
                "popcoins_earned": popcoins_earned,
                "popcoins_spent": popcoins_spent,
                "net_popcoins": popcoins_earned - popcoins_spent
            },
            "browsing_activity": {
                "products_viewed": len(browsing),
                "unique_categories": len(categories_viewed),
                "products_added_to_cart": products_added_to_cart,
                "conversion_rate": (products_added_to_cart / len(browsing) * 100) if browsing else 0
            },
            "purchase_activity": {
                "orders_placed": len(recent_purchases),
                "total_order_value": sum(p['total_amount'] for p in recent_purchases)
            },
            "engagement_metrics": {
                "active_challenges": len(challenges),
                "active_goals": len(goals),
                "completed_challenges": sum(1 for c in challenges if c['is_completed'])
            },
            "activity_trend": trend,
            "activity_score": activity_score
        }
    except Exception as e:
        return {"error": f"Error generating activity summary: {e}"}


# ============================================================================
# TOOL REGISTRY & METADATA
# ============================================================================

# Define all tools with metadata for LLM agent discovery
TOOL_REGISTRY = {
    # Core Data Retrieval Tools
    "get_user_profile": {
        "category": "Core Data",
        "description": "Retrieve user profile information",
        "agents": ["All agents"],
        "complexity": "Low"
    },
    "get_xcoin_balance": {
        "category": "Core Data",
        "description": "Get user's popCoin balance",
        "agents": ["All agents"],
        "complexity": "Low"
    },
    "get_xcoin_ledger": {
        "category": "Core Data",
        "description": "Get detailed popCoin transaction ledger",
        "agents": ["Smart Redemption", "Expiry Manager", "Earnings Optimizer"],
        "complexity": "Medium"
    },
    "get_catalog_products": {
        "category": "Core Data",
        "description": "Search and filter catalog products",
        "agents": ["Catalog Discovery", "Smart Redemption", "Goal Assistant"],
        "complexity": "Medium"
    },
    "get_product_by_id": {
        "category": "Core Data",
        "description": "Get specific product details",
        "agents": ["All agents"],
        "complexity": "Low"
    },
    "get_transaction_history": {
        "category": "Core Data",
        "description": "Retrieve transaction history",
        "agents": ["Earnings Optimizer", "Budget Manager", "Transaction Support"],
        "complexity": "Medium"
    },
    "get_purchase_history": {
        "category": "Core Data",
        "description": "Get purchase order history",
        "agents": ["Budget Manager", "Catalog Discovery"],
        "complexity": "Low"
    },
    "get_browsing_history": {
        "category": "Core Data",
        "description": "Retrieve browsing history",
        "agents": ["Catalog Discovery", "Smart Redemption"],
        "complexity": "Low"
    },
    "get_shopping_cart": {
        "category": "Core Data",
        "description": "Get shopping cart items",
        "agents": ["Cart Recovery", "Smart Redemption"],
        "complexity": "Low"
    },
    "get_user_goals": {
        "category": "Core Data",
        "description": "Retrieve user goals",
        "agents": ["Goal Assistant", "Smart Redemption"],
        "complexity": "Low"
    },
    "get_challenges": {
        "category": "Core Data",
        "description": "Get available challenges",
        "agents": ["Challenges & Missions", "Earnings Optimizer"],
        "complexity": "Low"
    },
    "get_challenge_progress": {
        "category": "Core Data",
        "description": "Get user's challenge progress",
        "agents": ["Challenges & Missions"],
        "complexity": "Low"
    },
    "get_product_recommendations": {
        "category": "Core Data",
        "description": "Get personalized recommendations",
        "agents": ["Catalog Discovery", "Smart Redemption"],
        "complexity": "Medium"
    },
    "get_product_trends": {
        "category": "Core Data",
        "description": "Get trending products",
        "agents": ["Catalog Discovery"],
        "complexity": "Low"
    },
    "get_referrals": {
        "category": "Core Data",
        "description": "Get user's referral information",
        "agents": ["Referral Assistant"],
        "complexity": "Low"
    },
    "get_budget_insights": {
        "category": "Core Data",
        "description": "Get budget tracking insights",
        "agents": ["Budget Manager"],
        "complexity": "Medium"
    },
    "get_notifications": {
        "category": "Core Data",
        "description": "Retrieve user notifications",
        "agents": ["All agents"],
        "complexity": "Low"
    },
    
    # Analytics & Calculation Tools
    "calculate_savings_potential": {
        "category": "Analytics",
        "description": "Calculate savings for a product",
        "agents": ["Smart Redemption", "Cart Recovery"],
        "complexity": "Medium"
    },
    "calculate_earning_rate": {
        "category": "Analytics",
        "description": "Analyze popCoin earning rate",
        "agents": ["Earnings Optimizer", "Goal Assistant"],
        "complexity": "High"
    },
    "calculate_goal_timeline": {
        "category": "Analytics",
        "description": "Estimate timeline to reach goal",
        "agents": ["Goal Assistant"],
        "complexity": "High"
    },
    "find_optimal_redemption": {
        "category": "Analytics",
        "description": "Find best redemption options",
        "agents": ["Smart Redemption", "Expiry Manager"],
        "complexity": "High"
    },
    "analyze_transaction_patterns": {
        "category": "Analytics",
        "description": "Analyze transaction behavior",
        "agents": ["Earnings Optimizer", "Budget Manager", "Challenges & Missions"],
        "complexity": "High"
    },
    "calculate_budget_utilization": {
        "category": "Analytics",
        "description": "Calculate budget usage",
        "agents": ["Budget Manager"],
        "complexity": "Medium"
    },
    "calculate_conversion_value": {
        "category": "Analytics",
        "description": "Calculate popCoin rupee value",
        "agents": ["Smart Redemption", "Budget Manager"],
        "complexity": "Low"
    },
    
    # Action & Update Tools
    "create_user_goal": {
        "category": "Actions",
        "description": "Create product goal",
        "agents": ["Goal Assistant"],
        "complexity": "Medium"
    },
    "update_goal_progress": {
        "category": "Actions",
        "description": "Update goal progress",
        "agents": ["Goal Assistant"],
        "complexity": "Low"
    },
    "create_notification": {
        "category": "Actions",
        "description": "Send user notification",
        "agents": ["All agents"],
        "complexity": "Low"
    },
    "mark_notification_read": {
        "category": "Actions",
        "description": "Mark notification as read",
        "agents": ["All agents"],
        "complexity": "Low"
    },
    "add_to_cart": {
        "category": "Actions",
        "description": "Add product to cart",
        "agents": ["Catalog Discovery", "Smart Redemption", "Goal Assistant"],
        "complexity": "Low"
    },
    "remove_from_cart": {
        "category": "Actions",
        "description": "Remove item from cart",
        "agents": ["Cart Recovery"],
        "complexity": "Low"
    },
    "update_cart_quantity": {
        "category": "Actions",
        "description": "Update cart item quantity",
        "agents": ["Cart Recovery"],
        "complexity": "Low"
    },
    "enroll_in_challenge": {
        "category": "Actions",
        "description": "Enroll in challenge",
        "agents": ["Challenges & Missions"],
        "complexity": "Medium"
    },
    "generate_referral_code": {
        "category": "Actions",
        "description": "Generate referral code",
        "agents": ["Referral Assistant"],
        "complexity": "Low"
    },
    "update_budget_alert": {
        "category": "Actions",
        "description": "Update budget alert settings",
        "agents": ["Budget Manager"],
        "complexity": "Low"
    },
    
    # Intelligence & Recommendation Tools
    "get_alternative_products": {
        "category": "Intelligence",
        "description": "Find alternative products",
        "agents": ["Catalog Discovery", "Goal Assistant"],
        "complexity": "High"
    },
    "predict_expiry_risk": {
        "category": "Intelligence",
        "description": "Identify expiring popCoins",
        "agents": ["Expiry Manager"],
        "complexity": "High"
    },
    "suggest_earning_opportunities": {
        "category": "Intelligence",
        "description": "Recommend earning strategies",
        "agents": ["Earnings Optimizer"],
        "complexity": "High"
    },
    "detect_cart_abandonment": {
        "category": "Intelligence",
        "description": "Detect abandoned cart",
        "agents": ["Cart Recovery"],
        "complexity": "Medium"
    },
    "rank_products_by_value": {
        "category": "Intelligence",
        "description": "Rank products by value",
        "agents": ["Smart Redemption", "Catalog Discovery"],
        "complexity": "High"
    },
    "suggest_challenge_missions": {
        "category": "Intelligence",
        "description": "Recommend personalized challenges",
        "agents": ["Challenges & Missions", "Earnings Optimizer"],
        "complexity": "High"
    },
    
    # Composite Helper Tools
    "get_user_dashboard_summary": {
        "category": "Composite",
        "description": "Get complete user dashboard",
        "agents": ["Master Orchestrator"],
        "complexity": "High"
    },
    "calculate_total_cart_value_with_popcoins": {
        "category": "Composite",
        "description": "Calculate cart total with popCoins",
        "agents": ["Cart Recovery", "Smart Redemption"],
        "complexity": "Medium"
    },
    "get_user_activity_summary": {
        "category": "Composite",
        "description": "Get user activity summary",
        "agents": ["Master Orchestrator", "Budget Manager"],
        "complexity": "High"
    }
}


def get_tools_for_agent(agent_name: str) -> List[str]:
    """
    Get list of recommended tools for a specific agent.
    
    Args:
        agent_name: Name of the agent (e.g., "Smart Redemption Advisor")
    
    Returns:
        List of tool function names recommended for this agent
    """
    recommended_tools = []
    
    for tool_name, metadata in TOOL_REGISTRY.items():
        agents = metadata.get('agents', [])
        if agent_name in agents or "All agents" in agents:
            recommended_tools.append(tool_name)
    
    return recommended_tools


def print_tool_documentation():
    """Print formatted documentation for all tools."""
    print("=" * 80)
    print("PopCash MCP Tools Library - Complete Documentation")
    print("=" * 80)
    print(f"\nTotal Tools: {len(TOOL_REGISTRY)}")
    
    categories = {}
    for tool_name, metadata in TOOL_REGISTRY.items():
        category = metadata['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(tool_name)
    
    for category, tools in categories.items():
        print(f"\n{category} ({len(tools)} tools):")
        for tool in tools:
            print(f"  - {tool}")
    
    print("\n" + "=" * 80)

# ============================================================================
# REVERSE TOOL REGISTRY: AGENTS -> TOOLS MAPPING
# ============================================================================

AGENT_TOOL_MAPPING = {
    "Smart Redemption Advisor": [
        "get_user_profile",
        "get_xcoin_balance",
        "get_xcoin_ledger",
        "get_catalog_products",
        "get_product_by_id",
        "get_browsing_history",
        "get_shopping_cart",
        "get_user_goals",
        "get_product_recommendations",
        "get_product_trends",
        "get_notifications",
        "calculate_savings_potential",
        "find_optimal_redemption",
        "calculate_conversion_value",
        "create_notification",
        "mark_notification_read",
        "add_to_cart",
        "rank_products_by_value",
        "calculate_total_cart_value_with_popcoins"
    ],
    
    "Personalized Earnings Optimizer": [
        "get_user_profile",
        "get_xcoin_balance",
        "get_xcoin_ledger",
        "get_product_by_id",
        "get_transaction_history",
        "get_challenges",
        "get_challenge_progress",
        "get_notifications",
        "calculate_earning_rate",
        "analyze_transaction_patterns",
        "create_notification",
        "mark_notification_read",
        "suggest_earning_opportunities",
        "suggest_challenge_missions"
    ],
    
    "Goal-Based Shopping Assistant": [
        "get_user_profile",
        "get_xcoin_balance",
        "get_catalog_products",
        "get_product_by_id",
        "get_user_goals",
        "get_notifications",
        "calculate_earning_rate",
        "calculate_goal_timeline",
        "create_user_goal",
        "update_goal_progress",
        "create_notification",
        "mark_notification_read",
        "add_to_cart",
        "get_alternative_products"
    ],
    
    "Transaction Troubleshooting & Support": [
        "get_user_profile",
        "get_xcoin_balance",
        "get_xcoin_ledger",
        "get_product_by_id",
        "get_transaction_history",
        "get_purchase_history",
        "get_notifications",
        "create_notification",
        "mark_notification_read"
    ],
    
    "Catalog Discovery & Trend Insights": [
        "get_user_profile",
        "get_xcoin_balance",
        "get_catalog_products",
        "get_product_by_id",
        "get_browsing_history",
        "get_purchase_history",
        "get_product_recommendations",
        "get_product_trends",
        "get_notifications",
        "create_notification",
        "mark_notification_read",
        "add_to_cart",
        "get_alternative_products",
        "rank_products_by_value"
    ],
    
    "Budget Manager & Spending Insights": [
        "get_user_profile",
        "get_xcoin_balance",
        "get_product_by_id",
        "get_transaction_history",
        "get_purchase_history",
        "get_budget_insights",
        "get_notifications",
        "analyze_transaction_patterns",
        "calculate_budget_utilization",
        "calculate_conversion_value",
        "create_notification",
        "mark_notification_read",
        "update_budget_alert",
        "get_user_activity_summary"
    ],
    
    "Referral Program Assistant": [
        "get_user_profile",
        "get_xcoin_balance",
        "get_product_by_id",
        "get_referrals",
        "get_notifications",
        "create_notification",
        "mark_notification_read",
        "generate_referral_code"
    ],
    
    "Cart Abandonment Recovery": [
        "get_user_profile",
        "get_xcoin_balance",
        "get_catalog_products",
        "get_product_by_id",
        "get_shopping_cart",
        "get_notifications",
        "calculate_savings_potential",
        "create_notification",
        "mark_notification_read",
        "remove_from_cart",
        "update_cart_quantity",
        "detect_cart_abandonment",
        "calculate_total_cart_value_with_popcoins"
    ],
    
    "popCoin Expiry Manager": [
        "get_user_profile",
        "get_xcoin_balance",
        "get_xcoin_ledger",
        "get_catalog_products",
        "get_product_by_id",
        "get_notifications",
        "find_optimal_redemption",
        "create_notification",
        "mark_notification_read",
        "predict_expiry_risk"
    ],
    
    "Gamified Challenges & Missions": [
        "get_user_profile",
        "get_xcoin_balance",
        "get_product_by_id",
        "get_transaction_history",
        "get_challenges",
        "get_challenge_progress",
        "get_notifications",
        "analyze_transaction_patterns",
        "create_notification",
        "mark_notification_read",
        "enroll_in_challenge",
        "suggest_challenge_missions"
    ],
    
    "Master Orchestrator": [
        "get_user_profile",
        "get_xcoin_balance",
        "get_xcoin_ledger",
        "get_catalog_products",
        "get_product_by_id",
        "get_transaction_history",
        "get_purchase_history",
        "get_browsing_history",
        "get_shopping_cart",
        "get_user_goals",
        "get_challenges",
        "get_challenge_progress",
        "get_product_recommendations",
        "get_product_trends",
        "get_referrals",
        "get_budget_insights",
        "get_notifications",
        "calculate_savings_potential",
        "calculate_earning_rate",
        "calculate_goal_timeline",
        "find_optimal_redemption",
        "analyze_transaction_patterns",
        "calculate_budget_utilization",
        "calculate_conversion_value",
        "create_user_goal",
        "update_goal_progress",
        "create_notification",
        "mark_notification_read",
        "add_to_cart",
        "remove_from_cart",
        "update_cart_quantity",
        "enroll_in_challenge",
        "generate_referral_code",
        "update_budget_alert",
        "get_alternative_products",
        "predict_expiry_risk",
        "suggest_earning_opportunities",
        "detect_cart_abandonment",
        "rank_products_by_value",
        "suggest_challenge_missions",
        "get_user_dashboard_summary",
        "calculate_total_cart_value_with_popcoins",
        "get_user_activity_summary"
    ]
}


# ============================================================================
# AGENT TOOL STATISTICS
# ============================================================================

AGENT_TOOL_STATS = {
    "Smart Redemption Advisor": {
        "total_tools": 19,
        "core_data_tools": 11,
        "analytics_tools": 3,
        "action_tools": 3,
        "intelligence_tools": 1,
        "composite_tools": 1
    },
    "Personalized Earnings Optimizer": {
        "total_tools": 14,
        "core_data_tools": 8,
        "analytics_tools": 2,
        "action_tools": 2,
        "intelligence_tools": 2,
        "composite_tools": 0
    },
    "Goal-Based Shopping Assistant": {
        "total_tools": 14,
        "core_data_tools": 6,
        "analytics_tools": 2,
        "action_tools": 4,
        "intelligence_tools": 1,
        "composite_tools": 0
    },
    "Transaction Troubleshooting & Support": {
        "total_tools": 9,
        "core_data_tools": 6,
        "analytics_tools": 0,
        "action_tools": 2,
        "intelligence_tools": 0,
        "composite_tools": 0
    },
    "Catalog Discovery & Trend Insights": {
        "total_tools": 14,
        "core_data_tools": 8,
        "analytics_tools": 0,
        "action_tools": 3,
        "intelligence_tools": 2,
        "composite_tools": 0
    },
    "Budget Manager & Spending Insights": {
        "total_tools": 14,
        "core_data_tools": 7,
        "analytics_tools": 3,
        "action_tools": 3,
        "intelligence_tools": 0,
        "composite_tools": 1
    },
    "Referral Program Assistant": {
        "total_tools": 8,
        "core_data_tools": 4,
        "analytics_tools": 0,
        "action_tools": 3,
        "intelligence_tools": 0,
        "composite_tools": 0
    },
    "Cart Abandonment Recovery": {
        "total_tools": 13,
        "core_data_tools": 6,
        "analytics_tools": 1,
        "action_tools": 4,
        "intelligence_tools": 1,
        "composite_tools": 1
    },
    "popCoin Expiry Manager": {
        "total_tools": 10,
        "core_data_tools": 6,
        "analytics_tools": 1,
        "action_tools": 2,
        "intelligence_tools": 1,
        "composite_tools": 0
    },
    "Gamified Challenges & Missions": {
        "total_tools": 12,
        "core_data_tools": 7,
        "analytics_tools": 1,
        "action_tools": 3,
        "intelligence_tools": 1,
        "composite_tools": 0
    },
    "Master Orchestrator": {
        "total_tools": 43,
        "core_data_tools": 17,
        "analytics_tools": 7,
        "action_tools": 10,
        "intelligence_tools": 6,
        "composite_tools": 3
    }
}


# ============================================================================
# JSON FORMATTED OUTPUT
# ============================================================================

import json

# Pretty print the agent-to-tools mapping
print("=" * 80)
print("AGENT -> TOOLS MAPPING (JSON)")
print("=" * 80)
print(json.dumps(AGENT_TOOL_MAPPING, indent=2))

print("\n" + "=" * 80)
print("AGENT TOOL STATISTICS (JSON)")
print("=" * 80)
print(json.dumps(AGENT_TOOL_STATS, indent=2))

# Summary table
print("\n" + "=" * 80)
print("SUMMARY TABLE")
print("=" * 80)
print(f"{'Agent Name':<40} {'Total Tools':<15} {'Specialization'}")
print("-" * 80)

for agent, tools in AGENT_TOOL_MAPPING.items():
    stats = AGENT_TOOL_STATS[agent]
    specialization = max(
        [
            ("Core Data", stats['core_data_tools']),
            ("Analytics", stats['analytics_tools']),
            ("Actions", stats['action_tools']),
            ("Intelligence", stats['intelligence_tools'])
        ],
        key=lambda x: x[1]
    )[0]
    print(f"{agent:<40} {stats['total_tools']:<15} {specialization}")

print("=" * 80)

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print_tool_documentation()
    
    print("\n\nExample: Get tools for Smart Redemption Advisor")
    tools = get_tools_for_agent("Smart Redemption")
    print(f"Recommended tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool}")
    
    print("\n\nExample: Test get_user_profile")
    profile = get_user_profile("U000001")
    if profile:
        print(f"User: {profile.get('name')}")
        print(f"Balance check...")
        balance = get_xcoin_balance("U000001")
        if balance:
            print(f"Current popCoins: {balance['current_balance']}")
    
    print("\n\nExample: Calculate savings potential")
    savings = calculate_savings_potential(41030, 536)
    if 'product_title' in savings:
        print(f"Product: {savings['product_title']}")
        print(f"Savings: ₹{savings['savings_amount']} ({savings['savings_percentage']}%)")
        print(f"Can afford: {savings['user_has_enough_popcoins']}")
    
    print("\n\nExample: Find optimal redemption")
    options = find_optimal_redemption(500, category="Fashion", limit=3)
    print(f"Top 3 redemption options:")
    for opt in options:
        if 'product_title' in opt:
            print(f"  - {opt['product_title']}: {opt['savings_percentage']:.1f}% off, Score: {opt['value_efficiency_score']}")
