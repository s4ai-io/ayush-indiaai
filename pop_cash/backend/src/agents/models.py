"""
Pydantic models for all CSV datasets in the backend/dataset folder.
Auto-generated based on CSV schema analysis.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal


# ==================== User Profile Models ====================

class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    age: int
    gender: str
    location: str
    registration_date: date
    preferred_categories: str  # Stored as string representation of list
    account_status: str
    phone_number: str

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "U000001",
                "name": "John Doe",
                "email": "john@example.com",
                "age": 28,
                "gender": "Male",
                "location": "Mumbai",
                "registration_date": "2025-01-15",
                "preferred_categories": "['Electronics', 'Fashion']",
                "account_status": "Active",
                "phone_number": "+91-9876543210"
            }
        }


# ==================== Browsing History Models ====================

class BrowsingHistory(BaseModel):
    browse_id: str
    user_id: str
    product_id: int
    category: str
    brand: str
    view_timestamp: str
    time_spent_seconds: int
    added_to_cart: bool
    source: str

    class Config:
        json_schema_extra = {
            "example": {
                "browse_id": "BRW000001",
                "user_id": "U000001",
                "product_id": 41030,
                "category": "Snack Time",
                "brand": "Ambrosia",
                "view_timestamp": "2025-11-05T14:23:45",
                "time_spent_seconds": 45,
                "added_to_cart": True,
                "source": "Search"
            }
        }


# ==================== Catalog Models ====================

class CatalogProduct(BaseModel):
    actual_product_id: Optional[str] = None
    structure: Optional[str] = None
    title: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    style_code: Optional[str] = None
    vendor_sku_code: Optional[str] = None
    ideal_for: Optional[str] = None
    size_chart: Optional[str] = None
    category_name: Optional[str] = None
    sp: Optional[float] = None  # Selling price
    mrp: Optional[float] = None  # Maximum retail price
    coins_earn: Optional[int] = None
    coins_burn: Optional[int] = None
    brand_name: Optional[str] = None
    id: Optional[str] = None
    age_group: Optional[str] = None
    occasion: Optional[str] = None
    material: Optional[str] = None
    material_care: Optional[str] = None
    pattern: Optional[str] = None
    fit: Optional[str] = None
    length: Optional[str] = None
    neck: Optional[str] = None
    sleeve_length: Optional[str] = None
    style: Optional[str] = None
    waist: Optional[str] = None
    closure: Optional[str] = None
    size_and_fit: Optional[str] = None
    features: Optional[str] = None
    skin_type: Optional[str] = None
    hair_type: Optional[str] = None
    pack_size: Optional[str] = None
    preference: Optional[str] = None
    pack_quantity: Optional[str] = None
    package_contents: Optional[str] = None
    date_created: Optional[str] = None
    date_updated: Optional[str] = None
    product_id: Optional[str] = None
    container_type: Optional[str] = None
    country_of_origin: Optional[str] = None
    dosage: Optional[str] = None
    flavour: Optional[str] = None
    food_preference: Optional[str] = None
    food_type: Optional[str] = None
    heel_pattern: Optional[str] = None
    how_to_use: Optional[str] = None
    ingredients: Optional[str] = None
    instructions: Optional[str] = None
    is_organic: Optional[bool] = None
    model: Optional[str] = None
    mounting_type: Optional[str] = None
    nutrition_content: Optional[str] = None
    other_details: Optional[str] = None
    outer_material: Optional[str] = None
    professional_care: Optional[str] = None
    protein_type: Optional[str] = None
    quality: Optional[str] = None
    shade: Optional[str] = None
    shape: Optional[str] = None
    shelf_life: Optional[str] = None
    shoes_fastening: Optional[str] = None
    shoes_type: Optional[str] = None
    sole_material: Optional[str] = None
    treatment_form: Optional[str] = None
    weave_type: Optional[str] = None
    weight: Optional[str] = None
    product_rank: Optional[int] = None
    dim_breadth: Optional[float] = None
    dim_height: Optional[float] = None
    dim_length: Optional[float] = None
    shipping_weight: Optional[float] = None
    shipping_weight_type: Optional[str] = None
    importer_address: Optional[str] = None
    manufacturer_address: Optional[str] = None
    color_relation_json: Optional[str] = None
    catalogue_rank: Optional[int] = None
    weightage_score: Optional[float] = None
    rank_type: Optional[str] = None
    compatible_devices: Optional[str] = None
    warranty: Optional[str] = None
    warranty_type: Optional[str] = None
    image_list: Optional[str] = None


# ==================== Challenge Models ====================

class Challenge(BaseModel):
    challenge_id: str
    challenge_name: str
    description: str
    challenge_type: str
    target_value: int
    reward_popcoins: int
    duration_days: int
    start_date: date
    end_date: date
    is_active: bool
    difficulty: str

    class Config:
        json_schema_extra = {
            "example": {
                "challenge_id": "CH001",
                "challenge_name": "Weekend Warrior",
                "description": "Complete 3 payments this weekend",
                "challenge_type": "Transaction Count",
                "target_value": 3,
                "reward_popcoins": 100,
                "duration_days": 2,
                "start_date": "2025-12-02",
                "end_date": "2025-12-04",
                "is_active": True,
                "difficulty": "Easy"
            }
        }


# ==================== Notification Models ====================

class Notification(BaseModel):
    notification_id: str
    user_id: str
    notification_type: str
    title: str
    message: str
    sent_at: str
    is_read: bool
    read_at: Optional[str] = None
    clicked: bool
    channel: str
    priority: str

    class Config:
        json_schema_extra = {
            "example": {
                "notification_id": "NOTIF00000001",
                "user_id": "U000001",
                "notification_type": "Challenge Update",
                "title": "Challenge Update",
                "message": "You're 67% through your challenge!",
                "sent_at": "2025-12-01T10:10:40",
                "is_read": True,
                "read_at": "2025-11-07T17:10:40",
                "clicked": True,
                "channel": "In-App",
                "priority": "Medium"
            }
        }


# ==================== Product Recommendation Models ====================

class ProductRecommendation(BaseModel):
    recommendation_id: str
    user_id: str
    product_id: int
    product_title: str
    category: str
    brand: str
    recommendation_score: float
    recommendation_reason: str
    recommended_at: str
    clicked: bool
    purchased: bool

    class Config:
        json_schema_extra = {
            "example": {
                "recommendation_id": "REC00000001",
                "user_id": "U000001",
                "product_id": 1012775,
                "product_title": "Wall Hanging Decor",
                "category": "Wall Accents",
                "brand": "PRAKRITI",
                "recommendation_score": 0.92,
                "recommendation_reason": "Trending now",
                "recommended_at": "2025-12-02T18:10:21",
                "clicked": False,
                "purchased": False
            }
        }


# ==================== Product Trends Models ====================

class ProductTrend(BaseModel):
    product_id: int
    product_title: str
    category: str
    brand: str
    views_last_7days: int
    views_last_30days: int
    add_to_cart_count: int
    purchase_count: int
    conversion_rate: float
    avg_rating: float
    num_reviews: int
    trending_score: float
    stock_level: str
    last_updated: str

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 41030,
                "product_title": "Roasted & Lightly Salted California Pistachio",
                "category": "Snack Time",
                "brand": "Ambrosia",
                "views_last_7days": 128,
                "views_last_30days": 2080,
                "add_to_cart_count": 26,
                "purchase_count": 22,
                "conversion_rate": 24.67,
                "avg_rating": 4.8,
                "num_reviews": 328,
                "trending_score": 0.93,
                "stock_level": "Medium",
                "last_updated": "2025-12-03T17:10:40"
            }
        }


# ==================== Purchase History Models ====================

class PurchaseHistoryItem(BaseModel):
    """Individual item in a purchase order"""
    product_id: int
    title: str
    quantity: int
    price: float


class PurchaseHistory(BaseModel):
    order_id: str
    user_id: str
    order_date: str
    num_items: int
    total_amount: float
    popcoins_used: int
    payment_method: str
    order_status: str
    delivery_date: Optional[date] = None
    items: str  # JSON string containing list of items

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ORD00000001",
                "user_id": "U000001",
                "order_date": "2025-11-05T14:30:00",
                "num_items": 2,
                "total_amount": 1299.50,
                "popcoins_used": 50,
                "payment_method": "UPI",
                "order_status": "Delivered",
                "delivery_date": "2025-11-08",
                "items": '[{"product_id": 41030, "title": "Pistachio", "quantity": 1, "price": 347.0}]'
            }
        }


# ==================== Referral Tracking Models ====================

class ReferralTracking(BaseModel):
    referral_id: str
    referrer_user_id: str
    referred_user_id: str
    referral_code: str
    signup_date: date
    first_payment_completed: bool
    first_payment_date: Optional[date] = None
    referrer_reward_popcoins: int
    referred_reward_popcoins: int
    reward_credited: bool
    reward_credit_date: Optional[date] = None
    status: str

    class Config:
        json_schema_extra = {
            "example": {
                "referral_id": "REF00000001",
                "referrer_user_id": "U000001",
                "referred_user_id": "U000192",
                "referral_code": "REFU000001",
                "signup_date": "2025-11-29",
                "first_payment_completed": False,
                "first_payment_date": None,
                "referrer_reward_popcoins": 0,
                "referred_reward_popcoins": 0,
                "reward_credited": False,
                "reward_credit_date": None,
                "status": "Pending"
            }
        }


# ==================== Shopping Cart Models ====================

class ShoppingCart(BaseModel):
    cart_id: str
    user_id: str
    product_id: int
    title: str
    category: str
    brand: str
    quantity: int
    price: float
    mrp: float
    popcoins_required: int
    added_at: str
    is_available: bool
    price_changed: bool

    class Config:
        json_schema_extra = {
            "example": {
                "cart_id": "CART00000001",
                "user_id": "U000001",
                "product_id": 41030,
                "title": "Pistachio Snack",
                "category": "Snack Time",
                "brand": "Ambrosia",
                "quantity": 2,
                "price": 347.0,
                "mrp": 525.0,
                "popcoins_required": 35,
                "added_at": "2025-11-05T14:23:45",
                "is_available": True,
                "price_changed": False
            }
        }


# ==================== Transaction History Models ====================

class TransactionHistory(BaseModel):
    transaction_id: str
    user_id: str
    transaction_type: str
    amount: float
    transaction_date: str
    payment_method: str
    status: str
    popcoins_earned: int
    vendor_name: Optional[str] = None
    category: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "TXN00000001",
                "user_id": "U000001",
                "transaction_type": "Purchase",
                "amount": 1450.75,
                "transaction_date": "2025-10-11T10:30:15",
                "payment_method": "Credit Card",
                "status": "Success",
                "popcoins_earned": 29,
                "vendor_name": "Amazon",
                "category": "Electronics"
            }
        }


# ==================== User Budget Insights Models ====================

class UserBudgetInsights(BaseModel):
    user_id: str
    monthly_budget_limit: float
    current_month_spend: float
    budget_remaining: float
    budget_utilized_percent: float
    alert_threshold: int
    alert_enabled: bool
    category_spending: str  # JSON string with category-wise spending
    top_spending_category: str
    avg_transaction_value: float
    popcoins_saved_this_month: int
    last_updated: str

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "U000001",
                "monthly_budget_limit": 5000.0,
                "current_month_spend": 37663.24,
                "budget_remaining": -32663.24,
                "budget_utilized_percent": 753.26,
                "alert_threshold": 75,
                "alert_enabled": True,
                "category_spending": '{"Electronics": 2009.14, "Entertainment": 12331.75}',
                "top_spending_category": "Utilities",
                "avg_transaction_value": 2665.13,
                "popcoins_saved_this_month": 315,
                "last_updated": "2025-12-03T17:10:02"
            }
        }


# ==================== User Challenge Progress Models ====================

class UserChallengeProgress(BaseModel):
    progress_id: str
    user_id: str
    challenge_id: str
    challenge_name: str
    current_progress: int
    target_value: int
    progress_percentage: float
    is_completed: bool
    popcoins_earned: int
    started_at: date
    completed_at: Optional[date] = None
    last_updated: str

    class Config:
        json_schema_extra = {
            "example": {
                "progress_id": "PROG00000001",
                "user_id": "U000001",
                "challenge_id": "CH004",
                "challenge_name": "Big Spender",
                "current_progress": 2457,
                "target_value": 5000,
                "progress_percentage": 49.14,
                "is_completed": False,
                "popcoins_earned": 0,
                "started_at": "2025-12-01",
                "completed_at": None,
                "last_updated": "2025-12-03T17:09:45"
            }
        }


# ==================== User Goals Models ====================

class UserGoal(BaseModel):
    goal_id: str
    user_id: str
    product_id: int
    product_title: str
    target_popcoins: int
    current_popcoins: int
    popcoins_needed: int
    target_price: float
    estimated_days: int
    created_at: date
    target_date: date
    status: str
    notification_enabled: bool

    class Config:
        json_schema_extra = {
            "example": {
                "goal_id": "GOAL00000001",
                "user_id": "U000001",
                "product_id": 41030,
                "product_title": "Roasted & Lightly Salted California Pistachio",
                "target_popcoins": 35,
                "current_popcoins": 536,
                "popcoins_needed": 0,
                "target_price": 347.0,
                "estimated_days": 29,
                "created_at": "2025-11-04",
                "target_date": "2025-12-27",
                "status": "Active",
                "notification_enabled": True
            }
        }


# ==================== User PopCoin Balance Models ====================

class UserPopCoinBalance(BaseModel):
    user_id: str
    total_popcoins_earned: int
    total_popcoins_spent: int
    current_balance: int
    popcoins_expiring_soon: int
    last_earned_date: str
    last_updated: str

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "U000001",
                "total_popcoins_earned": 850,
                "total_popcoins_spent": 314,
                "current_balance": 536,
                "popcoins_expiring_soon": 88,
                "last_earned_date": "2025-11-29T17:08:37",
                "last_updated": "2025-12-03T17:08:53"
            }
        }


# ==================== PopCoin Ledger Models ====================

class PopCoinLedger(BaseModel):
    ledger_id: str
    user_id: str
    transaction_id: str
    popcoins_earned: int
    popcoins_spent: int
    popcoins_balance: int
    earned_date: str
    expiry_date: date
    spent_date: Optional[date] = None
    is_expired: bool
    status: str

    class Config:
        json_schema_extra = {
            "example": {
                "ledger_id": "LED00000001",
                "user_id": "U000001",
                "transaction_id": "TXN00000001",
                "popcoins_earned": 29,
                "popcoins_spent": 0,
                "popcoins_balance": 29,
                "earned_date": "2025-10-11T17:08:37",
                "expiry_date": "2026-01-09",
                "spent_date": None,
                "is_expired": False,
                "status": "Active"
            }
        }
