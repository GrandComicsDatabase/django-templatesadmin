from django.conf.urls import patterns,url
from django.contrib.admin.sites import AdminSite

from functools import update_wrapper

urlpatterns = patterns('',
    url(r'^$', 'templatesadmin.views.listing', name='templatesadmin-overview'),
    url(r'^edit/(?P<path>.*)/$', 'templatesadmin.views.modify', name='templatesadmin-edit'),
)
