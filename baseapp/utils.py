from .models import Item


def find_potential_matches(new_item):
    """Finds matching items to notify their owners."""
    # Find items with the opposite status (e.g., if new_item is 'Lost', find 'Found' items)
    opposite_status = 'Found' if new_item.status == 'Lost' else 'Lost'

    # Define a search area (e.g., within ~5km)
    lat_range = 0.05
    lon_range = 0.05

    # Find unresolved items that are:
    # 1. The opposite status
    # 2. The SAME item type (this is your requirement)
    # 3. Geographically nearby
    potential_matches = Item.objects.filter(
        is_resolved=False,
        status=opposite_status,
        item_type=new_item.item_type,  # The key filter for your request
        latitude__range=(new_item.latitude - lat_range, new_item.latitude + lat_range),
        longitude__range=(new_item.longitude - lon_range, new_item.longitude + lon_range)
    ).exclude(user=new_item.user)

    return potential_matches