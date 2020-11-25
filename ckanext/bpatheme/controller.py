# encoding: utf-8

from pylons import cache
import sqlalchemy.exc

import ckan.logic as logic
import ckan.lib.search as search
import ckan.lib.base as base
import ckan.model as model
import ckan.lib.helpers as h

from ckan.common import _, config, c

CACHE_PARAMETERS = ['__cache', '__no_cache__']


class SummaryController(base.BaseController):
    controller = "ckanext.bpatheme.controller:SummaryController"
    def __before__(self, action, **env):
        try:
            base.BaseController.__before__(self, action, **env)
            context = {'model': model, 'user': c.user,
                       'auth_user_obj': c.userobj}
            logic.check_access('site_read', context)
        except logic.NotAuthorized:
            base.abort(403, _('Not authorized to see this page'))

    def index(self):
        return self.about()

    def about(self):
        return base.render('home/about.html')