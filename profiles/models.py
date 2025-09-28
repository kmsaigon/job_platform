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

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.name} ({self.user.username})"
