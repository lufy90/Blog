from django.contrib import admin

from .models import Category, Post

admin.site.register(Category)
#admin.site.register(Post)

class PostAdmin(admin.ModelAdmin):
#  pass
  date_hierarchy = 'created_on'
  def save_model(self, request, obj, form, change):
    obj.author = request.user
    super(PostAdmin, self).save_model(request, obj, form, change)
admin.site.register(Post, PostAdmin)
# Register your models here.
