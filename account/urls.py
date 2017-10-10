from django.conf.urls import include, url
from account import views

urlpatterns = [
	url(r'^login', views.login_view, name='login'),
	url(r'^logout', views.logout_view, name='logout'),
	url(r'^register', views.register_view, name='register'),
	url(r'^api/user/approve', views.admin_approve_pending_users_view, name='admin_approve_pending_users'),
	url(r'^api/user/delete', views.deleteUser, name ='deleteUser'),
	url(r'^api/user/disapprove', views.admin_disapprove_pending_users_view, name='admin_disapprove_pending_users'),
	# url(r'^api/user/unblock', views.admin_unblock_users_view, name='admin_unblock_users'),
	url(r'^api/mastery/get-page-meta', views.get_page_meta_view, name='get_page_meta'),
	url(r'^api/mastery/get-page-data', views.get_page_data_view, name='get_page_data'),
	url(r'^admin', views.admin_get_view, name='admin_get'),
	url(r'^api/mastery/topics',views.get_topics, name='get_topics'),
	url(r'^api/mastery/trend',views.get_trend, name='get_trend'),
    url(r'^report-mastery',views.get_report_mastery,name='get_report_mastery'),
	# url(r'^', views.report_homepage_view, name='report'),
	]
