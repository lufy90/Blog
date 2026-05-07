from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import logout
from django.utils.html import strip_tags
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import re
from .models import Entry, Category, FileModel, Comment
from .forms import EntryForm, CommentForm, ReplyForm
from .utils import get_client_ip
from .meaningless_comment_limits import (
    purge_old_meaningless_attempts,
    is_meaningless_rate_limited,
    log_meaningless_attempt,
)
from settings.models import SiteSettings
from django.http import HttpResponse, JsonResponse


def _anonymous_comment_captcha_required(request):
    if request.user.is_authenticated:
        return False
    return SiteSettings.get_value('require_anonymous_comment_captcha', True)


def _first_form_error_message(form, default_message):
    for field_name in form.errors:
        for err in form.errors[field_name]:
            return str(err)
    for err in form.non_field_errors():
        return str(err)
    return default_message


# Post Views
class PostListView(ListView):
    model = Entry
    template_name = 'entries/post_list.html'
    context_object_name = 'posts'
    
    def get_paginate_by(self, queryset):
        """Get pagination from settings"""
        return SiteSettings.get_value('posts_per_page', 10)
    
    def get_queryset(self):
        return Entry.objects.filter(
            visibility='public'
        ).order_by('-created_on')


class PostDetailView(DetailView):
    model = Entry
    template_name = 'entries/post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return Entry.objects.filter(
            visibility='public'
        )
    
    def get(self, request, *args, **kwargs):
        """Override get method to increment view count for public posts"""
        response = super().get(request, *args, **kwargs)
        post = self.get_object()
        
        # Only increment view count for public posts when accessed via public URL
        if post.visibility == 'public':
            post.increment_view_count()
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        # Get previous and next posts
        try:
            # For public posts, order by published_on first, then created_on as fallback
            context['next_post'] = Entry.objects.filter(
                visibility='public'
            ).exclude(
                id=post.id
            ).filter(
                Q(published_on__lt=post.published_on) if post.published_on else Q(created_on__lt=post.created_on)
            ).order_by(
                '-published_on', '-created_on'
            ).first()
        except:
            context['next_post'] = None
            
        try:
            context['previous_post'] = Entry.objects.filter(
                visibility='public'
            ).exclude(
                id=post.id
            ).filter(
                Q(published_on__gt=post.published_on) if post.published_on else Q(created_on__gt=post.created_on)
            ).order_by(
                'published_on', 'created_on'
            ).first()
        except:
            context['previous_post'] = None
        
        # Add settings to context
        context['settings'] = SiteSettings.get_settings()

        use_captcha = _anonymous_comment_captcha_required(self.request)
        context['comment_form'] = CommentForm(
            user=self.request.user,
            use_captcha=use_captcha,
        )
        reply_forms = {}
        for c in post.get_approved_comments():
            reply_forms[c.id] = ReplyForm(
                user=self.request.user,
                parent_comment=c,
                use_captcha=use_captcha,
            )
        context['reply_forms'] = reply_forms
        
        # Indicate this is the public post view
        context['is_my_post_view'] = False
        
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Entry
    template_name = 'entries/post_form.html'
    form_class = EntryForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        if form.instance.visibility == 'public' and not form.instance.published_on:
            form.instance.published_on = timezone.now()
        ip = get_client_ip(self.request)
        form.instance.creation_ip = ip
        form.instance.last_edit_ip = ip
        response = super().form_valid(form)
        # Handle file uploads
        files = self.request.FILES.getlist('files')
        uploaded_files = []
        for uploaded_file in files:
            if uploaded_file:
                file_model = FileModel.objects.create(
                    file=uploaded_file,
                    uploaded_by=self.request.user,
                    original_filename=uploaded_file.name
                )
                self.object.files.add(file_model)
                uploaded_files.append(file_model)
        
        # Store uploaded files in session for template access
        if uploaded_files:
            self.request.session['recently_uploaded_files'] = [
                {'url': f.file.url, 'name': f.original_filename, 'is_image': f.is_image_file}
                for f in uploaded_files
            ]

        # Attach files uploaded by editor before the post was created
        pending_editor_file_ids = self.request.session.get('pending_editor_file_ids', [])
        if pending_editor_file_ids:
            pending_files = FileModel.objects.filter(
                id__in=pending_editor_file_ids,
                uploaded_by=self.request.user
            )
            if pending_files.exists():
                self.object.files.add(*pending_files)
            self.request.session.pop('pending_editor_file_ids', None)
        
        messages.success(self.request, 'Post created successfully!', extra_tags='update-tip')
        # Clear recently uploaded files from session
        if 'recently_uploaded_files' in self.request.session:
            del self.request.session['recently_uploaded_files']
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(author=self.request.user)
        return context


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Entry
    template_name = 'entries/post_form.html'
    form_class = EntryForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        if form.instance.visibility == 'public' and not form.instance.published_on:
            form.instance.published_on = timezone.now()
        form.instance.last_edit_ip = get_client_ip(self.request)
        response = super().form_valid(form)
        # Handle file uploads
        files = self.request.FILES.getlist('files')
        for uploaded_file in files:
            if uploaded_file:
                file_model = FileModel.objects.create(
                    file=uploaded_file,
                    uploaded_by=self.request.user,
                    original_filename=uploaded_file.name
                )
                self.object.files.add(file_model)
        messages.success(self.request, 'Post updated successfully!', extra_tags='update-tip')
        return response
    
    def test_func(self):
        entry = self.get_object()
        return self.request.user == entry.author
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(author=self.request.user)
        return context


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Entry
    template_name = 'entries/post_confirm_delete.html'
    success_url = reverse_lazy('entries:post_list')
    
    def test_func(self):
        entry = self.get_object()
        return self.request.user == entry.author


