from django.conf.urls import include, url
from sync_report import views

urlpatterns = [
	url(r'^sync_report/', views.get_sync_report, name= 'get_sync_report'),
	url(r'^sync_report_school', views.get_sync_report_school, name= 'get_sync_report_school'),
	url(r'^sync_data', views.get_sync_data, name= 'get_sync_data'),
	url(r'^send_mail',views.send_mail_alert, name='send_mail_alert'),
	]