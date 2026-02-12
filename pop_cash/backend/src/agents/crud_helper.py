"""
CRUD Operations Helper for CSV-based Data Management
Provides generic CRUD operations for all Pydantic models with CSV storage.
"""

import csv
import os
from pathlib import Path
from typing import TypeVar, Generic, List, Optional, Dict, Any, Callable
from pydantic import BaseModel, ValidationError
from datetime import datetime, date
import json

from src.agents.models import (
    UserProfile, BrowsingHistory, CatalogProduct, Challenge, Notification,
    ProductRecommendation, ProductTrend, PurchaseHistory, ReferralTracking,
    ShoppingCart, TransactionHistory, UserBudgetInsights, UserChallengeProgress,
    UserGoal, UserPopCoinBalance, PopCoinLedger
)

T = TypeVar('T', bound=BaseModel)

# Dataset directory path
DATASET_DIR = Path(__file__).parent.parent / "dataset"

class CSVCRUDException(Exception):
    """Custom exception for CSV CRUD operations"""
    pass


class CSVHandler(Generic[T]):
    """Generic CSV CRUD handler for Pydantic models"""
    
    def __init__(self, model_class: type[T], csv_filename: str, id_field: str = "id"):
        """
        Initialize CSV handler
        
        Args:
            model_class: Pydantic model class
            csv_filename: Name of the CSV file in dataset directory
            id_field: Name of the ID field for the model
        """
        self.model_class = model_class
        self.csv_path = DATASET_DIR / csv_filename
        self.id_field = id_field
        
        # Ensure CSV file exists
        if not self.csv_path.exists():
            raise CSVCRUDException(f"CSV file not found: {self.csv_path}")
    
    def _parse_value(self, value: str, field_type: type) -> Any:
        """Parse CSV string value to appropriate Python type"""
        if value == "" or value is None:
            return None
        
        # Handle boolean
        if field_type == bool:
            return value.lower() in ('true', '1', 'yes')
        
        # Handle datetime
        if field_type == datetime:
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        
        # Handle date
        if field_type == date:
            return datetime.strptime(value, '%Y-%m-%d').date()
        
        # Handle numeric types
        if field_type == int:
            return int(float(value))  # Handle cases like "1.0"
        
        if field_type == float:
            return float(value)
        
        # Default to string
        return value
    
    def _convert_to_csv_value(self, value: Any) -> str:
        """Convert Python value to CSV string"""
        if value is None:
            return ""
        
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        
        if isinstance(value, bool):
            return str(value)
        
        return str(value)
    
    def read_all(self, skip: int = 0, limit: Optional[int] = None) -> List[T]:
        """
        Read all records from CSV
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
        """
        records = []
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for idx, row in enumerate(reader):
                    if idx < skip:
                        continue
                    
                    if limit and len(records) >= limit:
                        break
                    
                    try:
                        # Parse values according to model fields
                        parsed_row = {}
                        for field_name, field_info in self.model_class.model_fields.items():
                            if field_name in row:
                                try:
                                    field_type = field_info.annotation
                                    # Handle Optional types
                                    if hasattr(field_type, '__origin__') and field_type.__origin__ is type(Optional):
                                        field_type = field_type.__args__[0]
                                    parsed_row[field_name] = self._parse_value(row[field_name], field_type)
                                except Exception as e:
                                    print(f"Error parsing field {field_name}: {e}")
                                    parsed_row[field_name] = None
                        
                        record = self.model_class(**parsed_row)
                        records.append(record)
                    except ValidationError as e:
                        print(f"Validation error for row {idx}: {e}")
                        continue
        
        except Exception as e:
            raise CSVCRUDException(f"Error reading CSV file: {str(e)}")
        
        return records
    
    def read_by_id(self, record_id: Any) -> Optional[T]:
        """
        Read a single record by ID
        
        Args:
            record_id: ID value to search for
            
        Returns:
            Model instance or None if not found
        """
        records = self.filter_by(**{self.id_field: record_id})
        return records[0] if records else None
    
    def filter_by(self, **filters) -> List[T]:
        """
        Filter records by field values
        
        Args:
            **filters: Field name and value pairs to filter by
            
        Returns:
            List of matching model instances
        """
        all_records = self.read_all()
        
        filtered = []
        for record in all_records:
            match = True
            for field, value in filters.items():
                if getattr(record, field, None) != value:
                    match = False
                    break
            
            if match:
                filtered.append(record)
        
        return filtered
    
    def search(self, predicate: Callable[[T], bool]) -> List[T]:
        """
        Search records using a custom predicate function
        
        Args:
            predicate: Function that takes a record and returns True/False
            
        Returns:
            List of matching model instances
        """
        all_records = self.read_all()
        return [record for record in all_records if predicate(record)]
    
    def create(self, record: T) -> T:
        """
        Create a new record in CSV
        
        Args:
            record: Model instance to create
            
        Returns:
            Created model instance
        """
        try:
            # Read existing records
            existing_records = self.read_all()
            
            # Check if ID already exists
            record_id = getattr(record, self.id_field)
            if any(getattr(r, self.id_field) == record_id for r in existing_records):
                raise CSVCRUDException(f"Record with {self.id_field}={record_id} already exists")
            
            # Append new record
            existing_records.append(record)
            
            # Write back to CSV
            self._write_all(existing_records)
            
            return record
        
        except Exception as e:
            raise CSVCRUDException(f"Error creating record: {str(e)}")
    
    def update(self, record_id: Any, updates: Dict[str, Any]) -> Optional[T]:
        """
        Update a record by ID
        
        Args:
            record_id: ID of the record to update
            updates: Dictionary of field names and new values
            
        Returns:
            Updated model instance or None if not found
        """
        try:
            # Read all records
            records = self.read_all()
            
            # Find and update the record
            updated_record = None
            for idx, record in enumerate(records):
                if getattr(record, self.id_field) == record_id:
                    # Create updated record
                    record_dict = record.model_dump()
                    record_dict.update(updates)
                    updated_record = self.model_class(**record_dict)
                    records[idx] = updated_record
                    break
            
            if updated_record is None:
                return None
            
            # Write back to CSV
            self._write_all(records)
            
            return updated_record
        
        except Exception as e:
            raise CSVCRUDException(f"Error updating record: {str(e)}")
    
    def delete(self, record_id: Any) -> bool:
        """
        Delete a record by ID
        
        Args:
            record_id: ID of the record to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            # Read all records
            records = self.read_all()
            
            # Filter out the record to delete
            initial_count = len(records)
            records = [r for r in records if getattr(r, self.id_field) != record_id]
            
            if len(records) == initial_count:
                return False  # Record not found
            
            # Write back to CSV
            self._write_all(records)
            
            return True
        
        except Exception as e:
            raise CSVCRUDException(f"Error deleting record: {str(e)}")
    
    def bulk_create(self, records: List[T]) -> List[T]:
        """
        Create multiple records at once
        
        Args:
            records: List of model instances to create
            
        Returns:
            List of created model instances
        """
        try:
            existing_records = self.read_all()
            
            # Check for duplicate IDs
            existing_ids = {getattr(r, self.id_field) for r in existing_records}
            for record in records:
                record_id = getattr(record, self.id_field)
                if record_id in existing_ids:
                    raise CSVCRUDException(f"Duplicate {self.id_field}: {record_id}")
            
            # Append new records
            existing_records.extend(records)
            
            # Write back to CSV
            self._write_all(existing_records)
            
            return records
        
        except Exception as e:
            raise CSVCRUDException(f"Error bulk creating records: {str(e)}")
    
    def count(self, **filters) -> int:
        """
        Count records matching filters
        
        Args:
            **filters: Field name and value pairs to filter by
            
        Returns:
            Count of matching records
        """
        if filters:
            return len(self.filter_by(**filters))
        return len(self.read_all())
    
    def _write_all(self, records: List[T]) -> None:
        """Write all records to CSV file"""
        if not records:
            # Keep header only
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
            
            with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            return
        
        # Get fieldnames from model
        fieldnames = list(self.model_class.model_fields.keys())
        
        with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in records:
                row = {}
                for field in fieldnames:
                    value = getattr(record, field, None)
                    row[field] = self._convert_to_csv_value(value)
                writer.writerow(row)


# ==================== Specific Handler Instances ====================

class UserProfileHandler(CSVHandler[UserProfile]):
    def __init__(self):
        super().__init__(UserProfile, "user_profiles.csv", "user_id")
    
    def get_by_email(self, email: str) -> Optional[UserProfile]:
        """Get user by email address"""
        users = self.filter_by(email=email)
        return users[0] if users else None
    
    def get_active_users(self) -> List[UserProfile]:
        """Get all active users"""
        return self.filter_by(account_status="Active")


class BrowsingHistoryHandler(CSVHandler[BrowsingHistory]):
    def __init__(self):
        super().__init__(BrowsingHistory, "browsing_history.csv", "browse_id")
    
    def get_user_history(self, user_id: str, limit: int = 50) -> List[BrowsingHistory]:
        """Get browsing history for a user"""
        history = self.filter_by(user_id=user_id)
        return sorted(history, key=lambda x: x.view_timestamp, reverse=True)[:limit]
    
    def get_recently_viewed(self, user_id: str, days: int = 7) -> List[BrowsingHistory]:
        """Get recently viewed products"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        return self.search(lambda x: x.user_id == user_id and x.view_timestamp >= cutoff)


