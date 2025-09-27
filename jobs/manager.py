from django.db import models
from django.db.models import Q
import re

class JobQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)
    
    def search_title(self, query):
        if not query:
            return self
        return self.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(company__icontains=query)
        )
    
    def search_location(self, location):
        if not location:
            return self
        # Split location by common separators and search each part
        location_parts = re.split(r'[,\s]+', location.strip())
        location_q = Q()
        for part in location_parts:
            if part.strip():
                location_q |= Q(location__icontains=part.strip())
        return self.filter(location_q)
    
    def search_skills(self, skills_string):
        if not skills_string:
            return self
        
        skills_list = [skill.strip().lower() for skill in skills_string.split(',')]
        skills_q = Q()
        
        for skill in skills_list:
            if skill:
                skills_q |= Q(skills_required__icontains=skill)
        
        return self.filter(skills_q)
    
    def salary_range(self, min_salary=None, max_salary=None):
        queryset = self
        
        if min_salary:
            queryset = queryset.filter(
                Q(salary_max__gte=min_salary) | Q(salary_max__isnull=True)
            )
        
        if max_salary:
            queryset = queryset.filter(
                Q(salary_min__lte=max_salary) | Q(salary_min__isnull=True)
            )
        
        return queryset
    
    def work_arrangement(self, arrangement):
        if not arrangement:
            return self
        return self.filter(work_arrangement=arrangement)
    
    def with_visa_sponsorship(self):
        return self.filter(visa_sponsorship=True)
    
    def employment_types(self, types_list):
        if not types_list:
            return self
        return self.filter(employment_type__in=types_list)

class JobManager(models.Manager):
    def get_queryset(self):
        return JobQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def search(self, **filters):
        """Comprehensive search method"""
        queryset = self.active()
        
        if filters.get('title'):
            queryset = queryset.search_title(filters['title'])
        
        if filters.get('location'):
            queryset = queryset.search_location(filters['location'])
        
        if filters.get('skills'):
            queryset = queryset.search_skills(filters['skills'])
        
        if filters.get('salary_min') or filters.get('salary_max'):
            queryset = queryset.salary_range(
                filters.get('salary_min'), 
                filters.get('salary_max')
            )
        
        if filters.get('work_arrangement'):
            queryset = queryset.work_arrangement(filters['work_arrangement'])
        
        if filters.get('visa_sponsorship'):
            queryset = queryset.with_visa_sponsorship()
        
        if filters.get('employment_type'):
            queryset = queryset.employment_types(filters['employment_type'])
        
        return queryset
