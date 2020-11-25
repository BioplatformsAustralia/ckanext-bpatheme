# encoding: utf-8

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
from ckan.common import _, c


CACHE_PARAMETERS = ['__cache', '__no_cache__']


class SummaryController(base.BaseController):
    def __before__(self, action, **env):
        try:
            base.BaseController.__before__(self, action, **env)
            context = {'model': model, 'user': c.user,
                       'auth_user_obj': c.userobj}
            logic.check_access('site_read', context)
        except logic.NotAuthorized:
            base.abort(403, _('Not authorized to see this page'))

    def index(self):
        return base.render('summary/about.html')