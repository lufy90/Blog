from django.contrib import admin
from .models import SiteSettings, BlockedIPAddress


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Simple admin interface for SiteSettings"""
    
    list_display = ['site_name', 'contact_email']
    readonly_fields = ['created_on', 'updated_on']
    
    fieldsets = (
        ('Site Information', {
            'fields': ('site_name', 'site_description', 'site_tagline', 'site_icon')
        }),
        ('Content Settings', {
            'fields': ('posts_per_page', 'my_posts_per_page', 'search_results_per_page')
        }),
        ('Display Settings', {
            'fields': (
                'show_author_info', 'show_post_dates', 'show_categories', 
                'show_mood_badges', 'show_priority_badges', 'show_attached_files_public', 'theme'
            )
        }),
        ('Footer Information', {
            'fields': ('copyright_text', 'footer_text', 'powered_by_text')
        }),
        ('Feature Toggles', {
            'fields': (
                'enable_search', 'enable_categories', 'enable_file_uploads',
                'enable_mood_tracking', 'enable_priority_tracking', 'enable_pinning'
            )
        }),
        ('Comment Settings', {
            'fields': (
                'enable_comments', 'allow_anonymous_comments', 'require_comment_approval',
                'enable_comment_replies', 'max_comment_length', 'comment_sensitive_keywords',
                'block_meaningless_comments',
                'meaningless_rate_limit_max_attempts',
                'meaningless_rate_limit_window_minutes',
                'meaningless_attempt_retention_days',
            ),
            'description': 'Configure comment functionality and moderation settings.'
        }),
    )


@admin.register(BlockedIPAddress)
class BlockedIPAddressAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'note', 'created_on']
    search_fields = ['ip_address', 'note']
    ordering = ['-created_on']
