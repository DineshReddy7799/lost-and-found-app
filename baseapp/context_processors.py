from .models import Notification
from .forms import ItemForm  # Import your ItemForm


def notifications(request):
    context = {}
    if request.user.is_authenticated:
        # Get unread notification count
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        context['unread_notifications'] = unread_count

    # Add the item_form to the context for every page
    context['item_form'] = ItemForm()

    return context