class CatalogHandler(CSVHandler[CatalogProduct]):
    def __init__(self):
        super().__init__(CatalogProduct, "catelog.csv", "id")
    
    def get_by_category(self, category: str) -> List[CatalogProduct]:
        """Get products by category"""
        return self.filter_by(category_name=category)
    
    def get_by_brand(self, brand: str) -> List[CatalogProduct]:
        """Get products by brand"""
        return self.filter_by(brand_name=brand)
    
    def search_by_title(self, search_term: str) -> List[CatalogProduct]:
        """Search products by title"""
        search_term = search_term.lower()
        return self.search(lambda x: search_term in x.title.lower())


class ChallengeHandler(CSVHandler[Challenge]):
    def __init__(self):
        super().__init__(Challenge, "challenges.csv", "challenge_id")
    
    def get_active_challenges(self) -> List[Challenge]:
        """Get all active challenges"""
        return self.filter_by(is_active=True)
    
    def get_by_difficulty(self, difficulty: str) -> List[Challenge]:
        """Get challenges by difficulty"""
        return self.filter_by(difficulty=difficulty)


class NotificationHandler(CSVHandler[Notification]):
    def __init__(self):
        super().__init__(Notification, "notifications.csv", "notification_id")
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[Notification]:
        """Get notifications for a user"""
        notifications = self.filter_by(user_id=user_id)
        if unread_only:
            notifications = [n for n in notifications if not n.is_read]
        return sorted(notifications, key=lambda x: x.sent_at, reverse=True)
    
    def mark_as_read(self, notification_id: str) -> Optional[Notification]:
        """Mark notification as read"""
        return self.update(notification_id, {
            "is_read": True,
            "read_at": datetime.now()
        })


