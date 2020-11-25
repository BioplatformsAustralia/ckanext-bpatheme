# encoding: utf-8

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
from ckan.common import _, c


CACHE_PARAMETERS = ['__cache', '__no_cache__']


class SummaryController(base.BaseController):

    def index(self):
        return base.render('summary/index.html')