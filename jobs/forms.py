from django import forms
from .models import Job


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'company', 'title', 'description', 'employment_type', 'work_mode',
            'visa_required', 'salary_min', 'salary_max', 'office_location'
        ]

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
        choices=[('', 'Any')] + list(Job.WorkMode.choices),  # Use actual model choices
        required=False,
        widget=forms.Select(attrs={'class': 'form-select filter-select'})
    )
    
    employment_type = forms.MultipleChoiceField(
        choices=Job.EmploymentType.choices,  # Use actual model choices
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )