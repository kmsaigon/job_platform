"""
Utility functions for candidate search and notifications
"""
from django.db.models import Q
from django.utils import timezone
from profiles.models import Profile
from math import radians, sin, cos, sqrt, atan2


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the distance (miles) between two lat/lon points."""
    R = 3958.8  # Radius of Earth in miles
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def get_candidates_for_search(saved_search):
    """
    Get candidates matching a saved search criteria.
    Returns a queryset of Profile objects.
    """
    # Start with public profiles only
    queryset = Profile.objects.filter(
        is_public=True
    ).select_related('user')
    
    # Skills search
    if saved_search.skills:
        skills_query = saved_search.skills
        search_skills = [skill.strip().lower() for skill in skills_query.split(',') if skill.strip()]
        
        if search_skills:
            skills_filter = Q()
            for skill in search_skills:
                skills_filter |= Q(skills__icontains=skill)
            queryset = queryset.filter(skills_filter)
    
    # Experience search
    if saved_search.experience:
        experience_query = saved_search.experience
        queryset = queryset.filter(
            Q(experience__icontains=experience_query) |
            Q(education__icontains=experience_query)
        )
    
    # Location search
    if saved_search.search_lat and saved_search.search_lng and saved_search.distance_radius:
        try:
            user_lat = float(saved_search.search_lat)
            user_lng = float(saved_search.search_lng)
            radius = float(saved_search.distance_radius)
            
            # Filter candidates within radius
            filtered_candidates = []
            for profile in queryset:
                # Include candidates without location preferences
                if not profile.preferred_location_lat or not profile.preferred_location_lng:
                    filtered_candidates.append(profile.id)
                    continue
                    
                # Check distance for candidates with location preferences
                distance = haversine(
                    user_lat, user_lng,
                    float(profile.preferred_location_lat),
                    float(profile.preferred_location_lng)
                )
                if distance <= radius:
                    filtered_candidates.append(profile.id)
            
            queryset = queryset.filter(id__in=filtered_candidates)
        except (ValueError, TypeError):
            pass  # Invalid coordinates, skip filter
    
    return queryset


def get_new_matches(saved_search):
    """
    Get new candidate matches for a saved search that were created/updated
    after the last check.
    """
    # Get all matching candidates
    all_matches = get_candidates_for_search(saved_search)
    
    # Filter for new matches (profiles created/updated after last check)
    if saved_search.last_checked_at:
        new_matches = all_matches.filter(
            Q(created_at__gt=saved_search.last_checked_at) |
            Q(updated_at__gt=saved_search.last_checked_at)
        )
    else:
        # If never checked, return all matches (but we'll only notify about recent ones)
        # Only notify about profiles created/updated in the last 7 days
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=7)
        new_matches = all_matches.filter(
            Q(created_at__gt=cutoff_date) |
            Q(updated_at__gt=cutoff_date)
        )
    
    return new_matches


def send_search_notification(saved_search, new_matches):
    """
    Send email notification to recruiter about new matches.
    """
    from django.core.mail import send_mail
    from django.conf import settings
    from django.urls import reverse
    
    if not saved_search.recruiter.email:
        return False
    
    match_count = new_matches.count()
    if match_count == 0:
        return False
    
    # Build email content
    subject = f'New Candidate Matches for "{saved_search.name}"'
    
    # Get search URL
    search_url = reverse('jobs:run_saved_search', args=[saved_search.id])
    # Try to get site URL from request if available, otherwise use settings or default
    site_url = getattr(settings, 'SITE_URL', None) or 'http://localhost:8000'
    full_url = f"{site_url}{search_url}"
    
    message = f"""Hello {saved_search.recruiter.get_full_name() or saved_search.recruiter.username},

You have {match_count} new candidate{'s' if match_count > 1 else ''} matching your saved search "{saved_search.name}".

"""
    
    # Add search criteria summary
    criteria = []
    if saved_search.skills:
        criteria.append(f"Skills: {saved_search.skills}")
    if saved_search.location:
        criteria.append(f"Location: {saved_search.location}")
    if saved_search.experience:
        criteria.append(f"Experience: {saved_search.experience}")
    
    if criteria:
        message += "Search Criteria:\n"
        message += "\n".join(f"  - {c}" for c in criteria)
        message += "\n\n"
    
    message += f"""View the new matches: {full_url}

You can manage your saved searches here: {site_url}{reverse('jobs:saved_searches')}

Best regards,
Job Search Platform
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@jobplatform.com',
            recipient_list=[saved_search.recruiter.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending notification email: {str(e)}")
        return False

