import os
import codecs
from datetime import datetime
from stat import ST_MTIME, ST_CTIME
from re import search

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.utils import get_app_template_dirs
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache

from .forms import TemplateForm, RichTemplateForm
from .models import FTemplate
from . import TemplatesAdminException
from django.contrib import messages

# Default settings that may be overriden by global settings (settings.py)
TEMPLATESADMIN_VALID_FILE_EXTENSIONS = getattr(
    settings,
    'TEMPLATESADMIN_VALID_FILE_EXTENSIONS',
    ('html', 'htm', 'txt', 'js', 'css', 'backup',)
)

TEMPLATESADMIN_GROUP = getattr(
    settings,
    'TEMPLATESADMIN_GROUP',
    'TemplateAdmins'
)

TEMPLATESADMIN_EDITHOOKS = getattr(
    settings,
    'TEMPLATESADMIN_EDITHOOKS',
    ('templatesadmin.edithooks.dotbackupfiles.DotBackupFilesHook', )
)

TEMPLATESADMIN_HIDE_READONLY = getattr(
    settings,
    'TEMPLATESADMIN_HIDE_READONLY',
    False
)

TEMPLATESADMIN_USE_RICHEDITOR = getattr(
    settings,
    'TEMPLATESADMIN_USE_RICHEDITOR',
    True
)

if str == type(TEMPLATESADMIN_EDITHOOKS):
    TEMPLATESADMIN_EDITHOOKS = (TEMPLATESADMIN_EDITHOOKS,)

_hooks = []

for path in TEMPLATESADMIN_EDITHOOKS:
    # inspired by django.template.context.get_standard_processors
    i = path.rfind('.')
    module, attr = path[:i], path[i + 1:]
    try:
        mod = __import__(module, {}, {}, [attr])
    except ImportError as e:
        raise ImproperlyConfigured('Error importing edithook module %s: "%s"' % (module, e))
    try:
        func = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" callable request processor' % (module, attr))

    _hooks.append(func)

TEMPLATESADMIN_EDITHOOKS = tuple(_hooks)

_fixpath = lambda path: os.path.abspath(os.path.normpath(path))

# Load all templates (recursively)
TEMPLATESADMIN_TEMPLATE_DIRS = getattr(
    settings,
    'TEMPLATESADMIN_TEMPLATE_DIRS', [
        d for d in list(dir for template_engine in settings.TEMPLATES for dir in template_engine.get('DIRS')) +
        list(get_app_template_dirs('templates')) if os.path.isdir(d)
    ]
)
TEMPLATESADMIN_TEMPLATE_DIRS = [_fixpath(dir) for dir in TEMPLATESADMIN_TEMPLATE_DIRS]


def user_in_templatesadmin_group(user):
    try:
        user.is_superuser or user.groups.get(name=TEMPLATESADMIN_GROUP)
        return True
    except ObjectDoesNotExist:
        return False


@never_cache
@login_required
@user_passes_test(lambda u: user_in_templatesadmin_group(u))
def listing(request,
            template_name='templatesadmin/overview.html',
            available_template_dirs=TEMPLATESADMIN_TEMPLATE_DIRS):

    template_dict = []
    for templatedir in available_template_dirs:
        for root, dirs, files in os.walk(templatedir):
            for f in sorted([f for f in files if f.rsplit('.')[-1]
                             in TEMPLATESADMIN_VALID_FILE_EXTENSIONS]):
                full_path = os.path.join(root, f)
                l = {'templatedir': templatedir,
                     'rootpath': root,
                     'abspath': full_path,
                     'modified': datetime.fromtimestamp(os.stat(full_path)[ST_MTIME]),
                     'created': datetime.fromtimestamp(os.stat(full_path)[ST_CTIME]),
                     'writeable': os.access(full_path, os.W_OK)
                     }

                # Do not fetch non-writeable templates if settings set.
                if (TEMPLATESADMIN_HIDE_READONLY is True and
                    l['writeable'] is True) or \
                   TEMPLATESADMIN_HIDE_READONLY is False:
                    try:
                        template_dict += (l,)
                    except KeyError:
                        template_dict = (l,)

    template_context = {
        'messages': messages.get_messages(request),
        'template_dict': template_dict,
        'opts': FTemplate._meta,
    }

    return render(request, template_name, template_context)


