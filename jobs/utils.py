# jobs/utils.py
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in miles
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    # Radius of earth in miles
    radius = 3959
    distance = radius * c
    
    return round(distance, 2)

def get_user_location_from_ip(request):
   
    try:
        import requests
        # Get user's IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Get location from IP (using ipapi.co - free tier available)
        response = requests.get(f'https://ipapi.co/{ip}/json/').json()
        
        return {
            'latitude': float(response.get('latitude', 0)),
            'longitude': float(response.get('longitude', 0)),
            'city': response.get('city', ''),
            'region': response.get('region', ''),
        }
    except:
        # Default to a location if IP lookup fails
        return {
            'latitude': 33.7490,  # Atlanta, GA as default
            'longitude': -84.3880,
            'city': 'Atlanta',
            'region': 'Georgia',
        }