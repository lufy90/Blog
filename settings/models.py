from django.db import models
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


class SiteSettings(models.Model):
    """Model to store site-wide settings"""
    
    # Site Information
    site_name = models.CharField(max_length=100, default="SimpleBlog", help_text="The name of your blog/site")
    site_description = models.TextField(blank=True, help_text="Brief description of your site")
    site_tagline = models.CharField(max_length=200, blank=True, help_text="A short tagline for your site")
    site_icon = models.ImageField(upload_to='site_icons/', blank=True, null=True, help_text="Site favicon/icon (recommended: 32x32 or 64x64 pixels)")
    
    # Contact Information
    contact_email = models.EmailField(blank=True, help_text="Contact email address")
    contact_phone = models.CharField(max_length=20, blank=True, help_text="Contact phone number")
    
    # Social Media
    twitter_url = models.URLField(blank=True, help_text="Twitter profile URL")
    facebook_url = models.URLField(blank=True, help_text="Facebook page URL")
    instagram_url = models.URLField(blank=True, help_text="Instagram profile URL")
    linkedin_url = models.URLField(blank=True, help_text="LinkedIn profile URL")
    github_url = models.URLField(blank=True, help_text="GitHub profile URL")
    
    # Content Settings
    posts_per_page = models.PositiveIntegerField(default=10, help_text="Number of posts to show per page")
    my_posts_per_page = models.PositiveIntegerField(default=20, help_text="Number of posts to show per page in My Posts")
    search_results_per_page = models.PositiveIntegerField(default=15, help_text="Number of search results per page")
    
    # Display Settings
    show_author_info = models.BooleanField(default=True, help_text="Show author information on posts")
    show_post_dates = models.BooleanField(default=True, help_text="Show post creation dates")
    show_categories = models.BooleanField(default=True, help_text="Show category information")
    show_mood_badges = models.BooleanField(default=True, help_text="Show mood badges on posts")
    show_priority_badges = models.BooleanField(default=True, help_text="Show priority badges on posts")
    
    # Theme Settings
    THEME_CHOICES = [
        ('default', 'Default Blue'),
        ('green', 'Forest Green'),
        ('purple', 'Royal Purple'),
        ('orange', 'Sunset Orange'),
        ('red', 'Crimson Red'),
        ('teal', 'Ocean Teal'),
        ('dark', 'Dark Mode'),
        ('light', 'Light Mode'),
    ]
    theme = models.CharField(
        max_length=20, 
        choices=THEME_CHOICES, 
        default='default',
        help_text="Choose the color theme for your site"
    )
    
    # Footer Information
    copyright_text = models.CharField(max_length=200, default="© 2025 SimpleBlog. All rights reserved.", help_text="Copyright declaration")
    footer_text = models.TextField(blank=True, help_text="Additional footer text")
    powered_by_text = models.CharField(max_length=100, default="SimpleBlog", help_text="Text to show in footer")
    powered_by_url = models.URLField(blank=True, default="https://github.com/lufy90/SimpleBlog", help_text="URL for the powered by link (optional)")
    
    # SEO Settings
    meta_keywords = models.TextField(blank=True, help_text="Default meta keywords for SEO")
    meta_description = models.TextField(blank=True, help_text="Default meta description for SEO")
    google_analytics_id = models.CharField(max_length=50, blank=True, help_text="Google Analytics tracking ID")
    
    # File Upload Settings
    enable_file_uploads = models.BooleanField(default=True, help_text="Enable file upload functionality")
    enable_image_compression = models.BooleanField(default=True, help_text="Enable automatic image compression")
    image_compression_limit_mb = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.0, 
        help_text="Compress images larger than this size (MB)"
    )
    image_compression_quality = models.PositiveIntegerField(
        default=85, 
        help_text="Image compression quality (1-100, higher = better quality)"
    )
    
    # Feature Toggles
    enable_search = models.BooleanField(default=True, help_text="Enable search functionality")
    enable_categories = models.BooleanField(default=True, help_text="Enable category functionality")
    enable_mood_tracking = models.BooleanField(default=True, help_text="Enable mood tracking")
    enable_priority_tracking = models.BooleanField(default=True, help_text="Enable priority tracking")
    enable_pinning = models.BooleanField(default=True, help_text="Enable post pinning functionality")
    
    # Comment Settings
    enable_comments = models.BooleanField(default=True, help_text="Enable comment functionality")
    allow_anonymous_comments = models.BooleanField(default=True, help_text="Allow anonymous users to post comments")
    require_comment_approval = models.BooleanField(default=False, help_text="Require admin approval for new comments")
    enable_comment_replies = models.BooleanField(default=True, help_text="Allow users to reply to comments")
    max_comment_length = models.PositiveIntegerField(default=1000, help_text="Maximum length for comments (characters)")
    comment_sensitive_keywords = models.TextField(
        blank=True,
        help_text="Comments containing any of these words or phrases are rejected. One per line, or comma-separated.",
    )
    block_meaningless_comments = models.BooleanField(
        default=False,
        help_text="Reject comments that look like random keys, extreme repetition, or strings with almost no letters.",
    )
    meaningless_rate_limit_max_attempts = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        help_text="Max meaningless comment attempts logged per IP within the window before further meaningless posts are blocked.",
    )
    meaningless_rate_limit_window_minutes = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(1)],
        help_text="Sliding window (minutes) for counting meaningless attempts per IP.",
    )
    meaningless_attempt_retention_days = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        help_text="Delete stored meaningless attempt logs older than this many days (also runs when a meaningless comment is checked).",
    )
    
    # Display Settings
    show_attached_files_public = models.BooleanField(default=True, help_text="Show attached files section on public post detail pages")
    
    # Timestamps
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return f"Site Settings - {self.site_name}"
    
    def clean(self):
        """Validate that only one instance exists"""
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError("Only one SiteSettings instance is allowed.")
    
    def save(self, *args, **kwargs):
        """Override save to clear cache"""
        # Clear cache when settings are updated
        cache.delete('site_settings')
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get settings from cache or database"""
        try:
            settings = cache.get('site_settings')
            if settings is None:
                settings = cls.objects.first()
                if settings:
                    cache.set('site_settings', settings, 3600)  # Cache for 1 hour
                else:
                    # Create default settings if none exist
                    settings = cls.objects.create()
                    cache.set('site_settings', settings, 3600)
            return settings
        except Exception as e:
            print(f"Error getting settings: {e}")
            return None
    
    @classmethod
    def get_value(cls, key, default=None):
        """Get a specific setting value"""
        settings = cls.get_settings()
        if settings:
            return getattr(settings, key, default)
        return default

    @classmethod
    def get_comment_sensitive_keyword_list(cls):
        """Return non-empty keyword strings from site settings (case matching applied later)."""
        settings = cls.get_settings()
        if not settings:
            return []
        raw = getattr(settings, 'comment_sensitive_keywords', '') or ''
        keywords = []
        normalized = raw.replace('\r\n', '\n').replace('\r', '\n')
        for line in normalized.split('\n'):
            for piece in line.split(','):
                w = piece.strip()
                if w:
                    keywords.append(w)
        return keywords

    @classmethod
    def comment_content_blocked_by_keywords(cls, content):
        """True if content contains any configured sensitive substring (case-insensitive)."""
        if content is None:
            content = ''
        keywords = cls.get_comment_sensitive_keyword_list()
        if not keywords:
            return False
        lowered = content.lower()
        for kw in keywords:
            if kw.lower() in lowered:
                return True
        return False

    @classmethod
    def comment_content_is_meaningless(cls, content):
        """True when meaningless-comment blocking is enabled and heuristics match."""
        if not cls.get_value('block_meaningless_comments', False):
            return False
        from settings.comment_meaningless import is_meaningless_comment_text
        return is_meaningless_comment_text(content)


class BlockedIPAddress(models.Model):
    """Exact client IP matches are rejected for all site requests (see IPBlacklistMiddleware)."""

    ip_address = models.CharField(max_length=45, unique=True)
    note = models.CharField(max_length=200, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']
        verbose_name = 'Blocked IP address'
        verbose_name_plural = 'Blocked IP addresses'

    def __str__(self):
        return self.ip_address

    def clean(self):
        super().clean()
        if not (self.ip_address or '').strip():
            raise ValidationError({'ip_address': 'IP address cannot be empty.'})

    def save(self, *args, **kwargs):
        self.ip_address = (self.ip_address or '').strip()[:45]
        super().save(*args, **kwargs)
