from django.shortcuts import render

from django.shortcuts import render

def sitemap_view(request):
    return render(request, 'sitemap.html')

