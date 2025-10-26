from django.db import models
from django.conf import settings


class Profile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
	name = models.CharField(max_length=150)
	headline = models.CharField(max_length=150, blank=True)
	skills = models.TextField(blank=True)
	education = models.TextField(blank=True)
	experience = models.TextField(blank=True)
	links = models.TextField(blank=True, help_text='Any links (one per line)')

	# Privacy Settings
	is_public = models.BooleanField(default=True, help_text='Make your profile visible to recruiters')
	show_contact_info = models.BooleanField(default=True, help_text='Show contact information to recruiters')
	show_experience = models.BooleanField(default=True, help_text='Show work experience to recruiters')
	show_education = models.BooleanField(default=True, help_text='Show education to recruiters')
	show_skills = models.BooleanField(default=True, help_text='Show skills to recruiters')
	show_links = models.BooleanField(default=True, help_text='Show links to recruiters')

	# Commute preferences - ADD THESE LINES
	preferred_location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text='Latitude of preferred location')
	preferred_location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text='Longitude of preferred location')
	preferred_location_address = models.CharField(max_length=255, blank=True, help_text='Address of preferred location')
	commute_radius = models.IntegerField(default=25, help_text='Preferred commute radius in miles')

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.name} ({self.user.username})"