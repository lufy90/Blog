from django import forms
from .models import Post, Comment, comment_text_validate
from django.utils.translation import ugettext_lazy as _

class CommentForm(forms.ModelForm):
  name = "comments"
#  text = forms.TextInput(validators=[comment_text_validate])
  class Meta:
    model = Comment
    fields = ['text', 'author']
    labels = {
#      'text': _('Comments'),
    }
    help_texts = {
#      'text': _('Can this work?'),
    }
  
#  def as_p(self):
#   pass 

