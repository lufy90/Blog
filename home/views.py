from django.shortcuts import render
from django.views import generic

from django.http import HttpResponse
from django.template import loader

from .models import Post

class HomeView(generic.TemplateView):
  template_name = 'home/home.html'

class PostsView(generic.ListView):
  template_name = 'home/posts.html'
  context_object_name = 'posts'
  def get_queryset(self):
    """ Return all of the posts """
    return Post.objects.order_by('-last_modified')

class DetailView(generic.DetailView):
  model = Post
  template_name = 'home/detail.html'
#def home(request):
#    template = loader.get_template('home/home.html')
#    return HttpResponse(template.render(request))


# Create your views here.
