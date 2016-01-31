# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from cgi import escape
from pyramid.security import unauthenticated_userid
from .interfaces import IUserClass


def get_user(request):
    userid = unauthenticated_userid(request)
    user_class = request.registry.queryUtility(IUserClass)
    if userid is not None:
        return user_class.get_by_id(request, userid)
    return None


def render_flash_messages(request):
    msgs = request.session.pop_flash()  # Pops from the empty string queue
    return ''.join([m.html if hasattr(m, 'html')
                    else bootstrap_msg(m) for m in msgs])


QUEUES = set(['error', 'warning', 'info', 'success', ''])


def render_flash_messages_from_queues(request):
    '''This method is for compatibility with other systems only.
    Some developers are using queues named after bootstrap message flavours.
    I think my system (using only the default queue '') is better,
    because FlashMessage already supports a ``kind`` attribute,
    but this function provides a way to display their flash messages, too.

    You can set QUEUES to something else if you like, from user code.
    '''
    msgs = []
    for q in QUEUES:
        for m in request.session.pop_flash(q):
            html = m.html if hasattr(m, 'html') \
                else bootstrap_msg(plain=m, kind=q)
            msgs.append(html)
    return ''.join(msgs)


def bootstrap_msg(plain=None, rich=None, kind='warning'):
    return '<div class="alert alert-{0}{1}"><button type="button" ' \
        'class="close" data-dismiss="alert">×</button>{2}</div>\n'.format(
            escape(kind),
            ' alert-block' if rich else '', rich or escape(plain))


class FlashMessage(object):
    """
    A flash message that renders in Twitter Bootstrap 2.1 style.
    To register a message, simply instantiate it.
    """
    __slots__ = ('kind', 'plain', 'rich')

    def __getstate__(self):
        '''Because we are using __slots__, pickling needs this method.'''
        return {'kind': self.kind, 'plain': self.plain, 'rich': self.rich}

    def __setstate__(self, state):
        self.kind = state.get('kind')
        self.plain = state.get('plain')
        self.rich = state.get('rich')
    KINDS = set(['error', 'warning', 'info', 'success'])

    def __init__(self, request, plain=None, rich=None, kind='warning',
                 allow_duplicate=False):
        assert (plain and not rich) or (rich and not plain)
        assert kind in self.KINDS, "Unknown kind of alert: \"{}\". " \
            "Possible kinds are {}".format(kind, self.KINDS)
        self.kind = kind
        self.rich = rich
        self.plain = plain
        request.session.flash(self, allow_duplicate=allow_duplicate)

    def __repr__(self):
        return 'FlashMessage("{}")'.format(self.plain)

    def __unicode__(self):
        return self.rich or self.plain

    @property
    def html(self):
        return bootstrap_msg(self.plain, self.rich, self.kind)
