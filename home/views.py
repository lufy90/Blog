from django.shortcuts import render
from django.views import generic

from django.http import HttpResponse
from django.template import loader

class HomeView(generic.TemplateView):
  template_name = 'home/home.html'

#def home(request):
#    template = loader.get_template('home/home.html')
#    return HttpResponse(template.render(request))


# Create your views here.
