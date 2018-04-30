from django import forms
from .widgets import CodeMirrorEditor


class TemplateForm(forms.Form):
    content = forms.CharField(
      widget=forms.Textarea(attrs={'rows': 10, 'cols': 80})
    )

    def __init__(self, *args, **kwargs):
        """
            Backward compatibility for RichTemplateForm
        """
        kwargs.pop('widget_extension')

        super(TemplateForm, self).__init__(*args, **kwargs)


class RichTemplateForm(forms.Form):
    """
        Display the code using CodeMirror editor
    """
    content = forms.CharField(
      widget=forms.Textarea(attrs={'rows': 10, 'cols': 80})
    )

    def __init__(self, *args, **kwargs):
        extension = kwargs.pop('widget_extension')

        super(RichTemplateForm, self).__init__(*args, **kwargs)

        #
        # Overwrite editor field dynamically
        #
        self.fields['content'] = forms.CharField(
            widget=CodeMirrorEditor(attrs={'extension': extension})
        )
