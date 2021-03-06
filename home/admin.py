from django.contrib import admin

from .models import Category, Post, Comment, About
from django.forms import Textarea
#from django.db import models
from tinymce import models as tinymce_models

admin.site.register(Category)
#admin.site.register(Post)

class PostAdmin(admin.ModelAdmin):
  date_hierarchy = 'created_on'
  fields = ('title', 'category', 'content', 'approve_comment')
  list_display = ('title', 'last_modified', 'author')

#  formfield_overrides = {
#    tinymce_models.HTMLField: 
#      {'widget': Textarea(attrs={'rows':15, 'cols':60})},
#  }

  def save_model(self, request, obj, form, change):
    obj.author = request.user
    super(PostAdmin, self).save_model(request, obj, form, change)

admin.site.register(Post, PostAdmin)

admin.site.register(Comment)
admin.site.register(About)
# Register your models here.
