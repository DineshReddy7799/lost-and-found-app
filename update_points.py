import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lostandfound.settings')

import django
django.setup()

from baseapp.models import Item

items_to_update = Item.objects.all()
updated_count = 0

for item in items_to_update:
    item.save() # Calling save() will trigger the new logic to create the point
    updated_count += 1
    print(f"Updated point for: {item.title}")

print(f"\nDone. Updated {updated_count} items with location points.")