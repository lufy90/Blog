from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Q
import os


def file_upload_path(instance, filename):
    """Generate file path for uploaded files"""
    # Create path like: media/files/2024/01/15/filename.ext
    date_path = timezone.now().strftime('%Y/%m/%d')
    return os.path.join('files', date_path, filename)


class FileModel(models.Model):
    """Model to store uploaded files"""
    file = models.FileField(upload_to=file_upload_path)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50, blank=True)
    file_size = models.IntegerField(default=0)  # Size in bytes
    is_image_file = models.BooleanField(default=False)  # Database field for admin filtering
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.original_filename
    
    def save(self, *args, **kwargs):
        if not self.original_filename and self.file:
            self.original_filename = os.path.basename(self.file.name)
        
        if not self.file_type and self.file:
            # Get file extension
            ext = os.path.splitext(self.file.name)[1].lower()
            self.file_type = ext
        
        if not self.file_size and self.file:
            try:
                self.file_size = self.file.size
            except:
                pass
        
        # Set is_image_file based on file type
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        self.is_image_file = self.file_type.lower() in image_extensions
        
        super().save(*args, **kwargs)
    
    @property
    def is_image(self):
        """Check if file is an image (property for backward compatibility)"""
        return self.is_image_file
    
    @property
    def is_video(self):
        """Check if file is a video"""
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.mpeg']
        return self.file_type.lower() in [ext.lower() for ext in video_extensions] if self.file_type else False
    
    @property
    def video_mime_type(self):
        """Get the MIME type for video files"""
        if not self.is_video:
            return None
        
        mime_types = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.wmv': 'video/x-ms-wmv',
            '.flv': 'video/x-flv',
            '.webm': 'video/webm',
            '.mkv': 'video/x-matroska',
            '.m4v': 'video/x-m4v',
            '.mpeg': 'video/mpeg',
        }
        return mime_types.get(self.file_type.lower(), 'video/mp4')
    
    @property
    def file_url(self):
        """Get the URL for the file"""
        return self.file.url if self.file else None
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)


