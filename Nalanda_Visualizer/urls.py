"""Nalanda_Visualizer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin

import account.views
import usersession.views
import contentusage.views
import lesson.views
import exam.views

urlpatterns = [
    url(r'^account/', include('account.urls')),
    url(r'^usersession/', include('usersession.urls')),
    url(r'^contentusage/', include('contentusage.urls')),
    url(r'^lesson/', include('lesson.urls')),
    url(r'^exam/', include('exam.urls')),
    url(r'^sync_report/',include('sync_report.urls')),
    url(r'^admin/', admin.site.urls)
]