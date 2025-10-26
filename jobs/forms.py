from django import forms
from .models import Job, Application, Message, ApplicationEmail


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


class CandidateSearchForm(forms.Form):
    """Form for recruiters to search for candidates by skills, location, and experience"""
    
    skills = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Python, Django, React, JavaScript...',
            'class': 'form-control',
            'id': 'candidate_skills'
        }),
        label='Required Skills',
        help_text='Enter skills separated by commas'
    )
    
    location = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'City, State, Country...',
            'class': 'form-control',
            'id': 'candidate_location'
        }),
        label='Search Location',
        help_text='Search for candidates near this location'
    )
    
    experience = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Project keywords, technologies, experience...',
            'class': 'form-control',
            'id': 'candidate_experience'
        }),
        label='Experience/Projects',
        help_text='Search through candidate experience and projects'
    )
    
    # Hidden fields for location coordinates
    search_lat = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'search_lat'})
    )
    
    search_lng = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'search_lng'})
    )
    
    # Distance radius for location search
    distance_radius = forms.ChoiceField(
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
            'id': 'distance_radius'
        }),
        label='Search Radius'
    )
    
    # Sorting options
    sort_by = forms.ChoiceField(
        choices=[
            ('skills_match', 'Skills Match'),
            ('distance', 'Distance'),
            ('recent', 'Most Recent'),
            ('name', 'Name A-Z'),
        ],
        required=False,
        initial='skills_match',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'sort_by'
        }),
        label='Sort By'
    )


class MessageForm(forms.ModelForm):
    """Form for sending in-platform messages"""
    class Meta:
        model = Message
        fields = ['subject', 'content']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Message subject (optional)'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Write your message here...',
                'required': True
            })
        }
        labels = {
            'subject': 'Subject (optional)',
            'content': 'Message'
        }


class ApplicationEmailForm(forms.ModelForm):
    """Form for sending emails through the platform"""
    class Meta:
        model = ApplicationEmail
        fields = ['subject', 'message']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Your message will be emailed to the candidate...',
                'required': True
            })
        }
        labels = {
            'subject': 'Subject',
            'message': 'Message'
        }