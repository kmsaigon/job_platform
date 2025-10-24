from django.contrib import admin, messages
from .models import Company, Department, OfficeLocation
from .utils import geocode_address


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')
    search_fields = ('name',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'company')
    list_filter = ('company',)
    search_fields = ('name',)


@admin.register(OfficeLocation)
class OfficeLocationAdmin(admin.ModelAdmin):
    list_display = ('company', 'address', 'latitude', 'longitude')
    list_filter = ('company',)
    search_fields = ('address',)
    
    def save_model(self, request, obj, form, change):
        """
        Auto-geocode office location if coordinates are missing and address is provided.
        """
        # Only geocode if lat/lng are empty and address is provided
        if (not obj.latitude or not obj.longitude) and obj.address:
            try:
                coordinates = geocode_address(obj.address)
                if coordinates:
                    obj.latitude, obj.longitude = coordinates
                    messages.success(request, f'Successfully geocoded address: {obj.address}')
                else:
                    messages.warning(request, f'Could not geocode address: {obj.address}. Please enter coordinates manually.')
            except Exception as e:
                messages.error(request, f'Error geocoding address: {str(e)}')
        
        super().save_model(request, obj, form, change)