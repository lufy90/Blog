from django.shortcuts import render
from django.views import generic

from django.http import HttpResponse
from django.template import loader

from .models import Post

# home page view.
class HomeView(generic.TemplateView):
  ''' home page view '''
  template_name = 'home/home.html'
  def get_context_data(self, page_no=1, **kwargs):
    context = super(HomeView, self).get_context_data(**kwargs)
    page_no = int(page_no)
    posts_per_page = 10
    a, b = (page_no-1) * posts_per_page, page_no * posts_per_page
    context['posts'] = Post.objects.order_by('-created_on')[a:b]
    page_no_max = Post.objects.count() / posts_per_page + 1
    context['page_no'] = page_no
    pre = page_no - 1
    nex = page_no + 1
    if (pre < 1):
        context['prev'] = None
    else:
        context['prev'] = pre
    if (nex > page_no_max):
        context['next'] = None
    else:
        context['next'] = nex
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
    context['form'] = CommentForm
    return context



from django.views.generic.edit import FormView
from .forms import CommentForm
from django.urls import reverse_lazy, reverse
from .models import Comment
from django.shortcuts import get_object_or_404
class CommentView(FormView):
  ''' Page for add comments '''
  form_class = CommentForm
  template_name = 'home/detail.html'
  def get_post_pk(self):
    post_pk = self.kwargs['pk']
    return post_pk

#  success_url = reverse_lazy('home:detail', kwargs={'id':get_post_id()})
# http://blog.csdn.net/zh_m8/article/details/7975639
# https://www.w3.org/Protocols/rfc2616/rfc2616-sec5.html

  def form_valid(self, form):
    self.success_url = reverse('home:detail', kwargs={'pk':self.get_post_pk()})
    form.instance.comment_ip = self.request.META['REMOTE_ADDR'] 
    a = form.save(commit=False)
#    a.comment_ip = self.get_comment_request().META['REMOTE_ADDR'] # 20170907 21:00
    a.post = Post.objects.get(pk=self.get_post_pk())
    comment_rate_limit = 30
    if self.comment_interval() > comment_rate_limit:
      a.save()    
    return super(CommentView, self).form_valid(form)
  def comment_interval(self):
    ''' Return last comment interval '''
    from django.utils.timezone import utc
    from datetime import datetime
    now = datetime.utcnow().replace(tzinfo=utc)
    request_ip = self.request.META['REMOTE_ADDR']
    try:
      last_comment_created_on = Comment.objects.filter(comment_ip=request_ip).latest('created_on').created_on
      interval = (now-last_comment_created_on).seconds
      return interval
    except Comment.DoesNotExist:
      return 9999999

from .models import About
class AboutView(generic.TemplateView):
  ''' About page view. '''

  template_name = "home/about.html"
  def get_context_data(self, **kwargs):
    context = super(AboutView, self).get_context_data(**kwargs)
    try:
      context['title'] = About.objects.latest('created_on').title
      context['content'] = About.objects.latest('created_on').content
    except About.DoesNotExist:
      pass
    return context


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

from django.views import View
class Test2(View):
  def get(self, request):
    return HttpResponse(request.META['REMOTE_ADDR'])
#def home(request):
#    template = loader.get_template('home/home.html')
#    return HttpResponse(template.render(request))


# Create your views here.
