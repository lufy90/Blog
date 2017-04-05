from django.conf.urls import url
from . import views

app_name = 'home'
urlpatterns =[
  url(r'^$', views.HomeView.as_view(), name='home'),
  url(r'^posts/$', views.PostsView.as_view(), name='posts'),
  url(r'^posts/(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
  url(r'^test/(?P<pk>[0-9]+)/$', views.Test.as_view(), name='test'),

]
