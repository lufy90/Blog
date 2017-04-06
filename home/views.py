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
    # Get the next page and previous pave.
    try:
      context['next'] = self.get_object().get_next_by_created_on()
    except:
      context['next'] = None
    try:
      context['prev'] = self.get_object().get_previous_by_created_on()
    except:
      context['prev'] = None
    # comment form
#    kwargs['form'] = CommentForm()
    return context



from django.views.generic.edit import FormView
from .forms import CommentForm
from django.urls import reverse_lazy, reverse
from .models import Comment
from django.shortcuts import get_object_or_404
class CommentView(FormView):
  ''' Page for add comments '''
  form_class = CommentForm
  template_name = 'home/addcomment.html'
  def get_post_pk(self):
    post_pk = self.kwargs['pk']
    return post_pk
#  success_url = reverse_lazy('home:detail', kwargs={'id':get_post_id()})

  def form_valid(self, form):
    self.success_url = reverse('home:detail', kwargs={'pk':self.get_post_pk()})
    
    a = form.save(commit=False)
    a.post = Post.objects.get(pk=self.get_post_pk())
    a.save()
    
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
