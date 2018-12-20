from django.conf.urls import include, url
from usersession import views

urlpatterns = [
	url(r'^api/usersession/get-page-meta', views.get_page_meta_view, name='get_page_meta'),
	url(r'^api/usersession/get-page-data', views.get_page_data_view, name='get_page_data'),
	url(r'^api/usersession/trend', views.get_trend_data_view, name='get_trend_data'),
	url(r'^api/usersession/superset_data', views.get_superset_data, name='get_superset_data')
]