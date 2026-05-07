from django import forms
from django.contrib.auth.models import User
from captcha.fields import CaptchaField, CaptchaTextInput
from settings.models import SiteSettings
from .models import Entry, Category, FileModel, Comment


class MultipleFileInput(forms.FileInput):
    """Custom widget for multiple file uploads"""
    def __init__(self, attrs=None):
        default_attrs = {'multiple': 'multiple'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
    
    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        return files.get(name)


class MultipleFileField(forms.FileField):
    """Custom field for multiple file uploads"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)
    
    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = []
            for each_file in data:
                if each_file:
                    result.append(single_file_clean(each_file, initial))
            return result
        else:
            return single_file_clean(data, initial)


class EntryForm(forms.ModelForm):
    """Form for creating and editing entries"""
    
    class Meta:
        model = Entry
        fields = ['title', 'content', 'visibility', 'category', 'priority', 'is_pinned', 'mood']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mood': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Filter categories by user
            self.fields['category'].queryset = Category.objects.filter(author=user)


class FileUploadForm(forms.ModelForm):
    """Form for uploading files"""
    
    class Meta:
        model = FileModel
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional description'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.uploaded_by = self.user
        if commit:
            instance.save()
        return instance


class CommentForm(forms.ModelForm):
    """Form for creating comments"""
    author_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name (optional if logged in)'
        }),
        help_text='Required for anonymous comments'
    )
    author_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email (optional if logged in)'
        }),
        help_text='Required for anonymous comments'
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Write your comment here...'
        })
    )
    
    class Meta:
        model = Comment
        fields = ['content', 'author_name', 'author_email']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        use_captcha = kwargs.pop('use_captcha', False)
        super().__init__(*args, **kwargs)

        max_len = SiteSettings.get_value('max_comment_length', 1000)
        self.fields['content'].widget.attrs['maxlength'] = str(max_len)

        if use_captcha:
            self.fields['captcha'] = CaptchaField(
                label='Verification',
                widget=CaptchaTextInput(
                    attrs={
                        'class': 'form-control',
                        'placeholder': 'Enter the characters shown in the image',
                        'autocomplete': 'off',
                    }
                ),
            )
        
        # If user is authenticated, hide name and email fields
        if self.user and self.user.is_authenticated:
            self.fields['author_name'].widget = forms.HiddenInput()
            self.fields['author_email'].widget = forms.HiddenInput()
            self.fields['author_name'].required = False
            self.fields['author_email'].required = False
        else:
            # For anonymous users, make name and email required
            self.fields['author_name'].required = True
            self.fields['author_email'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        
        # For anonymous users, ensure name and email are provided
        if not self.user or not self.user.is_authenticated:
            if not cleaned_data.get('author_name'):
                raise forms.ValidationError('Name is required for anonymous comments.')
            if not cleaned_data.get('author_email'):
                raise forms.ValidationError('Email is required for anonymous comments.')
        
        # Check comment length
        content = cleaned_data.get('content', '')
        if content:
            max_length = SiteSettings.get_value('max_comment_length', 1000)
            if len(content) > max_length:
                raise forms.ValidationError(f'Comment is too long. Maximum {max_length} characters allowed.')
        
        return cleaned_data
    
    def save(self, commit=True):
        comment = super().save(commit=False)
        
        # Set the author if user is authenticated
        if self.user and self.user.is_authenticated:
            comment.author = self.user
            comment.author_name = ''
            comment.author_email = ''
        else:
            comment.author = None
        
        if commit:
            comment.save()
        
        return comment


class ReplyForm(forms.ModelForm):
    """Form for creating replies to comments"""
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Write your reply...'
        })
    )
    
    class Meta:
        model = Comment
        fields = ['content']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.parent_comment = kwargs.pop('parent_comment', None)
        use_captcha = kwargs.pop('use_captcha', False)
        super().__init__(*args, **kwargs)

        max_len = SiteSettings.get_value('max_comment_length', 1000)
        self.fields['content'].widget.attrs['maxlength'] = str(max_len)

        if use_captcha:
            self.fields['captcha'] = CaptchaField(
                label='Verification',
                widget=CaptchaTextInput(
                    attrs={
                        'class': 'form-control',
                        'placeholder': 'Enter the characters shown in the image',
                        'autocomplete': 'off',
                    }
                ),
            )

    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content', '')
        if content:
            max_length = SiteSettings.get_value('max_comment_length', 1000)
            if len(content) > max_length:
                self.add_error(
                    'content',
                    f'Reply is too long. Maximum {max_length} characters allowed.',
                )
        return cleaned_data
    
    def save(self, commit=True):
        reply = super().save(commit=False)
        
        # Set the author and parent comment
        if self.user and self.user.is_authenticated:
            reply.author = self.user
        reply.parent = self.parent_comment
        
        if commit:
            reply.save()
        
        return reply 