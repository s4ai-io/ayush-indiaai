from typing import Optional, Dict, Any, List
from src.agents.crud_helper import CatalogHandler
from src.agents.tools import get_xcoin_balance

def get_user_intent_options(user_id: str) -> Dict[str, Any]:
    """
    Get user's popCoin balance and generate intent-based questions.
    This is Level 0 - the initial intent layer before catalog navigation.
    
    Args:
        user_id: User identifier (e.g., "U000001")
        
    Returns:
        Dictionary containing:
        - level: 0 (intent level)
        - next_level_name: "intent"
        - options: List of intent options with routing metadata
        - balance_info: Full balance data from get_xcoin_balance
        - context: Human-readable balance summary
        - is_leaf: False (not a leaf node)
    
    Example:
        >>> get_user_intent_options("U000001")
        {
            "level": 0,
            "next_level_name": "intent",
            "options": [
                {"text": "Spend my popCoins on products", "category": "intent", "routes_to": "catalog"},
                {"text": "Earn more popCoins", "category": "intent", "routes_to": "earnings"},
                ...
            ],
            "context": "Balance: 536 popCoins (88 expiring soon)",
            "is_leaf": False
        }
    """
    try:
        # Get user's balance
        balance_data = get_xcoin_balance(user_id)
        
        # Extract key metrics
        current_balance = balance_data.get('current_balance', 0)
        expiring_soon = balance_data.get('popcoins_expiring_soon', 0)
        
        # Generate context string
        context = f"Balance: {current_balance} popCoins"
        if expiring_soon > 0:
            context += f" ({expiring_soon} expiring soon)"
        
        # Define intent options with routing metadata
        options = [
            {
                "text": "Spend my popCoins on products",
                "category": "intent",
                "routes_to": "catalog"
            },
            {
                "text": "Earn more popCoins",
                "category": "intent",
                "routes_to": "earnings"
            },
            {
                "text": "Check expiring popCoins",
                "category": "intent",
                "routes_to": "expiry"
            },
            {
                "text": "See my popCoin goals",
                "category": "intent",
                "routes_to": "goals"
            }
        ]
        
        return {
            "level": 0,
            "next_level_name": "intent",
            "options": options,
            "balance_info": balance_data,
            "context": context,
            "is_leaf": False,
            "auto_selected": []
        }
        
    except Exception as e:
        print(f"Error in get_user_intent_options: {e}")
        # Return fallback options without balance info
        return {
            "level": 0,
            "next_level_name": "intent",
            "options": [
                {"text": "Spend my popCoins on products", "category": "intent", "routes_to": "catalog"},
                {"text": "Earn more popCoins", "category": "intent", "routes_to": "earnings"}
            ],
            "context": "Explore your popCoin options",
            "is_leaf": False,
            "auto_selected": []
        }

def get_catalog_hierarchy(
    ideal_for: Optional[str] = None,
    category_name: Optional[str] = None,
    brand_name: Optional[str] = None,
    color: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve the next level of catalog options based on current hierarchical selections.
    Automatically skips levels if only one option is available.
    
    Args:
        ideal_for: Selection for Level 1
        category_name: Selection for Level 2
        brand_name: Selection for Level 3
        color: Selection for Level 4
        
    Returns:
        Dictionary containing:
        - level: Current numeric level (1-5)
        - next_level_name: Name of attribute for next level
        - options: List of available options
        - is_leaf: True if end of hierarchy
        - auto_selected: List of strings describing auto-selected options (e.g. "brand_name: Nike")
    """
    try:
        handler = CatalogHandler()
        products = handler.read_all()
        
        print(f"DEBUG: Total products loaded: {len(products)}")
        if products:
             print(f"DEBUG: First product sample: {products[0]}")

        auto_selected = []
        current_level_products = products
        


        # --- Helper to get unique options ---
        def get_options(prods, field):
            vals = set()
            for p in prods:
                val = getattr(p, field, None)
                if val:
                    vals.add(val)
            return sorted(list(vals))

        # --- Level 1: ideal_for ---
        if not ideal_for:
            opts = get_options(current_level_products, "ideal_for")
            if len(opts) == 1:
                ideal_for = opts[0]
                auto_selected.append(f"ideal_for: {ideal_for}")
            else:
                return {"level": 1, "next_level_name": "ideal_for", "options": opts, "is_leaf": False, "auto_selected": auto_selected}

        # Filter Level 1
        current_level_products = [p for p in current_level_products if p.ideal_for and p.ideal_for.lower() == ideal_for.lower()]
        print(f"DEBUG: After filtering ideal_for='{ideal_for}': {len(current_level_products)} products remaining")
        
        # --- Level 2: category_name ---
        if not category_name:
            opts = get_options(current_level_products, "category_name")
            if len(opts) == 1:
                category_name = opts[0]
                auto_selected.append(f"category_name: {category_name}")
            else:
                return {"level": 2, "next_level_name": "category_name", "options": opts, "is_leaf": False, "auto_selected": auto_selected}

        # Filter Level 2
        current_level_products = [p for p in current_level_products if p.category_name and p.category_name.lower() == category_name.lower()]
        print(f"DEBUG: After filtering category_name='{category_name}': {len(current_level_products)} products remaining")

        # --- Level 3: brand_name ---
        if not brand_name:
            opts = get_options(current_level_products, "brand_name")
            if len(opts) == 1:
                brand_name = opts[0]
                auto_selected.append(f"brand_name: {brand_name}")
            else:
                return {"level": 3, "next_level_name": "brand_name", "options": opts, "is_leaf": False, "auto_selected": auto_selected}

        # Filter Level 3
        current_level_products = [p for p in current_level_products if p.brand_name and p.brand_name.lower() == brand_name.lower()]
        print(f"DEBUG: After filtering brand_name='{brand_name}': {len(current_level_products)} products remaining")

        # --- Level 4: color ---
        if not color:
            opts = get_options(current_level_products, "color")
            if len(opts) == 1:
                color = opts[0]
                auto_selected.append(f"color: {color}")
                # Fall through to leaf
            else:
                return {"level": 4, "next_level_name": "color", "options": opts, "is_leaf": False, "auto_selected": auto_selected}
        
        # --- Level 5: Leaf ---
        return {
            "level": 5, 
            "next_level_name": None, 
            "options": [], 
            "is_leaf": True, 
            "auto_selected": auto_selected,
            "final_filters": {
                "ideal_for": ideal_for,
                "category_name": category_name,
                "brand_name": brand_name,
                "color": color
            }
        }


    except Exception as e:
        print(f"Error in get_catalog_hierarchy: {e}")
        return {
            "error": str(e),
            "options": []
        }
