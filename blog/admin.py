from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

# Import your models
from settings.models import SiteSettings, BlockedIPAddress
from settings.admin import SiteSettingsAdmin, BlockedIPAddressAdmin
from entries.models import Entry, Category, FileModel, Comment, MeaninglessCommentAttempt
from entries.admin import (
    EntryAdmin,
    CategoryAdmin,
    FileModelAdmin,
    CommentAdmin,
    MeaninglessCommentAttemptAdmin,
)

class BlogAdminSite(AdminSite):
    """Custom admin site for the blog"""
    
    # Customize admin site
    site_header = "SimpleBlog Administration"
    site_title = "SimpleBlog Admin"
    index_title = "Welcome to Blog Administration"
    
    # Custom CSS class for the admin site
    site_url = "/"
    
    def each_context(self, request):
        """Add custom context to all admin pages"""
        context = super().each_context(request)
        context['site_header'] = self.site_header
        context['site_title'] = self.site_title
        return context

# Create custom admin site instance
admin_site = BlogAdminSite(name='blog_admin')

# Register default Django admin models with proper admin classes
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)

# Register your models with the custom admin site
admin_site.register(SiteSettings, SiteSettingsAdmin)
admin_site.register(BlockedIPAddress, BlockedIPAddressAdmin)
admin_site.register(Entry, EntryAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(FileModel, FileModelAdmin)
admin_site.register(Comment, CommentAdmin)
admin_site.register(MeaninglessCommentAttempt, MeaninglessCommentAttemptAdmin)
