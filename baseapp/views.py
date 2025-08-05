import csv
import json
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Item, Profile
from .forms import ItemForm, CustomUserCreationForm
from .utils import find_potential_matches
from django.contrib.auth.models import User
from django.db.models import F
from django.contrib.auth import logout as auth_logout
from .models import Conversation, Message
from django.contrib.gis.geos import LineString
from django.contrib.gis.measure import D
from django.http import JsonResponse
import json

@login_required
def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'baseapp/register.html', {'form': form})


def dashboard_view(request):
    # --- This is your existing logic for filtering the item list ---
    items = Item.objects.filter(is_resolved=False).order_by('-created_at')
    item_form = ItemForm()

    query = request.GET.get('q')
    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location_name__icontains=query)
        )

    status = request.GET.get('status')
    if status in ['Lost', 'Found']:
        items = items.filter(status=status)

    item_type = request.GET.get('item_type')
    if item_type:
        items = items.filter(item_type=item_type)

    # ** NEW: Analytics Calculations are added here **
    total_active_items = Item.objects.filter(is_resolved=False).count()
    lost_items_count = Item.objects.filter(status='Lost', is_resolved=False).count()
    found_items_count = Item.objects.filter(status='Found', is_resolved=False).count()

    resolved_count = Item.objects.filter(is_resolved=True).count()
    total_reported_count = Item.objects.count()
    if total_reported_count > 0:
        success_rate = round((resolved_count / total_reported_count) * 100)
    else:
        success_rate = 0

    # ** Update the context with BOTH old and new data **
    context = {
        'items': items,
        #'item_form': item_form,
        'item_type_choices': Item.ITEM_TYPE_CHOICES,
        'total_active_items': total_active_items,
        'lost_items_count': lost_items_count,
        'found_items_count': found_items_count,
        'success_rate': success_rate,
    }
    return render(request, 'baseapp/dashboard.html', context)


# Add these imports at the top
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .utils import find_potential_matches


@login_required
def add_item_view(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, 'Your item has been reported successfully!')

            # ** THIS IS THE MISSING CODE **
            # Award 5 reputation points for reporting an item
            profile = request.user.profile
            profile.reputation_score = F('reputation_score') + 5
            profile.save()

            # Find matching items
            matches = find_potential_matches(item)

            # Loop through the matches and email each owner
            for match in matches:
                subject = f'Potential Match for your {match.status} Item!'
                context = {
                    'recipient_user': match.user,
                    'your_item': match,
                    'newly_reported_item': item
                }
                html_message = render_to_string('baseapp/email/match_notification.html', context)
                plain_message = strip_tags(html_message)
                send_mail(subject, plain_message, 'noreply@yourdomain.com', [match.user.email],
                          html_message=html_message)

            return redirect('dashboard')

    return redirect('dashboard')

@login_required
def my_items_view(request):
    items = Item.objects.filter(user=request.user).order_by('-created_at')

    # Apply filtering logic
    query = request.GET.get('q')
    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    status = request.GET.get('status')
    if status in ['Lost', 'Found']:
        items = items.filter(status=status)

    item_type = request.GET.get('item_type')
    if item_type:
        items = items.filter(item_type=item_type)

    context = {
        'items': items,
        'item_type_choices': Item.ITEM_TYPE_CHOICES,
    }
    return render(request, 'baseapp/my_items.html', context)


from django.db.models import F  # Make sure this is imported at the top of the file


@login_required
def resolve_item_view(request, item_id):
    try:
        item = Item.objects.get(id=item_id, user=request.user)

        # Check if the item is not already resolved to prevent giving points multiple times
        if not item.is_resolved:
            item.is_resolved = True
            item.save()
            messages.success(request, f'The item "{item.title}" has been marked as resolved.')

            # ** THIS IS THE MISSING CODE **
            # Award 15 reputation points for a successful resolution
            profile = request.user.profile
            profile.reputation_score = F('reputation_score') + 15
            profile.save()
        else:
            messages.info(request, "This item has already been resolved.")

    except Item.DoesNotExist:
        messages.error(request, 'Item not found or you do not have permission to resolve it.')

    return redirect('my_items')