# User's Posts Views
class MyPostsListView(LoginRequiredMixin, ListView):
    model = Entry
    template_name = 'entries/my_posts.html'
    context_object_name = 'posts'
    
    def get_paginate_by(self, queryset):
        """Get pagination from settings"""
        return SiteSettings.get_value('my_posts_per_page', 20)
    
    def get_queryset(self):
        return Entry.objects.filter(
            author=self.request.user
        ).order_by('-is_pinned', '-created_on')


class MyPostDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Entry
    template_name = 'entries/post_detail.html'
    context_object_name = 'post'
    
    def test_func(self):
        entry = self.get_object()
        return self.request.user == entry.author
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        # Get previous and next posts for the same user
        try:
            context['next_post'] = Entry.objects.filter(
                author=post.author
            ).exclude(
                id=post.id
            ).filter(
                #Q(published_on__lt=post.published_on) if post.published_on else Q(created_on__lt=post.created_on)
                Q(created_on__lt=post.created_on)
            ).order_by(
                '-is_pinned', '-created_on'
            ).first()
        except:
            context['next_post'] = None
            
        try:
            context['previous_post'] = Entry.objects.filter(
                author=post.author
            ).exclude(
                id=post.id
            ).filter(
                #Q(published_on__gt=post.published_on) if post.published_on else Q(created_on__gt=post.created_on)
                Q(created_on__gt=post.created_on)
            ).order_by(
                'is_pinned', 'created_on'
            ).first()
        except:
            context['previous_post'] = None
        
        # Add settings to context
        context['settings'] = SiteSettings.get_settings()

        use_captcha = _anonymous_comment_captcha_required(self.request)
        context['comment_form'] = CommentForm(
            user=self.request.user,
            use_captcha=use_captcha,
        )
        reply_forms = {}
        for c in post.get_approved_comments():
            reply_forms[c.id] = ReplyForm(
                user=self.request.user,
                parent_comment=c,
                use_captcha=use_captcha,
            )
        context['reply_forms'] = reply_forms
        
        # Indicate this is the my post view
        context['is_my_post_view'] = True
        
        return context


# Category and Filtered Views
@login_required
def posts_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, author=request.user)
    posts = Entry.objects.filter(
        author=request.user,
        category=category
    ).order_by('-is_pinned', '-updated_on')
    return render(request, 'entries/posts_by_category.html', {
        'category': category,
        'posts': posts
    })


