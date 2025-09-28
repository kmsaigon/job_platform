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
    class Meta:
        model = Profile
        fields = [
            'name', 'headline', 'skills', 'education', 'experience', 'links',
            'is_public', 'show_contact_info', 'show_experience', 'show_education', 
            'show_skills', 'show_links'
        ]

    def __init__(self, *args, **kwargs):
        super(CustomProfileCreationForm, self).__init__(*args, **kwargs)
        
        # Privacy fields (checkboxes)
        privacy_fields = ['is_public', 'show_contact_info', 'show_experience', 'show_education', 'show_skills', 'show_links']
        
        for fieldname, field in self.fields.items():
            field.help_text = None
            if fieldname in privacy_fields:
                # Checkbox styling
                field.widget.attrs['class'] = 'form-check-input'
            else:
                # Text input styling
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing + ' form-control').strip()