# encoding: utf-8
import json
import os
import re
import urllib
import time
import hmac
from logging import getLogger
from urlparse import urlsplit

from ckan.common import g
import ckan.lib.helpers as h
import ckan.logic as logic

import ckan.lib.base as base
import pandas as pd

log = getLogger(__name__)

from ckanext.bpatheme import summary


class SummaryController(base.BaseController):
    def index(self):
        bt_json, bt_header = summary.generate_summary()
        return base.render('summary/index.html',
                           extra_vars={'spreadsheet_data': bt_json, 'spreadsheet_columns': bt_header})

class ContactController(base.BaseController):
    def index(self):
        return base.render('home/contact.html')


class TokenController(base.BaseController):
    def bioplatforms_webtoken(self):
        # bpa-otu auth
        if not g.user:
            base.abort(403, 'Please log into CKAN.')

        user_details = {
            'user': g.user,
            'auth_user_obj': g.userobj
        }

        user_id = {'id': g.userobj.id}
        user_data = logic.get_action('user_show')(user_details, user_id)

        organisations = []

        user_organisations = h.organizations_available(permission='read')
        for uo in user_organisations:
            organisations.append(uo['name'])

        data_portion = {
            'email': user_data['email'],
            'timestamp': time.time(),
            'organisations': organisations
        }

        data_portion = json.dumps(data_portion)

        secret_key = os.environ.get('BPAOTU_AUTH_SECRET_KEY')
        digest_maker = hmac.new(secret_key)
        digest_maker.update(data_portion)
        digest = digest_maker.hexdigest()

        return (digest + "||" + data_portion)
