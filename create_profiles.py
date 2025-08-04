# This script ensures every existing user has a profile.
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lostandfound.settings') # Replace 'lostandfound' with your project's name

import django
django.setup()

from django.contrib.auth.models import User
from baseapp.models import Profile

# Get all users
users = User.objects.all()
created_count = 0

for user in users:
    # The get_or_create method is safe. It finds an existing profile or creates a new one.
    profile, created = Profile.objects.get_or_create(user=user)
    if created:
        created_count += 1
        print(f"Created profile for: {user.username}")

print(f"\nDone. Created {created_count} new profiles.")