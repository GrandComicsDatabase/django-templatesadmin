from django.contrib import admin
from django.conf.urls import re_path

from django.utils.translation import gettext as _
from django.http import HttpResponseRedirect, HttpResponseForbidden

from templatesadmin.models import FTemplate
from templatesadmin.views import listing, modify

from functools import update_wrapper


@admin.register(FTemplate)
class TemplatesAdmin(admin.ModelAdmin):
    """
        Admin for TemplatesAdmin
    """
    model = FTemplate

    def add_view(self, request, form_url='', extra_content=None):
        return HttpResponseForbidden(_("You can't create new template's by admin interface. Try using the console."))

    def delete_view(self, request, object_id, extra_context=None):
        return HttpResponseForbidden(_("You can't delete templates by admin. Try using the console."))

    def history_view(self, request, object_id, extra_context=None):
        return HttpResponseRedirect('/')

    def changelist_view(self, request):
        return listing(request)

    def change_view(self, request, object_id, extra_context=None):
        return modify(request, object_id)

    def get_urls(self):
        """
            Get templatesadmin admin urls
        """

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        # This is copied on admin.py.
        urlpatterns = [
            re_path(r'^$',                           wrap(self.changelist_view),     name='templatesadmin_ftemplate_changelist'),
            re_path(r'^add/',                        wrap(self.add_view),            name='templatesadmin_ftemplate_add'),
            re_path(r'^edit/(?P<object_id>.*)/$',    wrap(self.change_view),         name='templatesadmin_ftemplate_change'),
        ]

        return urlpatterns


