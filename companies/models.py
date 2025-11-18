from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('company', 'name')

    def __str__(self) -> str:
        return f"{self.company.name} - {self.name}"


class OfficeLocation(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='office_locations')
    address = models.CharField(max_length=512)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self) -> str:
        location_parts = [self.city, self.state, self.country]
        location_str = ', '.join(filter(None, location_parts))
        if location_str:
            return f"{self.company.name} - {location_str}"
        return f"{self.company.name} - {self.address}"

    @property
    def has_coordinates(self):
        """Check if location has valid coordinates"""
        return self.latitude is not None and self.longitude is not None

    # ALSO ADD THIS PROPERTY (useful)
    @property
    def full_address(self):
        """Return formatted full address"""
        return f"{self.address}, {self.city}, {self.state} {self.postal_code}"

    # AND THIS ONE (useful for maps)
    @property
    def google_maps_url(self):
        """Return Google Maps URL for this location"""
        if self.has_coordinates:
            return f"https://www.google.com/maps/search/?api=1&query={self.latitude},{self.longitude}"
        return None
