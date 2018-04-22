from django.conf.urls import patterns,url
from django.contrib.admin.sites import AdminSite

from functools import update_wrapper
from templatesadmin import views as ta_views
urlpatterns = [
    url(r'^$', ta_views.listing, name='templatesadmin-overview'),
    url(r'^edit/(?P<path>.*)/$', ta_views.modify, name='templatesadmin-edit'),
]
