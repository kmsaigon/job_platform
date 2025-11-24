from django import forms
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from decimal import Decimal, ROUND_HALF_UP

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
        required=False,  # Changed to False - location is optional
        widget=forms.HiddenInput(),  # Changed to HiddenInput since we use custom UI
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
    
    def clean_preferred_location_lat(self):
        """Round latitude to 6 decimal places before validation"""
        lat = self.cleaned_data.get('preferred_location_lat')
        if lat is not None:
            try:
                # Convert to Decimal and round to 6 decimal places
                lat_decimal = Decimal(str(lat))
                # Round to 6 decimal places
                lat_rounded = lat_decimal.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                return lat_rounded
            except (ValueError, TypeError):
                return None
        return None
    
    def clean_preferred_location_lng(self):
        """Round longitude to 6 decimal places before validation"""
        lng = self.cleaned_data.get('preferred_location_lng')
        if lng is not None:
            try:
                # Convert to Decimal and round to 6 decimal places
                lng_decimal = Decimal(str(lng))
                # Round to 6 decimal places
                lng_rounded = lng_decimal.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                return lng_rounded
            except (ValueError, TypeError):
                return None
        return None
    
    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data.get('preferred_location_lat')
        lng = cleaned_data.get('preferred_location_lng')
        address = cleaned_data.get('preferred_location_address', '').strip()
        
        # If address is provided but no coordinates, clear the address
        # This allows saving without location, but if they provide address, they need coordinates
        if address and (not lat or not lng):
            # Clear the address if coordinates are missing
            cleaned_data['preferred_location_address'] = ''
            cleaned_data['preferred_location_lat'] = None
            cleaned_data['preferred_location_lng'] = None
            # Don't raise error - just clear invalid address
            # This allows users to save profile without location
        elif not address:
            # If no address, also clear coordinates
            cleaned_data['preferred_location_lat'] = None
            cleaned_data['preferred_location_lng'] = None
        
        return cleaned_data