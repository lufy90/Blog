from django import forms
from .models import SiteSettings


class SiteSettingsForm(forms.ModelForm):
    """Form for managing site settings"""
    
    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'site_description', 'site_tagline', 'site_icon',
            'contact_email', 'contact_phone',
            'twitter_url', 'facebook_url', 'instagram_url', 'linkedin_url', 'github_url',
            'posts_per_page', 'my_posts_per_page', 'search_results_per_page',
            'show_author_info', 'show_post_dates', 'show_categories', 
            'show_mood_badges', 'show_priority_badges', 'show_attached_files_public', 'theme',
            'copyright_text', 'footer_text', 'powered_by_text', 'powered_by_url',
            'meta_keywords', 'meta_description', 'google_analytics_id',
            'enable_file_uploads', 'enable_image_compression', 'image_compression_limit_mb', 'image_compression_quality',
            'enable_search', 'enable_categories',
            'enable_mood_tracking', 'enable_priority_tracking', 'enable_pinning',
            'enable_comments', 'allow_anonymous_comments', 'require_comment_approval',
            'enable_comment_replies', 'max_comment_length', 'comment_sensitive_keywords',
            'block_meaningless_comments',
            'meaningless_rate_limit_max_attempts',
            'meaningless_rate_limit_window_minutes',
            'meaningless_attempt_retention_days',
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control'}),
            'site_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'site_tagline': forms.TextInput(attrs={'class': 'form-control'}),
            'site_icon': forms.FileInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control'}),
            'posts_per_page': forms.NumberInput(attrs={'class': 'form-control'}),
            'my_posts_per_page': forms.NumberInput(attrs={'class': 'form-control'}),
            'search_results_per_page': forms.NumberInput(attrs={'class': 'form-control'}),
            'copyright_text': forms.TextInput(attrs={'class': 'form-control'}),
            'footer_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'powered_by_text': forms.TextInput(attrs={'class': 'form-control'}),
            'powered_by_url': forms.URLInput(attrs={'class': 'form-control'}),
            'meta_keywords': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'google_analytics_id': forms.TextInput(attrs={'class': 'form-control'}),
            'theme': forms.Select(attrs={'class': 'form-control'}),
            'image_compression_limit_mb': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'image_compression_quality': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '100'}),
            'max_comment_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'comment_sensitive_keywords': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'meaningless_rate_limit_max_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'meaningless_rate_limit_window_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'meaningless_attempt_retention_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to checkbox fields
        for field_name in ['show_author_info', 'show_post_dates', 'show_categories', 
                          'show_mood_badges', 'show_priority_badges', 'show_attached_files_public', 'enable_search', 
                          'enable_categories', 'enable_file_uploads', 'enable_image_compression', 'enable_mood_tracking', 
                          'enable_priority_tracking', 'enable_pinning', 'enable_comments',
                          'allow_anonymous_comments', 'require_comment_approval', 'enable_comment_replies',
                          'block_meaningless_comments']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'form-check-input'})
    
    def clean_site_icon(self):
        """Validate site icon file"""
        icon = self.cleaned_data.get('site_icon')
        if icon:
            # Check file size (max 2MB)
            if icon.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Icon file size must be less than 2MB.")
            
            # Check file type by extension
            allowed_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.ico']
            file_extension = icon.name.lower()
            if not any(file_extension.endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError("Please upload a valid image file (PNG, JPEG, GIF, ICO).")
        
        return icon 