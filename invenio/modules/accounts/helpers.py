# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Helper methods for accounts."""

from datetime import datetime, timedelta

from flask import g, render_template, url_for, current_app

from flask_login import login_user, logout_user

from invenio.base.globals import cfg
from invenio.base.i18n import _
from invenio.ext.email import send_email
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User

from sqlalchemy.orm.exc import NoResultFound


def flask_set_uid(uid, remember_me=False):
    """Set user id into the session, and raise the cookie to the client."""
    if uid > 0:
        login_user(uid, remember_me)
    else:
        logout_user()
    return uid


def register_user(email, password, nickname, login_method=None):
    """Register user.

    :param email: the user email
    :param password: the user password
    :param login_method: login method
    """
    activated = 1  # By default activated

    # if local login
    if not login_method or \
            not cfg['CFG_EXTERNAL_AUTHENTICATION'][login_method]:
        if cfg['CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS'] >= 2:
            return 5
        elif cfg['CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT']:
            activated = 2  # Email confirmation required
        elif cfg['CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS'] >= 1:
            activated = 0  # Administrator confirmation required

    # okay, go on and register the user
    user = User(nickname=nickname,
                email=email,
                password=password,
                note=activated,
                last_login=datetime.now())

    if cfg['CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT']:
        verify_email(user)

    try:
        db.session.add(user)
        db.session.commit()
    except Exception:
        current_app.logger.exception("Could not store user.")
        db.session.rollback()
        return 7
    if activated == 1:  # Ok we consider the user as logged in :-)
        flask_set_uid(user.id)
    return 0


def confirm_email(email):
    """Confirm the email.

    It returns None when there are problems, otherwise it return the uid
    involved.
    """
    if cfg['CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS'] == 0:
        activated = 1
    elif cfg['CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS'] == 1:
        activated = 0
    elif cfg['CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS'] >= 2:
        return -1
    try:
        user = User.query.filter_by(email=email).one()
        user.note = activated

        if cfg['CFG_ACCESS_CONTROL_NOTIFY_ADMIN_ABOUT_NEW_ACCOUNTS']:
            send_new_admin_account_warning(email, cfg['CFG_SITE_ADMIN_EMAIL'])

        return user.id
    except NoResultFound:
        return None


def send_new_admin_account_warning(new_account_email, send_to):
    """Send an email to the address given by send_to about the new account."""
    sub = _("New account on '%(website)s'", website=cfg['CFG_SITE_NAME'])
    if cfg['CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS'] == 1:
        sub += " - " + _("PLEASE ACTIVATE")
    body = _("A new account has been created on '%(website)s'",
             website=cfg['CFG_SITE_NAME'])
    if cfg['CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS'] == 1:
        body += _(" and is awaiting activation")
    body += ":\n\n"
    body += _("Username/Email: %(email)s", email=new_account_email) + "\n\n"
    body += _("You can approve or reject this account request at: %(link)s\n",
              link="%s/admin/webaccess/webaccessadmin.py/manageaccounts" %
              cfg['CFG_SITE_URL'])
    return send_email(cfg['CFG_SITE_SUPPORT_EMAIL'], send_to, subject=sub,
                      content=body)


def send_account_activation_email(user):
    """Send an account activation email."""
    from invenio.modules.access.mailcookie import \
        mail_cookie_create_mail_activation

    expires_in = cfg.get('CFG_WEBSESSION_ADDRESS_ACTIVATION_EXPIRE_IN_DAYS')

    address_activation_key = mail_cookie_create_mail_activation(
        user.email,
        cookie_timeout=timedelta(days=expires_in)
    )

    # Render context.
    ctx = {
        "ip_address": None,
        "user": user,
        "email": user.email,
        "activation_link": url_for(
            'webaccount.access',
            mailcookie=address_activation_key,
            _external=True,
            _scheme='https',
        ),
        "days": expires_in,
    }

    # Send email
    send_email(
        cfg.get('CFG_SITE_SUPPORT_EMAIL'),
        user.email,
        _("Account registration at %(sitename)s",
          sitename=cfg["CFG_SITE_NAME_INTL"].get(getattr(g, 'ln',
                                                 cfg['CFG_SITE_LANG']),
                                                 cfg['CFG_SITE_NAME'])),
        render_template("accounts/emails/activation.tpl", **ctx)
    )


def verify_email(user, force=False):
    """Verify email address."""
    if force or user.note == "2":
        if user.note != "2":
            user.note = 2
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise
        send_account_activation_email(user)
        return True
    return False
