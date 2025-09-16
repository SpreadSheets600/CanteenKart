import google.generativeai as genai
from flask import current_app
from sqlalchemy import func
from app.models.order import OrderItem
from app.models.menu_item import MenuItem
from app.models.order import Order


def get_top_orders(limit=10):
    """Get top ordered items based on total quantity sold."""
    try:
        # Query for most ordered items
        top_items = (
            OrderItem.query
            .join(MenuItem)
            .with_entities(
                MenuItem.item_id,
                MenuItem.name,
                MenuItem.description,
                MenuItem.price,
                MenuItem.image,
                func.sum(OrderItem.quantity).label('total_quantity')
            )
            .group_by(MenuItem.item_id)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                'item_id': item.item_id,
                'name': item.name,
                'description': item.description,
                'price': item.price,
                'image': item.image,
                'total_quantity': item.total_quantity
            }
            for item in top_items
        ]
    except Exception as e:
        current_app.logger.error(f"Error getting top orders: {e}")
        return []


def get_user_recommendations(user_id, limit=5):
    """Get personalized recommendations for a user using Gemini AI."""
    try:
        # Get user's order history
        user_orders = (
            OrderItem.query
            .join(Order)
            .join(MenuItem)
            .filter(Order.user_id == user_id)
            .with_entities(
                MenuItem.name,
                MenuItem.description,
                func.sum(OrderItem.quantity).label('quantity')
            )
            .group_by(MenuItem.item_id)
            .all()
        )

        if not user_orders:
            # New user, recommend popular items
            return get_top_orders(limit)

        # Get all menu items for context
        all_items = MenuItem.query.filter_by(is_available=True).all()

        # Get popular items that user hasn't ordered
        user_ordered_item_ids = set()
        for order in user_orders:
            # We need to get item_ids, but we have names. Let's adjust.
            pass

        # Actually, let's get item_ids properly
        user_ordered_items = (
            OrderItem.query
            .join(Order)
            .filter(Order.user_id == user_id)
            .with_entities(OrderItem.item_id)
            .distinct()
            .all()
        )
        user_ordered_item_ids = {item.item_id for item in user_ordered_items}

        # Get popular items not ordered by user
        popular_items = get_top_orders(20)  # Get more to filter
        un_ordered_popular = [
            item for item in popular_items
            if item['item_id'] not in user_ordered_item_ids
        ]

        if len(un_ordered_popular) >= limit:
            return un_ordered_popular[:limit]

        # Use Gemini for advanced recommendations
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            current_app.logger.warning("GEMINI_API_KEY not configured")
            return un_ordered_popular[:limit]

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Prepare context for Gemini
        user_history = "\n".join([
            f"- {order.name}: {order.description or 'No description'} (ordered {order.quantity} times)"
            for order in user_orders
        ])

        menu_items_text = "\n".join([
            f"- {item.name}: {item.description or 'No description'}"
            for item in all_items if item.item_id not in user_ordered_item_ids
        ])

        prompt = f"""
        Based on the user's order history and available menu items, recommend {limit} items they might like.

        User's order history:
        {user_history}

        Available menu items (not previously ordered):
        {menu_items_text}

        Please recommend {limit} items from the available list that would complement their previous orders or match their preferences.
        Return only the item names, one per line, no additional text.
        """

        try:
            response = model.generate_content(prompt)
            recommended_names = [
                line.strip('- ').strip()
                for line in response.text.strip().split('\n')
                if line.strip()
            ][:limit]

            # Match names to menu items
            recommendations = []
            for name in recommended_names:
                for item in all_items:
                    if item.name.lower() == name.lower() and item.item_id not in user_ordered_item_ids:
                        recommendations.append({
                            'item_id': item.item_id,
                            'name': item.name,
                            'description': item.description,
                            'price': item.price,
                            'image': item.image
                        })
                        break

            return recommendations[:limit]

        except Exception as e:
            current_app.logger.error(f"Gemini API error: {e}")
            return un_ordered_popular[:limit]

    except Exception as e:
        current_app.logger.error(f"Error getting user recommendations: {e}")
        return []
