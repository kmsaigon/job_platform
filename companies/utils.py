import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def geocode_address(address):
    """
    Geocode an address using Google Geocoding API.
    
    Args:
        address (str): Full address string to geocode
        
    Returns:
        tuple: (latitude, longitude) if successful, None if failed
    """
    if not address or not address.strip():
        return None
        
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
    if not api_key:
        logger.warning("GOOGLE_MAPS_API_KEY not configured")
        return None
    
    try:
        # Google Geocoding API endpoint
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address.strip(),
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('results'):
            # Get the first result
            result = data['results'][0]
            location = result['geometry']['location']
            lat = location['lat']
            lng = location['lng']
            
            logger.info(f"Successfully geocoded address: {address} -> ({lat}, {lng})")
            return (lat, lng)
        else:
            logger.warning(f"Geocoding failed for address '{address}': {data.get('status', 'Unknown error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during geocoding for address '{address}': {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during geocoding for address '{address}': {e}")
        return None