class Category(models.Model):
    name = models.CharField(max_length=100)
    desc = models.CharField(max_length=1024, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entry_categories')
    created_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        unique_together = ['name', 'author']
    
    def __str__(self):
        return self.name


class Entry(models.Model):
    MOOD_CHOICES = [
        ('happy', 'Happy'),
        ('sad', 'Sad'),
        ('excited', 'Excited'),
        ('calm', 'Calm'),
        ('anxious', 'Anxious'),
        ('neutral', 'Neutral'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    VISIBILITY_CHOICES = [
        ('private', 'Private'),
        ('public', 'Public'),
    ]
    
    # Core fields
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entries')
    title = models.CharField(max_length=200, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    published_on = models.DateTimeField(null=True, blank=True)
    
    date = models.DateField(null=True, blank=True)  # For diary entries
    mood = models.CharField(max_length=10, choices=MOOD_CHOICES, blank=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='private')
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='entries')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_pinned = models.BooleanField(default=False)
    
    # Files relationship
    files = models.ManyToManyField(FileModel, blank=True, related_name='entries')
    
    # Statistics
    view_count = models.PositiveIntegerField(default=0, help_text="Number of views for public posts")
    creation_ip = models.CharField(max_length=45, blank=True)
    last_edit_ip = models.CharField(max_length=45, blank=True)
    
    # Common fields
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-updated_on']
        verbose_name_plural = 'Entries'
        indexes = [
            models.Index(fields=['author', '-updated_on']),
            models.Index(fields=['date', '-created_on']),
            models.Index(fields=['category', '-updated_on']),
        ]
    
    def __str__(self):
        return self.title or f"Post {self.id}"
    
    def save(self, *args, **kwargs):
        # Auto-generate slug for posts
        if not self.slug:
            if self.title:
                self.slug = slugify(self.title, allow_unicode=True)
            else:
                # Use timestamp if no title
                self.slug = slugify(f"post-{timezone.now().strftime('%Y%m%d-%H%M%S')}")

        if not self._state.adding:
            original = Entry.objects.get(pk=self.pk)
            if not original.is_published and self.is_published:
                self.published_on = timezone.now()
            elif original.is_published and not self.is_published:
                self.published_on = None
            else:
                self.published_on = original.published_on

        # Set date to created_on date if not set
        if not self.date:
            self.date = self.created_on.date() if self.created_on else timezone.now().date()

        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get the canonical URL for this post (public URL if published, private URL if not)"""
        if self.visibility == 'public':
            return self.get_public_url()
        else:
            return self.get_private_url()
    
    def get_public_url(self):
        """Get the public URL for this post (post/<slug>/)"""
        return reverse('entries:post_detail', args=[self.slug])
    
    def get_private_url(self):
        """Get the private URL for this post (my-post/<pk>/)"""
        return reverse('entries:my_post_detail', args=[self.pk])
    
    @property
    def is_published(self):
        return self.visibility == 'public'
    
    @property
    def attached_images(self):
        """Get all attached image files"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        q_objects = Q()
        for ext in image_extensions:
            q_objects |= Q(file_type__iexact=ext)
        return self.files.filter(q_objects)
    
    @property
    def attached_videos(self):
        """Get all attached video files"""
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.mpeg']
        q_objects = Q()
        for ext in video_extensions:
            q_objects |= Q(file_type__iexact=ext)
        # Also try exact matches for common cases
        q_objects |= Q(file_type__in=video_extensions)
        return self.files.filter(q_objects)
    
    @property
    def attached_files(self):
        """Get all attached non-image and non-video files"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.mpeg']
        exclude_extensions = image_extensions + video_extensions
        q_objects = Q()
        for ext in exclude_extensions:
            q_objects |= Q(file_type__iexact=ext)
        return self.files.exclude(q_objects)
    
    def get_approved_comments(self):
        """Get all approved top-level comments for this post, newest first."""
        return self.comments.filter(is_approved=True, parent=None).order_by('-created_on')
    
    @property
    def comment_count(self):
        """Get the total number of approved comments"""
        return self.comments.filter(is_approved=True).count()
    
    def increment_view_count(self):
        """Increment the view count for public posts only"""
        if self.visibility == 'public':
            self.view_count += 1
            self.save(update_fields=['view_count'])
    
    @property
    def formatted_view_count(self):
        """Get formatted view count with appropriate suffix"""
        if self.view_count == 0:
            return "0 views"
        elif self.view_count == 1:
            return "1 view"
        else:
            return f"{self.view_count} views"


class Comment(models.Model):
    """Model for blog post comments"""
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    author_name = models.CharField(max_length=100, blank=True)  # For anonymous comments
    author_email = models.EmailField(blank=True)  # For anonymous comments
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_approved = models.BooleanField(default=True)  # Set to False for moderation
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    ip_address = models.CharField(max_length=45, blank=True)
    
    class Meta:
        ordering = ['-created_on']
        indexes = [
            models.Index(fields=['entry', 'created_on']),
            models.Index(fields=['is_approved', 'created_on']),
        ]
    
    def __str__(self):
        return f"Comment by {self.get_author_display()} on {self.entry.title}"
    
    def get_author_display(self):
        """Get the display name for the comment author"""
        if self.author:
            return self.author.username
        return self.author_name or 'Anonymous'
    
    def get_replies(self):
        """Get all approved replies to this comment, oldest first (thread order)."""
        return self.replies.filter(is_approved=True).order_by('created_on')
    
    @property
    def is_reply(self):
        """Check if this comment is a reply to another comment"""
        return self.parent is not None
    
    @property
    def is_anonymous(self):
        """Check if this is an anonymous comment"""
        return self.author is None


class MeaninglessCommentAttempt(models.Model):
    """Logged rejected meaningless comment text (not a public Comment) for IP rate limiting."""

    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='meaningless_attempts')
    parent_comment = models.ForeignKey(
        Comment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='meaningless_reply_attempts',
        help_text='Set when the attempt was a reply to this comment.',
    )
    content = models.TextField()
    ip_address = models.CharField(max_length=45, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']
        indexes = [
            models.Index(fields=['ip_address', 'created_on']),
            models.Index(fields=['created_on']),
        ]

    def __str__(self):
        return f'Meaningless attempt from {self.ip_address or "unknown"} on {self.entry_id}'