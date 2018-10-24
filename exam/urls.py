from django.conf.urls import include, url
from exam import views
#from .views import homePageView

urlpatterns = [
    url(r'^exam-metrics/', views.get_exam_metrics, name = 'get_exam_metrics'),
    url(r'^exams', views.get_exams, name ='get_exams'),
    url(r'^api/exam/get-page-data', views.get_exam_page_data, name = 'get_exam_page_data'),
    
]