# Add this import at the top of your views.py
from django.urls import reverse


@login_required
def map_overview_view(request):
    items = Item.objects.filter(is_resolved=False)

    items_data = []
    for item in items:
        # Smartly truncate the description
        description = (item.description[:47] + '...') if len(item.description) > 50 else item.description

        items_data.append({
            'lat': item.latitude,
            'lon': item.longitude,
            'title': item.title,
            'status': item.status,
            'description': description,
            # Add a URL to a detail page (assuming you have one named 'item_detail')
            # 'url': reverse('item_detail', args=[item.id])
        })

    # Convert the final list to JSON
    json_items = json.dumps(items_data)

    return render(request, 'baseapp/map_overview.html', {'items_data': json_items})

@login_required
def export_items_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lost_and_found_items.csv"'
    writer = csv.writer(response)
    writer.writerow(['Title', 'Status', 'Item Type', 'Date', 'Location', 'Reported By', 'Resolved'])
    items = Item.objects.all()
    for item in items:
        writer.writerow([item.title, item.status, item.item_type, item.lost_date, item.location_name, item.user.username, item.is_resolved])
    return response

from django.shortcuts import render, get_object_or_404

@login_required
def item_detail_view(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    context = {'item': item}
    return render(request, 'baseapp/item_detail.html', context)


@login_required
def edit_item_view(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    # Security check: ensure the current user is the owner
    if item.user != request.user:
        messages.error(request, "You don't have permission to edit this item.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your item has been updated.')
            return redirect('item_detail', item_id=item.id)
    else:
        form = ItemForm(instance=item)

    return render(request, 'baseapp/edit_item.html', {'form': form, 'item': item})


@login_required
def delete_item_view(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    # Security check
    if item.user != request.user:
        messages.error(request, "You don't have permission to delete this item.")
        return redirect('dashboard')

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Your item has been deleted.')
        return redirect('dashboard')

    # This redirect is a fallback for GET requests
    return redirect('item_detail', item_id=item.id)


from django.http import JsonResponse
from django.views.decorators.http import require_POST


@login_required
@require_POST  # This view only accepts POST requests
def contact_reporter_view(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if item.user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot contact yourself.'}, status=400)

    message_body = request.POST.get('message')
    sender_contact = request.POST.get('contact')

    if not message_body or not sender_contact:
        return JsonResponse({'status': 'error', 'message': 'All fields are required.'}, status=400)

    # Send email to the item's reporter
    subject = f'New Message Regarding Your Item: "{item.title}"'
    message = (
        f"Someone has sent you a message about your {item.status} item.\n\n"
        f"Message: {message_body}\n\n"
        f"You can reply to them at: {sender_contact}"
    )
    send_mail(subject, message, 'noreply@yourdomain.com', [item.user.email])

    return JsonResponse({'status': 'success', 'message': 'Your message has been sent!'})


# baseapp/views.py

# Add these to your imports at the top of the file
from .forms import UserUpdateForm, ProfileUpdateForm


# ... your other views (dashboard_view, etc.) ...

@login_required
def profile_view(request):
    if request.method == 'POST':
        # Create form instances with the submitted data and current user instances
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)

        # Check if both forms are valid
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')  # Redirect back to the profile page
    else:
        # If it's a GET request, show the forms with the user's current data
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'baseapp/profile.html', context)


# Add these new imports at the top of the file
from thefuzz import fuzz
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# ... your other views ...
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from thefuzz import fuzz
from .models import Item, Notification

from .models import Item, Notification, Conversation  # Make sure Conversation is imported


@login_required
@require_POST
def verify_answer_view(request):
    try:
        item_id = request.POST.get('item_id')
        submitted_answer = request.POST.get('answer')
        item = Item.objects.get(id=item_id)

        if not item.secret_answer:
            return JsonResponse({'error': 'This item has no secret answer.'}, status=400)

        match_ratio = fuzz.token_sort_ratio(item.secret_answer, submitted_answer)
        is_correct = match_ratio > 40

        if is_correct:
            # --- Send Email Notification ---
            subject = f'Ownership Verified for your item: "{item.title}"'
            context = {
                'owner_user': item.user,
                'verifier_user': request.user,
                'item': item,
            }
            html_message = render_to_string('baseapp/email/verification_success_notification.html', context)
            plain_message = strip_tags(html_message)
            send_mail(subject, plain_message, 'noreply@yourdomain.com', [item.user.email], html_message=html_message)

            # ** NEW: Find the relevant conversation **
            conversation = Conversation.objects.filter(
                item=item,
                participants=request.user
            ).filter(participants=item.user).first()

            # ** UPDATED: Create the in-app notification with the conversation link **
            Notification.objects.create(
                recipient=item.user,
                sender=request.user,
                item=item,
                conversation=conversation,  # This line was added
                message=f"Someone successfully answered the secret question for your item: '{item.title}'"
            )

        return JsonResponse({'correct': is_correct})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def contact_reporter_view(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if item.user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot contact yourself.'}, status=400)

    message_body = request.POST.get('message')
    sender_contact = request.POST.get('contact')

    if not message_body or not sender_contact:
        return JsonResponse({'status': 'error', 'message': 'All fields are required.'}, status=400)

    # ... your existing send_mail logic ...

    # ** THIS IS THE MISSING LINE **
    # Create an in-app notification for the item's owner
    Notification.objects.create(
        recipient=item.user,
        sender=request.user,
        item=item,
        message=f"{request.user.username} sent you a message about your item: '{item.title}'"
    )

    return JsonResponse({'status': 'success', 'message': 'Your message has been sent!'})


@login_required
def notifications_view(request):
    # Get all notifications for the current user
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    # Mark them all as read after fetching them
    notifications.update(is_read=True)

    context = {
        'notifications': notifications
    }
    return render(request, 'baseapp/notifications.html', context)




@login_required
def send_verification_email_view(request):
    user = request.user

    # Create a signed, timestamped token
    signer = signing.TimestampSigner()
    token = signer.sign(user.email)

    # Build the verification link
    verification_link = request.build_absolute_uri(
        reverse('verify_email', kwargs={'token': token})
    )

    # Send the email
    subject = 'Verify Your Email for Lost & Found'
    html_message = render_to_string('baseapp/email/verification_email.html', {
        'user': user,
        'verification_link': verification_link
    })
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, 'noreply@yourdomain.com', [user.email], html_message=html_message)

    messages.info(request, 'A verification email has been sent to your address.')
    return redirect('profile')


# baseapp/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User  # Make sure this import is present
from django.core import signing
from django.urls import reverse
from django.contrib import messages


# ... all your other imports ...

# ... your other views ...

def verify_email_view(request, token):
    signer = signing.TimestampSigner()
    try:
        # Check if the token is valid and not older than 1 day (86400 seconds)
        email = signer.unsign(token, max_age=86400)
        user = User.objects.get(email=email)

        # Mark the profile as verified
        user.profile.is_verified = True
        user.profile.save()

        messages.success(request, 'Your email has been successfully verified! You can now log in.')
    except signing.SignatureExpired:
        messages.error(request, 'The verification link has expired.')
    except signing.BadSignature:
        messages.error(request, 'Invalid verification link.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')

    return redirect('login')


@login_required
def leaderboard_view(request):
    # Get the top 10 profiles ordered by reputation score, from highest to lowest
    top_profiles = Profile.objects.order_by('-reputation_score')[:10]

    context = {
        'top_profiles': top_profiles
    }
    return render(request, 'baseapp/leaderboard.html', context)


@login_required
def inbox_view(request):
    # Get all conversations where the current user is a participant
    conversations = Conversation.objects.filter(participants=request.user).order_by('-created_at')

    # ** THE FIX IS HERE **
    # Get all of the user's unread notifications and mark them as read
    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False)
    unread_notifications.update(is_read=True)

    context = {
        'conversations': conversations
    }
    return render(request, 'baseapp/inbox.html', context)


# Make sure these are all imported at the top of your views.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


@login_required
def conversation_detail_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in conversation.participants.all():
        messages.error(request, "You don't have permission to view this conversation.")
        return redirect('dashboard')

    # Logic for when a user sends a new message
    if request.method == 'POST':
        body = request.POST.get('body')
        if body:
            # 1. Save the new message to the database
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                body=body
            )

            # 2. Find the other person in the chat to notify them
            recipient = conversation.participants.exclude(id=request.user.id).first()

            if recipient:
                # 3. Create the in-app notification for the recipient
                Notification.objects.create(
                    recipient=recipient,
                    sender=request.user,
                    item=conversation.item,
                    message=f"You have a new message from {request.user.username} about '{conversation.item.title}'"
                )

                # 4. Send the alert email to the recipient
                subject = f'New Message about your item: "{conversation.item.title}"'
                conversation_link = request.build_absolute_uri(
                    reverse('conversation_detail', kwargs={'conversation_id': conversation_id})
                )
                context = {
                    'recipient': recipient,
                    'sender': request.user,
                    'item': conversation.item,
                    'conversation_link': conversation_link
                }
                html_message = render_to_string('baseapp/email/new_message_notification.html', context)
                plain_message = strip_tags(html_message)
                send_mail(subject, plain_message, 'noreply@yourdomain.com', [recipient.email],
                          html_message=html_message)

            return redirect('conversation_detail', conversation_id=conversation_id)

    context = {
        'conversation': conversation
    }
    return render(request, 'baseapp/conversation_detail.html', context)


@login_required
def inbox_view(request):
    conversations = Conversation.objects.filter(participants=request.user).order_by('-created_at')
    context = {'conversations': conversations}
    return render(request, 'baseapp/inbox.html', context)


@login_required
def start_conversation_view(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if item.user == request.user:
        messages.error(request, "This is your own item.")
        return redirect('dashboard')

    # Find if a conversation already exists
    conversation = Conversation.objects.filter(item=item, participants=request.user).filter(participants=item.user).first()

    # If no conversation exists, create a new one AND send an email
    if not conversation:
        conversation = Conversation.objects.create(item=item)
        conversation.participants.add(request.user, item.user)

        # ** SEND EMAIL ALERT FOR THE NEW CONVERSATION **
        recipient = item.user
        subject = f'New Conversation Started for Your Item: "{item.title}"'
        conversation_link = request.build_absolute_uri(
            reverse('conversation_detail', kwargs={'conversation_id': conversation.id})
        )
        context = {
            'recipient': recipient,
            'sender': request.user,
            'item': item,
            'conversation_link': conversation_link
        }
        html_message = render_to_string('baseapp/email/conversation_started_notification.html', context)
        plain_message = strip_tags(html_message)
        send_mail(subject, plain_message, 'noreply@yourdomain.com', [recipient.email], html_message=html_message)

    # Redirect to the conversation (whether it's new or old)
    return redirect('conversation_detail', conversation_id=conversation.id)


# Make sure these are all imported at the top of your views.py
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse


@login_required
def conversation_detail_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in conversation.participants.all():
        messages.error(request, "You don't have permission to view this conversation.")
        return redirect('inbox')

    if request.method == 'POST':
        body = request.POST.get('body')
        if body:
            # NEW: Check for recent messages to prevent duplicates from fast double-clicks
            last_message = Message.objects.filter(conversation=conversation, sender=request.user).last()
            if last_message and (timezone.now() - last_message.timestamp < timedelta(seconds=2)):
                return redirect('conversation_detail', conversation_id=conversation_id)

            # Create the new message
            Message.objects.create(conversation=conversation, sender=request.user, body=body)

            # Find the recipient to notify them
            recipient = conversation.participants.exclude(id=request.user.id).first()
            if recipient:
                # 1. Create the in-app notification
                Notification.objects.create(
                    recipient=recipient,
                    sender=request.user,
                    item=conversation.item,
                    conversation=conversation,
                    message=f"You have a new message from {request.user.username} about '{conversation.item.title}'"
                )

                # # 2. Send the alert email
                # subject = f'New Message about your item: "{conversation.item.title}"'
                # conversation_link = request.build_absolute_uri(
                #     reverse('conversation_detail', kwargs={'conversation_id': conversation_id})
                # )
                # context = {
                #     'recipient': recipient,
                #     'sender': request.user,
                #     'item': conversation.item,
                #     'conversation_link': conversation_link
                # }
                # html_message = render_to_string('baseapp/email/new_message_notification.html', context)
                # plain_message = strip_tags(html_message)
                # send_mail(subject, plain_message, 'noreply@yourdomain.com', [recipient.email],
                #           html_message=html_message)

        # Redirect after a successful POST to prevent re-submission on refresh
        return redirect('conversation_detail', conversation_id=conversation_id)

    context = {'conversation': conversation}
    return render(request, 'baseapp/conversation_detail.html', context)


from django.contrib.gis.geos import LineString
from django.contrib.gis.measure import D  # D is for Distance
from django.http import JsonResponse
import json


@login_required
def search_route_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            route_coords = data.get('route')

            if not route_coords or len(route_coords) < 2:
                return JsonResponse({'error': 'Invalid route provided.'}, status=400)

            user_route = LineString(route_coords, srid=4326)
            buffer_in_degrees = 100 / 111320.0

            nearby_items = Item.objects.filter(
                is_resolved=False,
                location_point__isnull=False,
                location_point__dwithin=(user_route, buffer_in_degrees)
            )

            items_list = list(nearby_items.values('id', 'title', 'latitude', 'longitude'))
            return JsonResponse({'items': items_list})

        except Exception as e:
            print(f"CRITICAL ERROR in search_route_view: {e}")
            return JsonResponse({'error': 'An unexpected error occurred on the server.'}, status=500)


# @login_required
# def search_route_view(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             route_coords = data.get('route')
#
#             if not route_coords or len(route_coords) < 2:
#                 return JsonResponse({'error': 'Invalid route provided.'}, status=400)
#
#             user_route = LineString(route_coords, srid=4326)
#             buffer_in_degrees = 100 / 111320.0
#
#             nearby_items = Item.objects.filter(
#                 is_resolved=False,
#                 location_point__isnull=False,
#                 location_point__dwithin=(user_route, buffer_in_degrees)
#             )
#
#             # UPDATED: Manually build the list to include all necessary data
#             items_list = []
#             for item in nearby_items:
#                 items_list.append({
#                     'id': item.id,
#                     'title': item.title,
#                     'status': item.status,
#                     'item_type': item.item_type,
#                     'description': item.description,
#                     'location_name': item.location_name,
#                     'latitude': item.latitude,
#                     'longitude': item.longitude,
#                     'date': item.lost_date.strftime('%B %d, %Y'),
#                     'user': item.user.username,
#                     'owner_id': item.user.id,
#                     'owner_verified': item.user.profile.is_verified,
#                     'photo_url': item.photo.url if item.photo else '',
#                     'edit_url': reverse('edit_item', args=[item.id]),
#                     'delete_url': reverse('delete_item', args=[item.id]),
#                     'start_chat_url': reverse('start_conversation', args=[item.id]),
#                     'secret_question': item.secret_question or ''
#                 })
#
#             return JsonResponse({'items': items_list})
#
#         except Exception as e:
#             print(f"CRITICAL ERROR in search_route_view: {e}")
#             return JsonResponse({'error': 'An unexpected error occurred on the server.'}, status=500)