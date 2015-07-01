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

"""Manage acess module."""

from __future__ import print_function

from invenio.ext.script import Manager
from invenio.modules.access.firerole import repair_role_definitions
from invenio.modules.access.api import add_default_settings, \
    reset_default_settings
from invenio.base.globals import cfg


manager = Manager(usage=__doc__)


@manager.command
@manager.option("-d", "--demo", dest="demo", action="store_true")
def reset(demo=False):
    """Reset settings."""
    if demo:
        DEF_DEMO_USER_ROLES = cfg.get('DEF_DEMO_USER_ROLES', tuple())
        DEF_DEMO_ROLES = cfg.get('DEF_DEMO_ROLES', tuple())
        DEF_DEMO_AUTHS = cfg.get('DEF_DEMO_AUTHS', tuple())

        reset_default_settings(
            [cfg['CFG_SITE_ADMIN_EMAIL']],
            DEF_DEMO_USER_ROLES,
            DEF_DEMO_ROLES,
            DEF_DEMO_AUTHS)
    else:
        reset_default_settings([cfg['CFG_SITE_ADMIN_EMAIL']])


@manager.command
@manager.option("-d", "--demo", dest="demo", action="store_true")
def add(demo=False):
    """Add settings."""
    if demo:
        DEF_DEMO_USER_ROLES = cfg.get('DEF_DEMO_USER_ROLES', tuple())
        DEF_DEMO_ROLES = cfg.get('DEF_DEMO_ROLES', tuple())
        DEF_DEMO_AUTHS = cfg.get('DEF_DEMO_AUTHS', tuple())

        add_default_settings(
            [cfg['CFG_SITE_ADMIN_EMAIL']],
            DEF_DEMO_USER_ROLES,
            DEF_DEMO_ROLES, DEF_DEMO_AUTHS)
    else:
        add_default_settings([cfg['CFG_SITE_ADMIN_EMAIL']])


@manager.command
def repair():
    """Repair compiled firewall role definitions."""
    repair_role_definitions()


def main():
    """Execute script."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
