from django.urls import path, re_path
from django.contrib.admin.sites import AdminSite

from functools import update_wrapper
from templatesadmin import views as ta_views
urlpatterns = [
    path('', ta_views.listing, name='templatesadmin-overview'),
    re_path(r'^edit/(?P<path>.*)/$', ta_views.modify, name='templatesadmin-edit'),
]
