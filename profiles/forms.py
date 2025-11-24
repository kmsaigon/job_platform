from django import forms
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe

from .models import Profile

class CustomErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return mark_safe(''.join([f'<div class="alert alert-danger" role="alert">{e}</div>' for e in self]))

class CustomProfileCreationForm(forms.ModelForm):
    # Add location fields as CharField for the address input
    preferred_location_address = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your city, state (e.g., Atlanta, GA)',
            'id': 'location_input'
        }),
        label='Current Location',
        help_text='Where are you currently based? This helps recruiters find local candidates'
    )
    
    class Meta:
        model = Profile
        fields = [
            'name', 'headline', 'skills', 'education', 'experience', 'links',
            'preferred_location_address', 'preferred_location_lat', 'preferred_location_lng', 'commute_radius',
            'is_public', 'show_contact_info', 'show_experience', 'show_education', 
            'show_skills', 'show_links'
        ]
        widgets = {
            'preferred_location_lat': forms.HiddenInput(),
            'preferred_location_lng': forms.HiddenInput(),
            'commute_radius': forms.Select(choices=[
                (5, '5 miles'),
                (10, '10 miles'),
                (25, '25 miles'),
                (50, '50 miles'),
                (100, '100 miles'),
            ], attrs={'class': 'form-select'}),
        }
        labels = {
            'commute_radius': 'Preferred Commute Distance',
        }

    def __init__(self, *args, **kwargs):
        super(CustomProfileCreationForm, self).__init__(*args, **kwargs)
        
        # Privacy fields (checkboxes)
        privacy_fields = ['is_public', 'show_contact_info', 'show_experience', 'show_education', 'show_skills', 'show_links']
        
        for fieldname, field in self.fields.items():
            field.help_text = None
            if fieldname in privacy_fields:
                # Checkbox styling
                field.widget.attrs['class'] = 'form-check-input'
            elif fieldname not in ['preferred_location_lat', 'preferred_location_lng', 'preferred_location_address', 'commute_radius']:
                # Text input styling (skip location fields as they already have styling)
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing + ' form-control').strip()
    
    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data.get('preferred_location_lat')
        lng = cleaned_data.get('preferred_location_lng')
        address = cleaned_data.get('preferred_location_address')
        
        # If address is provided but no coordinates, raise error
        if address and (not lat or not lng):
            raise forms.ValidationError(
                'Please select a valid location from the dropdown suggestions. '
                'Start typing your city and select from the list that appears.'
            )
        
        return cleaned_data