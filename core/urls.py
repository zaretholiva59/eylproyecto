"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from asyncio import create_task
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

from tasks.views.create_task import create_task_view
from tasks.views.gantt_view import gantt_view

def redirect_to_dashboard(request):
    """Redirige a /dashboard/"""
    return redirect('/dashboard/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_dashboard),
    path("", include("projects.urls")),
    path('contabilidad/', include(('projects.urls.contabilidad', 'contabilidad'), namespace='contabilidad')),
    path('', include('tasks.url.gantt_urls')),
    path('', include('tasks.url.task_urls')),
    path('tasks/crear/', create_task_view, name='create_task'),
]
# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)