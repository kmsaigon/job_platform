from django.core.management.base import BaseCommand
from companies.models import OfficeLocation
import requests
from decimal import Decimal
import time

class Command(BaseCommand):
    help = 'Geocode all office locations that are missing coordinates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-geocode all locations, even those with existing coordinates',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        if force:
            locations = OfficeLocation.objects.all()
            self.stdout.write(self.style.WARNING(f'Re-geocoding ALL {locations.count()} locations...'))
        else:
            locations = OfficeLocation.objects.filter(
                latitude__isnull=True
            ) | OfficeLocation.objects.filter(
                longitude__isnull=True
            )
            self.stdout.write(f'Geocoding {locations.count()} locations without coordinates...')
        
        success_count = 0
        error_count = 0
        
        for location in locations:
            self.stdout.write(f'\nGeocoding: {location.city}, {location.state}...')
            self.stdout.write(f'  Address: {location.address}')
            
            coords = self.geocode_address(location)
            
            if coords:
                location.latitude = coords['latitude']
                location.longitude = coords['longitude']
                location.save()
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Success: {coords["latitude"]}, {coords["longitude"]}')
                )
            else:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed to geocode')
                )
            
            # Rate limiting - wait 1 second between requests
            time.sleep(1)
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'✓ Completed: {success_count} successful')
        )
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed: {error_count}')
            )
    
    def geocode_address(self, location):
        """Geocode using Nominatim (OpenStreetMap) - Free, no API key"""
        try:
            full_address = f"{location.address}, {location.city}, {location.state} {location.postal_code}, {location.country}"
            
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': full_address,
                'format': 'json',
                'limit': 1
            }
            headers = {
                'User-Agent': 'JobPlatform/1.0 (your-email@example.com)'  # Required by Nominatim
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0:
                return {
                    'latitude': Decimal(data[0]['lat']),
                    'longitude': Decimal(data[0]['lon']),
                }
            
            return None
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))
            return None