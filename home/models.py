from __future__ import unicode_literals

from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from tinymce import models as tinymce_models
class Category(models.Model):
  name = models.CharField(max_length=255, null=True)
  description = models.TextField(blank=True, null=True)
  create_on = models.DateTimeField(auto_now_add=True)
  last_modified = models.DateTimeField(auto_now=True)

  class Meta:
    verbose_name_plural = "Categories"

  def __unicode__(self):
    return self.name


from django.template.defaultfilters import slugify
import re

class Post(models.Model):
  title = models.CharField(max_length=200, null=True)
  slug = models.SlugField(max_length=255, blank=True, null=True)
  category = models.ForeignKey(Category, related_name='post_category', 
    blank=True, null=True)
#  content = models.TextField(blank=True, null=True)
  content = tinymce_models.HTMLField(blank=True, null=True)
  created_on = models.DateTimeField(auto_now_add=True)
  last_modified = models.DateTimeField(auto_now=True)
  author = models.ForeignKey(User, blank=True, null=True)
#  content_head = models.TextField(blank=True, null=True)
  class Meta:
    verbose_name_plural = "Posts"

  def __unicode__(self):
    return self.title

  def save(self, *args, **kwargs):
    self.slug = slugify(self.title)
    super(Post, self).save(*args, **kwargs)

  def get_content_head(self):
    ''' remove the html tags and get text head '''
    f = re.compile(r'</?\w+[^>]*>', re.S)
    html = self.content
    head = f.sub('', html)[:200]
    return head

class Comment(models.Model):
  ''' define post comments '''
  post = models.ForeignKey(Post, related_name='comments')
  author = models.CharField(max_length=200)
  text = models.TextField()
  created_on = models.DateTimeField(auto_now=True)
  approve_comment = models.BooleanField(default=False)

  def approv(self):
    self.approve_comment = True
    self.save()

  def __unicode__(self):
    return self.text[:50]

# about slug: 
# https://github.com/neithere/django-autoslug

# Create your models here.
