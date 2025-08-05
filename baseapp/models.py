# baseapp/models.py
from django.db import models
from django.contrib.auth.models import User
# Add these new imports for signals
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point

class Item(models.Model):
    STATUS_CHOICES = (
        ('Lost', 'Lost'),
        ('Found', 'Found'),
    )
    ITEM_TYPE_CHOICES = (
        ('Electronics', 'Electronics'),
        ('Documents', 'Documents'),
        ('Apparel', 'Apparel'),
        ('Other', 'Other'),
    )

    # Core Fields
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    photo = models.ImageField(upload_to='item_photos/', blank=True, null=True)
    contact_info = models.CharField(max_length=200, help_text="Email or phone number for contact")

    # Location & Date
    lost_date = models.DateField()
    location_name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    #location_point = gis_models.PointField(srid=4326, blank=True, null=True)
    # Admin & Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    secret_question = models.CharField(max_length=255, blank=True, null=True)
    secret_answer = models.CharField(max_length=255, blank=True, null=True)

    # def save(self, *args, **kwargs):
    #     if self.latitude and self.longitude:
    #         # Note the order is (longitude, latitude) for a PointField
    #         self.location_point = Point(self.longitude, self.latitude)
    #     super().save(*args, **kwargs)
def __str__(self):
        return f"{self.get_status_display()} {self.title}"



# ADD THE NEW PROFILE MODEL AND SIGNALS BELOW
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_info = models.CharField(max_length=200, blank=True, help_text="Your preferred contact (email or phone)")
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    reputation_score = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.user.username} Profile'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Conversation(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True)

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True)


    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message