@login_required
def pinned_posts(request):
    posts = Entry.objects.filter(
        author=request.user,
        is_pinned=True
    ).order_by('-updated_on')
    return render(request, 'entries/pinned_posts.html', {'posts': posts})


@login_required
def all_posts(request):
    """View all user's posts"""
    posts = Entry.objects.filter(
        author=request.user
    ).order_by('-created_on')
    return render(request, 'entries/all_posts.html', {'posts': posts})


@login_required
def custom_logout(request):
    """Custom logout view that handles GET requests"""
    logout(request)
    messages.success(request, 'You have been successfully logged out!')
    return redirect('entries:post_list')


def search_posts(request):
    """Search posts by title, content, category, and mood"""
    # Check if search is enabled
    if not SiteSettings.get_value('enable_search', True):
        messages.warning(request, 'Search functionality is currently disabled.')
        return redirect('entries:post_list')
    
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'public')  # 'public' or 'my_posts'
    
    if not query:
        if search_type == 'my_posts':
            return redirect('entries:my_posts')
        else:
            return redirect('entries:post_list')
    
    # Build the search query
    search_query = Q(title__icontains=query) | Q(content__icontains=query)
    
    if search_type == 'my_posts':
        # Search user's own posts
        if not request.user.is_authenticated:
            return redirect('login')
        
        posts = Entry.objects.filter(
            author=request.user
        ).filter(search_query).order_by('-is_pinned', '-created_on')
        
        # Also search by category name and mood if enabled
        category_posts = Entry.objects.none()
        mood_posts = Entry.objects.none()
        
        if SiteSettings.get_value('enable_categories', True):
            category_posts = Entry.objects.filter(
                author=request.user,
                category__name__icontains=query
            ).order_by('-is_pinned', '-created_on')
        
        if SiteSettings.get_value('enable_mood_tracking', True):
            mood_posts = Entry.objects.filter(
                author=request.user,
                mood__icontains=query
            ).order_by('-is_pinned', '-created_on')
        
        # Combine all results and remove duplicates
        all_posts = list(posts) + list(category_posts) + list(mood_posts)
        seen_ids = set()
        unique_posts = []
        for post in all_posts:
            if post.id not in seen_ids:
                seen_ids.add(post.id)
                unique_posts.append(post)
        
        # Sort by pinned status and creation date
        unique_posts.sort(key=lambda x: (-x.is_pinned, -x.created_on.timestamp()))
        
        template_name = 'entries/search_results.html'
        context = {
            'posts': unique_posts,
            'query': query,
            'search_type': 'my_posts',
            'results_count': len(unique_posts)
        }
    else:
        # Search public posts
        posts = Entry.objects.filter(
            visibility='public'
        ).filter(search_query).order_by('-published_on', '-created_on')
        
        # Also search by category name and mood if enabled
        category_posts = Entry.objects.none()
        mood_posts = Entry.objects.none()
        
        if SiteSettings.get_value('enable_categories', True):
            category_posts = Entry.objects.filter(
                visibility='public',
                category__name__icontains=query
            ).order_by('-published_on', '-created_on')
        
        if SiteSettings.get_value('enable_mood_tracking', True):
            mood_posts = Entry.objects.filter(
                visibility='public',
                mood__icontains=query
            ).order_by('-published_on', '-created_on')
        
        # Combine all results and remove duplicates
        all_posts = list(posts) + list(category_posts) + list(mood_posts)
        seen_ids = set()
        unique_posts = []
        for post in all_posts:
            if post.id not in seen_ids:
                seen_ids.add(post.id)
                unique_posts.append(post)
        
        # Sort by published date and creation date
        unique_posts.sort(key=lambda x: (-x.published_on.timestamp() if x.published_on else -x.created_on.timestamp(), -x.created_on.timestamp()))
        
        template_name = 'entries/search_results.html'
        context = {
            'posts': unique_posts,
            'query': query,
            'search_type': 'public',
            'results_count': len(unique_posts)
        }
    
    return render(request, template_name, context)


