# support/bot.py
import re
from django.urls import reverse
from listings.models import Order, Listing, SavedItem


def get_welcome_message():
    """
    Returns the initial welcome message from the support bot, including
    HTML links that trigger bot commands.
    """
    # This version uses data-attributes for the JavaScript to handle,
    # avoiding potential URL reversal errors during initial connection.
    message = (
        "Hi! Is there anything I can help you with?<br>"
        "<ul>"
        "<li><a href='#' class='chat-suggestion' data-message='Track my order'>Track your order</a></li>"
        "<li><a href='#' class='chat-suggestion' data-message='Search for products'>Search for products</a></li>"
        "<li><a href='#' class='chat-suggestion' data-message='View my wishlist'>View your wishlist</a></li>"
        "<li><a href='#' class='chat-suggestion' data-message='How to sell'>Learn how to sell</a></li>"
        "<li><a href='#' class='chat-suggestion' data-message='Report a user'>Report a user</a></li>"
        "</ul>"
    )
    return message


def get_bot_response(user, message, message_history=None):
    """
    The efficient, rule-based logic for the chatbot.
    """
    message_lower = message.lower()

    last_bot_message = ""
    if message_history and len(message_history) > 1:
        # Get the bot's last message to see if it was asking a question
        last_bot_message = message_history[-2].message.lower()

    if "what are you looking for" in last_bot_message:
        query = message
        results = Listing.objects.filter(title__icontains=query, status='available')[:3]
        if results:
            response_lines = [f"I found these results for '<b>{query}</b>':"]
            for listing in results:
                response_lines.append(f"&bull; <a href='{listing.get_absolute_url()}'>{listing.title}</a>")
            return "<br>".join(response_lines)
        else:
            return f"I'm sorry, I couldn't find any products matching '<b>{query}</b>'."

    order_match = re.search(r'order\s*(?:#|number|id)?\s*(\d+)', message_lower)
    if order_match:
        order_id = int(order_match.group(1))
        try:
            order = Order.objects.get(id=order_id, user=user)
            return f"Order #{order.id} is currently '<b>{order.get_status_display()}</b>'."
        except Order.DoesNotExist:
            return f"I couldn't find Order #{order_id} in your purchase history."

    if any(keyword in message_lower for keyword in ["order status", "my order", "track", "track my order", "where is my order"]):
        try:
            latest_order = Order.objects.filter(user=user).latest('created_at')
            return (f"Your latest order, #{latest_order.id}, is currently marked as "
                    f"'<b>{latest_order.get_status_display()}</b>'. You can also ask about a "
                    f"specific order by saying 'status for order #123'.")
        except Order.DoesNotExist:
            return "It looks like you haven't placed any orders yet."

    if message_lower == 'search for products':
        return "Of course! What are you looking for today?"

    search_match = re.search(r'(?:search for|find|looking for|do you have)\s*(.+)', message_lower)
    if search_match:
        query = search_match.group(1).strip()
        results = Listing.objects.filter(title__icontains=query, status='available')[:3]
        if results:
            response_lines = [f"I found these results for '<b>{query}</b>':"]
            for listing in results:
                response_lines.append(f"&bull; <a href='{listing.get_absolute_url()}'>{listing.title}</a>")
            return "<br>".join(response_lines)
        else:
            return f"I'm sorry, I couldn't find any products matching '<b>{query}</b>'."

    if "wishlist" in message_lower or "saved items" in message_lower or "view my wishlist" in message_lower:
        saved_items = SavedItem.objects.filter(user=user).select_related('listing')[:5]
        if saved_items:
            response_lines = ["Here are the latest items on your wishlist! ✨"]
            for item in saved_items:
                response_lines.append(f"&bull; <a href='{item.listing.get_absolute_url()}'>{item.listing.title}</a>")
            return "<br>".join(response_lines)
        else:
            return "Your wishlist is currently empty."

    if any(keyword in message_lower for keyword in ["how to sell", "create a listing", "sell something"]):
        return ("That's great! You can start selling by creating a listing. "
                f"Just click here to go to the <a href='{reverse('listings:listing_create')}'>Create Listing page</a>.")

    if any(keyword in message_lower for keyword in ["payment methods", "payment options", "cod"]):
        return "We currently support Cash on Delivery (COD). We are working on adding more payment options in the future!"

    if any(keyword in message_lower for keyword in ["contact seller", "ask a question"]):
        return ("To contact a seller, please go to the product's page and click the 'Message Seller' button. "
                "This will open a direct conversation with them.")

    if any(keyword in message_lower for keyword in ["report a user", "report user", "report someone"]):
        return ("I'm sorry to hear you've had an issue. You can file a report using our "
                f"<a href='{reverse('reports:create_user_report')}'>secure reporting form</a>. Please provide as much detail as possible.")

    if "help" in message_lower or "suggestion" in message_lower:
        return ("How can I help you today? You can ask me about:<br>"
                "&bull; Your latest order status<br>"
                "&bull; A specific order (e.g., 'status for order #123')<br>"
                "&bull; Your wishlist<br>"
                "&bull; To find products (e.g., 'search for red shoes')<br>"
                "&bull; How to sell on the platform<br>"
                "&bull; How to report a user")

    return "I'm sorry, I don't understand that. You can ask me for 'help' to see what I can do."