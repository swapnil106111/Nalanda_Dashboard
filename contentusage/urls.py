from django.conf.urls import include, url

from contentusage import views

urlpatterns = [
    url(r'^content-usage/', views.get_contentusage, name='get_contentusage'),
    url(r'^api/contentusage/schools', views.get_schools, name='get_schools'),
]