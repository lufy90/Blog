from django.shortcuts import render
from django.views import generic

from django.http import HttpResponse
from django.template import loader

from .models import Post

# home page view.
class HomeView(generic.TemplateView):
  ''' home page view '''
  template_name = 'home/home.html'
  def get_context_data(self, **kwargs):
    context = super(HomeView, self).get_context_data(**kwargs)
    context['posts'] = Post.objects.order_by('-created_on')
    return context

class PostsView(generic.ListView):
  template_name = 'home/posts.html'
  context_object_name = 'posts'
  def get_queryset(self):
    """ Return all of the posts """
    return Post.objects.order_by('-last_modified')

# display posts content.
class DetailView(generic.DetailView):
  ''' display posts content '''
  model = Post
  template_name = 'home/detail.html'
  def get_context_data(self, **kwargs):
    context = super(DetailView, self).get_context_data(**kwargs)
    try:
      context['next'] = self.get_object().get_next_by_created_on()
    except:
      context['next'] = None
    try:
      context['prev'] = self.get_object().get_previous_by_created_on()
    except:
      context['prev'] = None
    return context



from django.views.generic.edit import FormView
from .form import CommentForm

class CommentView(FormView):
  from_class = CommentForm
  template_name = 'home/detail.html'

  def form_valid(self, form):
    return super(CommentView, self).form_valid(form)




# Test view for purpose of debugging and learn.
class Test(generic.DetailView):
  ''' debugging and learn the machanism of view. '''
  model = Post
  template_name = 'home/test.html'
  def get_context_data(self, **kwargs):
    context = super(Test, self).get_context_data(**kwargs)
    context['content_head'] = self.get_object().get_content_head()
    try:
      context['next'] = self.get_object().get_next_by_created_on()
    except:
      context['next'] = None
    try:
      context['prev'] = self.get_object().get_previous_by_created_on()
    except:
      context['prev'] = None
    return context
#def home(request):
#    template = loader.get_template('home/home.html')
#    return HttpResponse(template.render(request))


# Create your views here.