@never_cache
@login_required
@user_passes_test(lambda u: user_in_templatesadmin_group(u))
def modify(request,
           path,
           template_name='templatesadmin/edit.html',
           base_form=TemplateForm,
           available_template_dirs=TEMPLATESADMIN_TEMPLATE_DIRS):

    template_path = _fixpath(path)
    base_form = (TEMPLATESADMIN_USE_RICHEDITOR and RichTemplateForm or TemplateForm)

    # Check if file is within template-dirs
    if not any([template_path.startswith(templatedir) for templatedir in available_template_dirs]):
        messages.error(request, message=_('Sorry, that file is not available for editing.'))
        return HttpResponseRedirect(reverse('admin:templatesadmin_ftemplate_changelist'))

    if request.method == 'POST':
        formclass = base_form
        for hook in TEMPLATESADMIN_EDITHOOKS:
            formclass.base_fields.update(hook.contribute_to_form(template_path))

        form = formclass(data=request.POST,
                         widget_extension=os.path.splitext(path)[1][1:])
        if form.is_valid():
            content = form.cleaned_data['content']

            try:
                for hook in TEMPLATESADMIN_EDITHOOKS:
                    pre_save_notice = hook.pre_save(request, form, template_path)
                    if pre_save_notice:
                        messages.warning(request, message=pre_save_notice)
            except TemplatesAdminException as e:
                messages.error(request, message=e.message)
                return HttpResponseRedirect(request.build_absolute_uri())

            # Save the template
            try:
                f = open(template_path, 'r', encoding='utf8')
                file_content = f.read()
                f.close()

                # browser tend to strip newlines from <textarea/>s before
                # HTTP-POSTing: re-insert them if neccessary

                # content is in dos-style lineending, will be converted in next step
                if (file_content[-1] == '\n' or file_content[:-2] == '\r\n') \
                   and content[:-2] != '\r\n':
                    content = "%s\r\n" % content

                # Template is saved in unix-style, save in unix style.
                if search("\r\n", file_content) is None:
                    content = content.replace("\r\n", "\n")

                f = codecs.open(template_path, 'w', 'utf-8')
                f.write(content)
                f.close()
            except IOError as e:
                messages.error(request,
                               message=_('Template "%(path)s" has not been saved! Reason: %(errormsg)s') %
                               {'path': path, 'errormsg': e})
                return HttpResponseRedirect(request.build_absolute_uri())

            try:
                for hook in TEMPLATESADMIN_EDITHOOKS:
                    post_save_notice = hook.post_save(request, form, template_path)
                    if post_save_notice:
                        messages.info(request, message=post_save_notice)
            except TemplatesAdminException as e:
                messages.error(request, message=e.message)
                return HttpResponseRedirect(request.build_absolute_uri())

            messages.success(request,
                             message=_('Template "%s" was saved successfully.' % path))
            return HttpResponseRedirect(reverse('templatesadmin-overview'))
    else:
        template_file = codecs.open(template_path, 'r', 'utf-8').read()

        formclass = base_form
        for hook in TEMPLATESADMIN_EDITHOOKS:
            formclass.base_fields.update(hook.contribute_to_form(template_path))

        form = formclass(
            initial={'content': template_file},
            widget_extension=os.path.splitext(path)[1][1:]
        )

    template_context = {
        'messages': messages.get_messages(request),
        'form': form,
        'short_path': path,
        'template_path': path,
        'opts': FTemplate._meta,
        'template_writeable': os.access(template_path, os.W_OK),
    }

    return render(request, template_name, template_context)

