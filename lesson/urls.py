from django.conf.urls import include, url
from lesson import views

urlpatterns = [
    url(r'^lesson-mastery/', views.get_lesson_mastery, name = 'get_lesson_mastery'),
    url(r'^api/lesson/lessons', views.get_lessons, name ='get_lessons'),
    url(r'^api/lesson/get-page-data', views.get_lesson_page_data, name = 'get_lesson_page_data')
]