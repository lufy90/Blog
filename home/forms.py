from django import forms
from .models import Post, Comment
from django.utils.translation import ugettext_lazy as _

class CommentForm(forms.ModelForm):
  name = "comments"
  class Meta:
    model = Comment
    fields = ['text', 'author']
    labels = {
#      'text': _('Comments'),
    }
    help_texts = {
#      'text': _('Can this works?'),
    }
  
#  def as_p(self):
#   pass 

