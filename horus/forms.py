# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
import deform


class SubmitForm(deform.Form):
    def __init__(self, *args, **kwargs):
        if not kwargs.get('buttons'):
            kwargs['buttons'] = ('submit',)
        super(SubmitForm, self).__init__(*args, **kwargs)


class BaseForm(deform.Form):
    def __init__(self, *args, **kwargs):
        if not kwargs.get('buttons'):
            kwargs['buttons'] = ('submit',)
        super(BaseForm, self).__init__(*args, **kwargs)


class BootstrapForm(BaseForm):
    """This form renders out twitter bootstrap templates."""
    def __init__(self, *args, **kwargs):
        super(BootstrapForm, self).__init__(*args, **kwargs)

        for child in self.children:
            if isinstance(child.widget, deform.widget.TextInputWidget) or \
                isinstance(child.widget, deform.widget.TextAreaWidget):

                if not child.widget.css_class:
                    child.widget.css_class = ''

                if not 'xlarge' in child.widget.css_class:
                    child.widget.css_class += ' xlarge'


class HorusForm(BootstrapForm):
    """This is the standard form we should use throughout our code, that way
    if we decide to swap our rendering later, we only have to do it in 1 place.
    """
    pass
