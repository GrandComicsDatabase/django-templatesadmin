from django import forms
from django.core.serializers.json import json

BASE_PATH = 'templatesadmin/codemirror'

MODES = {'css': [BASE_PATH + '/mode/css/css.js', ],
         'htmlmixed': [BASE_PATH + '/mode/htmlmixed/htmlmixed.js',
                       BASE_PATH + '/mode/javascript/javascript.js',
                       BASE_PATH + '/mode/xml/xml.js',
                       BASE_PATH + '/mode/css/css.js'],
         'javascript': [BASE_PATH + '/mode/javascript/javascript.js', ],
         }


class CodeMirrorEditor(forms.Textarea):
    """
        CodeMirror rich-editor in HTML (provides syntax highlight and
        other some basic things.)

        http://codemirror.net/
    """

    @property
    def media(self):
        js = [BASE_PATH + '/lib/codemirror.js',
              BASE_PATH + '/addon/edit/matchbrackets.js',
              BASE_PATH + '/addon/edit/closetags.js',
              BASE_PATH + '/addon/edit/matchtags.js']
        mode = self.config['mode']
        if mode in MODES:
            js.extend(MODES[mode])
        elif mode == 'django':
            js.extend(MODES['htmlmixed'])
            js.extend([BASE_PATH + '/mode/django/django.js',
                       BASE_PATH + '/addon/mode/overlay.js'])
        return forms.Media(js=js,
                           css={'all': [BASE_PATH + '/lib/codemirror.css', ]})

    def __init__(self, attrs=None, **kwargs):
        self.config = {"lineNumbers": True,
                       "matchBrackets": True,
                       "matchTags": True,
                       "autoCloseTags": True}
        if 'extension' in attrs:
            if attrs['extension'].startswith('htm'):
                self.config['mode'] = 'django'
            elif attrs['extension'] == 'js':
                self.config['mode'] = 'javascript'
            elif attrs['extension'] in MODES.keys():
                self.config['mode'] = attrs['extension']
            else:
                self.config['mode'] = 'htmlmixed'
        super(CodeMirrorEditor, self).__init__({'rows': '10', 'cols': '80'})

    def render(self, name, value, attrs=None, renderer=None):
        field = super(CodeMirrorEditor, self).render(name, value, attrs)

        return """%s
<script type="text/javascript">
    var code_editor = CodeMirror.fromTextArea(
        document.getElementById('%s'), %s
    );
</script>
""" % (field, attrs['id'], json.dumps(self.config))
