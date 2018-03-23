from django.conf.urls import include, url
from contentusage import views

urlpatterns = [
    url(r'^content-usage/', views.get_contentusage, name='get_contentusage'),
    url(r'^api/contentusage/schools', views.get_schools, name='get_schools'),
    url(r'^api/contentusage/get-page-meta', views.get_contentusage_page_meta, name='get_contentusage_page_meta'),
    url(r'^api/contentusage/get-page-data', views.get_contentusage_page_data, name='get_contentusage_page_data'),
]