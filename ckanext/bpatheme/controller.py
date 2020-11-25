# encoding: utf-8

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
from ckan.common import _, c
import requests
from logging import getLogger
log = getLogger(__name__)


CACHE_PARAMETERS = ['__cache', '__no_cache__']


class SummaryController(base.BaseController):

    def index(self):
        r = requests.get("https://sheets.googleapis.com/v4/spreadsheets/spreadsheetId/values/Sheet1")
        log.info("got request...")
        return base.render('summary/index.html')