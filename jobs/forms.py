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