class ProductRecommendationHandler(CSVHandler[ProductRecommendation]):
    def __init__(self):
        super().__init__(ProductRecommendation, "product_recommendations.csv", "recommendation_id")
    
    def get_user_recommendations(self, user_id: str, limit: int = 10) -> List[ProductRecommendation]:
        """Get recommendations for a user"""
        recs = self.filter_by(user_id=user_id)
        return sorted(recs, key=lambda x: x.recommendation_score, reverse=True)[:limit]


class ProductTrendHandler(CSVHandler[ProductTrend]):
    def __init__(self):
        super().__init__(ProductTrend, "product_trends.csv", "product_id")
    
    def get_trending_products(self, limit: int = 20) -> List[ProductTrend]:
        """Get trending products"""
        products = self.read_all()
        return sorted(products, key=lambda x: x.trending_score, reverse=True)[:limit]
    
    def get_by_category(self, category: str) -> List[ProductTrend]:
        """Get product trends by category"""
        return self.filter_by(category=category)


class PurchaseHistoryHandler(CSVHandler[PurchaseHistory]):
    def __init__(self):
        super().__init__(PurchaseHistory, "purchase_history.csv", "order_id")
    
    def get_user_orders(self, user_id: str) -> List[PurchaseHistory]:
        """Get user's purchase history"""
        orders = self.filter_by(user_id=user_id)
        return sorted(orders, key=lambda x: x.order_date, reverse=True)
    
    def get_by_status(self, status: str) -> List[PurchaseHistory]:
        """Get orders by status"""
        return self.filter_by(order_status=status)


class ReferralHandler(CSVHandler[ReferralTracking]):
    def __init__(self):
        super().__init__(ReferralTracking, "referral_tracking.csv", "referral_id")
    
    def get_user_referrals(self, user_id: str) -> List[ReferralTracking]:
        """Get referrals made by a user"""
        return self.filter_by(referrer_user_id=user_id)
    
    def get_completed_referrals(self, user_id: str) -> List[ReferralTracking]:
        """Get completed referrals for a user"""
        return self.search(lambda x: x.referrer_user_id == user_id and x.status == "Completed")