@login_required
def toggle_pin(request, pk):
    """Toggle pin status of a post"""
    # Check if pinning is enabled
    if not SiteSettings.get_value('enable_pinning', True):
        messages.warning(request, 'Post pinning functionality is currently disabled.')
        return redirect('entries:my_posts')
    
    post = get_object_or_404(Entry, pk=pk, author=request.user)
    
    # Toggle the pin status
    post.is_pinned = not post.is_pinned
    post.save()
    
    # Set appropriate message
    if post.is_pinned:
        messages.success(request, f'Post "{post.title}" has been pinned!')
    else:
        messages.success(request, f'Post "{post.title}" has been unpinned!')
    
    # Redirect back to the appropriate page
    # Check if we came from a specific page and redirect accordingly
    referer = request.META.get('HTTP_REFERER', '')
    
    if 'my-post/' in referer and '/edit/' not in referer:
        # We're on a post detail page, stay there
        return redirect('entries:my_post_detail', pk=pk)
    elif 'pinned' in referer:
        # We're on the pinned posts page
        return redirect('entries:pinned_posts')
    else:
        # Default to my posts list (including when coming from my-posts list)
        # Preserve page number if it exists in the referer
        page = request.GET.get('page')
        if page:
            return redirect(f'entries:my_posts?page={page}')
        else:
            return redirect('entries:my_posts')


@login_required
def toggle_visibility(request, pk):
    """Toggle visibility status of a post between public and private"""
    post = get_object_or_404(Entry, pk=pk, author=request.user)
    
    # Toggle the visibility status
    if post.visibility == 'public':
        post.visibility = 'private'
        messages.success(request, f'Post "{post.title}" has been made private!')
    else:
        post.visibility = 'public'
        # Set published_on date if making public for the first time
        if not post.published_on:
            post.published_on = timezone.now()
        messages.success(request, f'Post "{post.title}" has been made public!')
    
    post.save()
    
    # Redirect back to the appropriate page
    # Check if we came from a specific page and redirect accordingly
    referer = request.META.get('HTTP_REFERER', '')
    
    if 'my-post/' in referer and '/edit/' not in referer:
        # We're on a post detail page, stay there
        return redirect('entries:my_post_detail', pk=pk)
    else:
        # Default to my posts list (including when coming from my-posts list)
        # Preserve page number if it exists in the referer
        page = request.GET.get('page')
        if page:
            return redirect(f'entries:my_posts?page={page}')
        else:
            return redirect('entries:my_posts')


# Comment Views
@require_POST
def add_comment(request, post_id):
    """Add a comment to a post"""
    # Check if comments are enabled
    if not SiteSettings.get_value('enable_comments', True):
        messages.error(request, 'Comments are currently disabled.', extra_tags='update-error-tip')
        return redirect('entries:post_list')
    
    post = get_object_or_404(Entry, pk=post_id)
    
    # Allow comments on public posts or private posts by the author
    if post.visibility != 'public' and request.user != post.author:
        messages.error(request, 'You cannot comment on private posts.', extra_tags='update-error-tip')
        return redirect('entries:post_list')
    
    # Check if anonymous comments are allowed
    if not request.user.is_authenticated and not SiteSettings.get_value('allow_anonymous_comments', True):
        messages.error(request, 'Anonymous comments are not allowed. Please log in to comment.', extra_tags='update-error-tip')
        return redirect('entries:post_detail', slug=post.slug)
    
    use_captcha = _anonymous_comment_captcha_required(request)
    form = CommentForm(request.POST, user=request.user, use_captcha=use_captcha)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.entry = post
        if SiteSettings.comment_content_blocked_by_keywords(comment.content or ''):
            messages.error(request, 'Your comment contains blocked words and was not posted.', extra_tags='update-error-tip')
        elif SiteSettings.comment_content_is_meaningless(comment.content or ''):
            ip = get_client_ip(request)
            purge_old_meaningless_attempts()
            if is_meaningless_rate_limited(ip):
                messages.error(
                    request,
                    'Too many low-quality comment attempts from your network. Please wait before trying again.',
                    extra_tags='update-error-tip',
                )
            else:
                log_meaningless_attempt(post, comment.content, ip)
                messages.error(request, 'Your comment looks meaningless or like random text and was not posted.', extra_tags='update-error-tip')
        else:
            # Set approval status based on settings
            if SiteSettings.get_value('require_comment_approval', False):
                comment.is_approved = False
                messages.success(request, 'Your comment has been submitted and is awaiting approval.', extra_tags='update-tip')
            else:
                comment.is_approved = True
                messages.success(request, 'Your comment has been added successfully!', extra_tags='update-tip')
            
            comment.ip_address = get_client_ip(request)
            comment.save()
    else:
        msg = _first_form_error_message(
            form,
            'There was an error with your comment. Please try again.',
        )
        messages.error(request, msg, extra_tags='update-error-tip')
    
    # Redirect to appropriate post detail page
    if post.visibility == 'public':
        return redirect('entries:post_detail', slug=post.slug)
    else:
        return redirect('entries:my_post_detail', pk=post.pk)


