from django.conf.urls import url
from . import views

app_name = 'home'
urlpatterns =[
  url(r'^$', views.HomeView.as_view(), name='home'),
  url(r'^(?P<page_no>[0-9]+)/$', views.HomeView.as_view(), name='home'),
  url(r'^posts/$', views.PostsView.as_view(), name='posts'),
  url(r'^posts/(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
#  url(r'^posts/categories/$', views.CategoryView.as_view(), name='category'),
  url(r'^posts/categories/(?P<category_id_0>[0-9]+)/$', views.CategorisedPostsView.as_view(), name='categorised_posts'),
  url(r'^test/(?P<pk>[0-9]+)/$', views.Test.as_view(), name='test'),
  url(r'^posts/(?P<pk>[0-9]+)/addcomment/$', views.CommentView.as_view(), name='addcomment'),
  url(r'^about/$', views.AboutView.as_view(), name='about'),
  url(r'^test2/$', views.Test2.as_view(), name='Test2'),

]