class ShoppingCartHandler(CSVHandler[ShoppingCart]):
    def __init__(self):
        super().__init__(ShoppingCart, "shopping_cart.csv", "cart_id")
    
    def get_user_cart(self, user_id: str) -> List[ShoppingCart]:
        """Get user's shopping cart items"""
        return self.filter_by(user_id=user_id)
    
    def clear_user_cart(self, user_id: str) -> int:
        """Clear all items from user's cart"""
        cart_items = self.get_user_cart(user_id)
        count = 0
        for item in cart_items:
            if self.delete(item.cart_id):
                count += 1
        return count


class TransactionHandler(CSVHandler[TransactionHistory]):
    def __init__(self):
        super().__init__(TransactionHistory, "transaction_history.csv", "transaction_id")
    
    def get_user_transactions(self, user_id: str) -> List[TransactionHistory]:
        """Get user's transaction history"""
        transactions = self.filter_by(user_id=user_id)
        return sorted(transactions, key=lambda x: x.transaction_date, reverse=True)
    
    def get_successful_transactions(self, user_id: str) -> List[TransactionHistory]:
        """Get successful transactions for a user"""
        return self.search(lambda x: x.user_id == user_id and x.status == "Success")


class BudgetInsightsHandler(CSVHandler[UserBudgetInsights]):
    def __init__(self):
        super().__init__(UserBudgetInsights, "user_budget_insights.csv", "user_id")
    
    def get_over_budget_users(self) -> List[UserBudgetInsights]:
        """Get users who are over budget"""
        return self.search(lambda x: x.budget_utilized_percent > 100)


class ChallengeProgressHandler(CSVHandler[UserChallengeProgress]):
    def __init__(self):
        super().__init__(UserChallengeProgress, "user_challenge_progress.csv", "progress_id")
    
    def get_user_progress(self, user_id: str) -> List[UserChallengeProgress]:
        """Get user's challenge progress"""
        return self.filter_by(user_id=user_id)
    
    def get_completed_challenges(self, user_id: str) -> List[UserChallengeProgress]:
        """Get completed challenges for a user"""
        return self.search(lambda x: x.user_id == user_id and x.is_completed)


class UserGoalHandler(CSVHandler[UserGoal]):
    def __init__(self):
        super().__init__(UserGoal, "user_goals.csv", "goal_id")
    
    def get_user_goals(self, user_id: str) -> List[UserGoal]:
        """Get user's goals"""
        return self.filter_by(user_id=user_id)
    
    def get_active_goals(self, user_id: str) -> List[UserGoal]:
        """Get active goals for a user"""
        return self.search(lambda x: x.user_id == user_id and x.status == "Active")


class PopCoinBalanceHandler(CSVHandler[UserPopCoinBalance]):
    def __init__(self):
        super().__init__(UserPopCoinBalance, "user_xcoin_balance.csv", "user_id")


class PopCoinLedgerHandler(CSVHandler[PopCoinLedger]):
    def __init__(self):
        super().__init__(PopCoinLedger, "xcoin_ledger.csv", "ledger_id")
    
    def get_user_ledger(self, user_id: str) -> List[PopCoinLedger]:
        """Get user's xcoin ledger"""
        ledger = self.filter_by(user_id=user_id)
        return sorted(ledger, key=lambda x: x.earned_date, reverse=True)
    
    def get_active_popcoins(self, user_id: str) -> List[PopCoinLedger]:
        """Get active (not expired, not spent) popcoins"""
        return self.search(lambda x: x.user_id == user_id and x.status == "Active" and not x.is_expired)


# ==================== Factory Function ====================

def get_handler(model_name: str):
    """
    Get handler instance by model name
    
    Args:
        model_name: Name of the model/handler
        
    Returns:
        Handler instance
    """
    handlers = {
        "user_profile": UserProfileHandler,
        "browsing_history": BrowsingHistoryHandler,
        "catalog": CatalogHandler,
        "challenge": ChallengeHandler,
        "notification": NotificationHandler,
        "product_recommendation": ProductRecommendationHandler,
        "product_trend": ProductTrendHandler,
        "purchase_history": PurchaseHistoryHandler,
        "referral": ReferralHandler,
        "shopping_cart": ShoppingCartHandler,
        "transaction": TransactionHandler,
        "budget_insights": BudgetInsightsHandler,
        "challenge_progress": ChallengeProgressHandler,
        "user_goal": UserGoalHandler,
        "xcoin_balance": PopCoinBalanceHandler,
        "xcoin_ledger": PopCoinLedgerHandler,
    }
    
    handler_class = handlers.get(model_name.lower())
    if not handler_class:
        raise ValueError(f"Unknown handler: {model_name}")
    
    return handler_class()