@require_POST
def add_reply(request, comment_id):
    """Add a reply to a comment"""
    # Check if comments and replies are enabled
    if not SiteSettings.get_value('enable_comments', True):
        messages.error(request, 'Comments are currently disabled.', extra_tags='update-error-tip')
        return redirect('entries:post_list')
    
    if not SiteSettings.get_value('enable_comment_replies', True):
        messages.error(request, 'Comment replies are currently disabled.', extra_tags='update-error-tip')
        return redirect('entries:post_list')
    
    parent_comment = get_object_or_404(Comment, pk=comment_id, is_approved=True)
    post = parent_comment.entry
    
    # Allow replies on public posts or private posts by the author
    if post.visibility != 'public' and request.user != post.author:
        messages.error(request, 'You cannot reply to comments on private posts.', extra_tags='update-error-tip')
        return redirect('entries:post_list')
    
    # Check if anonymous replies are allowed
    if not request.user.is_authenticated and not SiteSettings.get_value('allow_anonymous_comments', True):
        messages.error(request, 'Anonymous replies are not allowed. Please log in to reply.', extra_tags='update-error-tip')
        if post.visibility == 'public':
            return redirect('entries:post_detail', slug=post.slug)
        else:
            return redirect('entries:my_post_detail', pk=post.pk)
    
    use_captcha = _anonymous_comment_captcha_required(request)
    form = ReplyForm(
        request.POST,
        user=request.user,
        parent_comment=parent_comment,
        use_captcha=use_captcha,
    )
    if form.is_valid():
        reply = form.save(commit=False)
        reply.entry = post
        if SiteSettings.comment_content_blocked_by_keywords(reply.content or ''):
            messages.error(request, 'Your reply contains blocked words and was not posted.', extra_tags='update-error-tip')
        elif SiteSettings.comment_content_is_meaningless(reply.content or ''):
            ip = get_client_ip(request)
            purge_old_meaningless_attempts()
            if is_meaningless_rate_limited(ip):
                messages.error(
                    request,
                    'Too many low-quality reply attempts from your network. Please wait before trying again.',
                    extra_tags='update-error-tip',
                )
            else:
                log_meaningless_attempt(post, reply.content, ip, parent_comment=parent_comment)
                messages.error(request, 'Your reply looks meaningless or like random text and was not posted.', extra_tags='update-error-tip')
        else:
            # Set approval status based on settings
            if SiteSettings.get_value('require_comment_approval', False):
                reply.is_approved = False
                messages.success(request, 'Your reply has been submitted and is awaiting approval.', extra_tags='update-tip')
            else:
                reply.is_approved = True
                messages.success(request, 'Your reply has been added successfully!', extra_tags='update-tip')
            
            reply.ip_address = get_client_ip(request)
            reply.save()
    else:
        msg = _first_form_error_message(
            form,
            'There was an error with your reply. Please try again.',
        )
        messages.error(request, msg, extra_tags='update-error-tip')
    
    # Redirect to appropriate post detail page
    if post.visibility == 'public':
        return redirect('entries:post_detail', slug=post.slug)
    else:
        return redirect('entries:my_post_detail', pk=post.pk)


