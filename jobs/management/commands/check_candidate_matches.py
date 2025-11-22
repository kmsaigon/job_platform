"""
Management command to check for new candidate matches in saved searches
and send notifications to recruiters.

Run this command periodically (e.g., via cron) to check for new matches.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from jobs.models import SavedCandidateSearch
from jobs.utils import get_new_matches, send_search_notification


class Command(BaseCommand):
    help = 'Check saved candidate searches for new matches and send notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without sending emails (for testing)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY-RUN mode (no emails will be sent)'))
        
        # Get all saved searches with notifications enabled
        saved_searches = SavedCandidateSearch.objects.filter(
            notifications_enabled=True
        )
        
        total_searches = saved_searches.count()
        self.stdout.write(f'Checking {total_searches} saved searches for new matches...\n')
        
        total_notifications = 0
        total_new_matches = 0
        
        for saved_search in saved_searches:
            self.stdout.write(f'\nChecking: "{saved_search.name}" (ID: {saved_search.id})')
            
            # Get new matches
            new_matches = get_new_matches(saved_search)
            match_count = new_matches.count()
            
            if match_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Found {match_count} new match(es)')
                )
                total_new_matches += match_count
                
                # Send notification if not dry run
                if not dry_run:
                    success = send_search_notification(saved_search, new_matches)
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Notification sent to {saved_search.recruiter.email}')
                        )
                        total_notifications += 1
                        # Update last_notified_at
                        saved_search.last_notified_at = timezone.now()
                        saved_search.save(update_fields=['last_notified_at'])
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Failed to send notification')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  [DRY-RUN] Would send notification to {saved_search.recruiter.email}')
                    )
                    total_notifications += 1
            else:
                self.stdout.write('  No new matches')
            
            # Update last_checked_at
            saved_search.last_checked_at = timezone.now()
            saved_search.save(update_fields=['last_checked_at'])
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✓ Completed checking {total_searches} searches'))
        self.stdout.write(f'  - Total new matches found: {total_new_matches}')
        if not dry_run:
            self.stdout.write(f'  - Notifications sent: {total_notifications}')
        else:
            self.stdout.write(self.style.WARNING(f'  - [DRY-RUN] Would send {total_notifications} notifications'))

