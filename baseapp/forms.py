# baseapp/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Item

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)

        def clean_email(self):
            email = self.cleaned_data.get('email')
            if email and User.objects.filter(email=email).exists():
                raise forms.ValidationError("A user with this email address already exists.")
            return email

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'title', 'description', 'status', 'item_type', 'photo',
            'contact_info', 'lost_date', 'location_name', 'latitude', 'longitude',
            'secret_question', 'secret_answer'
        ]
        widgets = {
            'lost_date': forms.DateInput(attrs={'type': 'date'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

# baseapp/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Profile, Item # Add Profile to imports

# ... your other forms (ItemForm, CustomUserCreationForm) ...

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['contact_info', 'bio']


from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm



