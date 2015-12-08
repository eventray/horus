# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from zope.interface import implementer
from .interfaces import IUIStrings
from .models import _


@implementer(IUIStrings)
class UIStringsBase(object):  # TODO Continue building
    '''A class containing all GUI strings in the application, such that
    user apps can simply subclass and change whatever text they want.
    '''
    activation_check_email = \
        _("Thank you for registering! Please check your e-mail now. You can "
          "continue by clicking the activation link we have sent you.")
    activation_email_verified = _("Your e-mail address has been verified. "
                                  "Thank you!")

    admin_create_user_done = _('The user {} has been created.')
    admin_edit_user_done = _('The user {} has been updated successfully.')
    admin_deactivate_user_done = _('The user {} has been '
        'deactivated successfully.')
    admin_activate_user_done = _('The user {} has been '
        'activated successfully.')
    admin_email_exists = _("Sorry, an account with the email {} "
                            "already exists. Please enter another one.")
    admin_username_exists = _("Sorry, an account with the username {} "
                            "already exists. Please enter another one.")
    admin_need_password = _("You must specify a valid password!")
    admin_user_id_missing = _('You must specify a user ID for that action!')

    authenticated = _('You are now logged in.')
    login_button = _('Log in')
    logout = _('You have logged out.')

    edit_profile_done = _('Your profile has been updated.')

    registration_email_exists = _("Sorry, an account with the email {} "
                                  "already exists. Try logging in instead.")
    registration_username_exists = _("Sorry, an account with this "
        "username already exists. Please enter another one.")
    registration_done = _('You have been registered. You may log in now!')

    reset_password_done = _('Your password has been reset!')
    reset_password_email_must_exist = _('We have no user with the email "{}". '
            "Try correcting this address or trying another.")
    reset_password_email_body = _('''\
Hello, {username}!

Someone requested resetting your password. If it was you, click here:
{link}

If you don't want to change your password, please ignore this email message.

Regards,
{domain}\n''')
    reset_password_email_subject = _("Reset your password")
    # You don't want to say "E-mail not registered" or anything like that
    # because it gives spammers context:
    reset_password_email_sent = _("Please check your e-mail to finish "
                                  "resetting your password.")

__doc__ = UIStringsBase.__doc__
