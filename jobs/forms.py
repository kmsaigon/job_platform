from django import forms
from .models import Job, Application


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'company', 'title', 'description', 'required_skills', 'employment_type', 'work_mode',
            'visa_required', 'salary_min', 'salary_max', 'office_location'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
            'required_skills': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Python, Django, React, JavaScript (one per line or comma-separated)'}),
        }

    def clean(self):
        cleaned = super().clean()
        salary_min = cleaned.get('salary_min')
        salary_max = cleaned.get('salary_max')
        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            self.add_error('salary_min', 'Minimum salary cannot exceed maximum salary.')
        return cleaned


class JobSearchForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Job title, keywords...',
            'class': 'form-control'
        })
    )
    
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'City, State, Country...',
            'class': 'form-control'
        })
    )
    
    salary_min = forms.DecimalField(  
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min salary',
            'class': 'form-control',
            'min': 0
        })
    )
    
    salary_max = forms.DecimalField( 
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max salary',
            'class': 'form-control',
            'min': 0
        })
    )
    
    visa_required = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    work_mode = forms.ChoiceField(
        choices=[('', 'Any')] + list(Job.WorkMode.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select filter-select'})
    )
    
    employment_type = forms.MultipleChoiceField(
        choices=Job.EmploymentType.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )
    
    # NEW: Commute radius filter fields
    commute_location = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your location (e.g., Atlanta, GA)',
            'class': 'form-control',
            'id': 'commute_location'
        }),
        label='Your Location'
    )
    
    commute_lat = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'commute_lat'})
    )
    
    commute_lng = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'commute_lng'})
    )
    
    commute_radius = forms.ChoiceField(
        choices=[
            ('', 'Any distance'),
            ('5', 'Within 5 miles'),
            ('10', 'Within 10 miles'),
            ('25', 'Within 25 miles'),
            ('50', 'Within 50 miles'),
            ('100', 'Within 100 miles'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'commute_radius'
        }),
        label='Distance'
    )


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['application_note']
        widgets = {
            'application_note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Tell the employer why you are a great fit for this role. Highlight relevant skills, experience, and your enthusiasm for the position.',
                'required': True
            })
        }
        labels = {
            'application_note': 'Why are you a good fit for this role?'
        }