@login_required
def delete_comment(request, comment_id):
    """Delete a comment (only by comment author or post author)"""
    comment = get_object_or_404(Comment, pk=comment_id)
    post = comment.entry
    
    # Check if user can delete this comment
    can_delete = (
        request.user == comment.author or 
        request.user == post.author or 
        request.user.is_staff
    )
    
    if not can_delete:
        messages.error(request, 'You do not have permission to delete this comment.', extra_tags='update-error-tip')
        if post.visibility == 'public':
            return redirect('entries:post_detail', slug=post.slug)
        else:
            return redirect('entries:my_post_detail', pk=post.pk)
    
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Comment deleted successfully.', extra_tags='update-tip')
        if post.visibility == 'public':
            return redirect('entries:post_detail', slug=post.slug)
        else:
            return redirect('entries:my_post_detail', pk=post.pk)
    
    # GET request - show confirmation
    return render(request, 'entries/comment_confirm_delete.html', {
        'comment': comment,
        'post': post
    })


@login_required
def edit_comment(request, comment_id):
    """Edit a comment (only by comment author)"""
    comment = get_object_or_404(Comment, pk=comment_id)
    post = comment.entry
    
    # Only comment author can edit
    if request.user != comment.author:
        messages.error(request, 'You can only edit your own comments.', extra_tags='update-error-tip')
        if post.visibility == 'public':
            return redirect('entries:post_detail', slug=post.slug)
        else:
            return redirect('entries:my_post_detail', pk=post.pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comment updated successfully.', extra_tags='update-tip')
            if post.visibility == 'public':
                return redirect('entries:post_detail', slug=post.slug)
            else:
                return redirect('entries:my_post_detail', pk=post.pk)
    else:
        form = CommentForm(instance=comment, user=request.user)
    
    return render(request, 'entries/comment_form.html', {
        'form': form,
        'comment': comment,
        'post': post
    })


@login_required
@require_POST
def upload_post_files(request, post_id):
    """Upload files for an existing post and return refreshed attachment data."""
    post = get_object_or_404(Entry, pk=post_id)

    if request.user != post.author:
        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

    files = request.FILES.getlist('files')
    if not files:
        return JsonResponse({'success': False, 'error': 'No files selected.'}, status=400)

    uploaded_count = 0
    for uploaded_file in files:
        if uploaded_file:
            file_model = FileModel.objects.create(
                file=uploaded_file,
                uploaded_by=request.user,
                original_filename=uploaded_file.name
            )
            post.files.add(file_model)
            uploaded_count += 1

    refreshed_files = []
    for file_obj in post.files.all():
        refreshed_files.append({
            'id': file_obj.id,
            'name': file_obj.original_filename,
            'url': file_obj.file.url,
            'is_image': file_obj.is_image_file,
            'size_mb': file_obj.file_size_mb,
            'delete_url': reverse('entries:delete_file', kwargs={'post_id': post.id, 'file_id': file_obj.id}),
        })

    return JsonResponse({
        'success': True,
        'uploaded_count': uploaded_count,
        'files': refreshed_files
    })


@login_required
@require_POST
def upload_editor_file(request):
    """Upload editor file(s) and return URL data for insert operations."""
    uploaded_files = request.FILES.getlist('files')
    if not uploaded_files:
        single_file = request.FILES.get('file')
        if single_file:
            uploaded_files = [single_file]

    if not uploaded_files:
        return JsonResponse({'success': False, 'error': 'No file provided.'}, status=400)

    post_id = request.POST.get('post_id')
    refreshed_files = []
    post = None
    if post_id:
        try:
            post = Entry.objects.get(pk=int(post_id), author=request.user)
        except (Entry.DoesNotExist, ValueError):
            return JsonResponse({'success': False, 'error': 'Post not found or no permission.'}, status=403)

    pending_editor_file_ids = request.session.get('pending_editor_file_ids', [])
    saved_files = []

    for uploaded_file in uploaded_files:
        file_model = FileModel.objects.create(
            file=uploaded_file,
            uploaded_by=request.user,
            original_filename=uploaded_file.name
        )
        saved_files.append(file_model)
        if post:
            post.files.add(file_model)
        else:
            pending_editor_file_ids.append(file_model.id)

    if not post:
        request.session['pending_editor_file_ids'] = list(set(pending_editor_file_ids))
    else:
        for file_obj in post.files.all():
            refreshed_files.append({
                'id': file_obj.id,
                'name': file_obj.original_filename,
                'url': file_obj.file.url,
                'is_image': file_obj.is_image_file,
                'size_mb': file_obj.file_size_mb,
                'delete_url': reverse('entries:delete_file', kwargs={'post_id': post.id, 'file_id': file_obj.id}),
            })

    return JsonResponse({
        'success': True,
        'uploaded_count': len(saved_files),
        'file': {
            'id': saved_files[0].id,
            'name': saved_files[0].original_filename,
            'url': saved_files[0].file.url,
            'is_image': saved_files[0].is_image_file
        } if saved_files else None,
        'uploaded_files': [
            {
                'id': file_obj.id,
                'name': file_obj.original_filename,
                'url': file_obj.file.url,
                'is_image': file_obj.is_image_file,
                'file_type': file_obj.file_type,
            }
            for file_obj in saved_files
        ],
        'files': refreshed_files
    })


@login_required
def debug_files(request, post_id):
    """Debug view to check file types and video detection"""
    try:
        post = Entry.objects.get(id=post_id, author=request.user)
    except Entry.DoesNotExist:
        return HttpResponse("Post not found", status=404)
    
    debug_info = {
        'post_title': post.title,
        'post_id': post.id,
        'all_files': [],
        'video_files': [],
        'image_files': [],
        'other_files': [],
    }
    
    for file_obj in post.files.all():
        file_info = {
            'id': file_obj.id,
            'original_filename': file_obj.original_filename,
            'file_type': file_obj.file_type,
            'file_path': file_obj.file.name if file_obj.file else None,
            'is_video': file_obj.is_video,
            'is_image': file_obj.is_image,
            'video_mime_type': file_obj.video_mime_type,
        }
        debug_info['all_files'].append(file_info)
        
        if file_obj.is_video:
            debug_info['video_files'].append(file_info)
        elif file_obj.is_image:
            debug_info['image_files'].append(file_info)
        else:
            debug_info['other_files'].append(file_info)
    
    # Also check the properties
    debug_info['attached_videos_count'] = post.attached_videos.count()
    debug_info['attached_images_count'] = post.attached_images.count()
    debug_info['attached_files_count'] = post.attached_files.count()
    
    return JsonResponse(debug_info)


@login_required
def delete_file(request, post_id, file_id):
    """Delete an attached file from a post"""
    post = get_object_or_404(Entry, pk=post_id)
    file_model = get_object_or_404(FileModel, pk=file_id)
    
    # Check if user owns the post
    if request.user != post.author:
        messages.error(request, "You don't have permission to delete files from this post.")
        return redirect('entries:my_post_detail', pk=post_id)
    
    # Check if file is attached to this post
    if file_model not in post.files.all():
        messages.error(request, "File not found in this post.")
        return redirect('entries:my_post_detail', pk=post_id)
    
    try:
        # Remove file from post (but don't delete the file model yet)
        post.files.remove(file_model)
        
        # Delete the actual file and file model
        file_model.file.delete(save=False)  # Delete the file from storage
        file_model.delete()  # Delete the database record
        
        messages.success(request, f"File '{file_model.original_filename}' has been deleted successfully.")
    except Exception as e:
        messages.error(request, f"Error deleting file: {str(e)}")
    
    # Check if the request came from the edit page
    referer = request.META.get('HTTP_REFERER', '')
    if 'edit' in referer or 'post_form' in referer:
        # Redirect back to edit page
        return redirect('entries:post_update', pk=post_id)
    else:
        # Redirect to post detail page
        if post.visibility == 'public':
            return redirect('entries:post_detail', slug=post.slug)
        else:
            return redirect('entries:my_post_detail', pk=post_id)
