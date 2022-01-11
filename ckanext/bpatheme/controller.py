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

summary_table_data_path = os.environ.get('SUMMARY_TABLE_DATA_PATH')
link_marker = '<i class="fa fa-circle" aria-hidden="true"></i>'
link_format = '<a target="_blank" rel="noopener noreferrer" href="{0}">{1}</a>'
search_patterns = {
    "yes": r"^[\s]*yes.*",
    "bioplatforms_http": r"^[\s]*http[s]?:\/\/data.bioplatforms.com.*$",
    "other_http": r"^[\s]*http[s]?:\/\/(?!data.bioplatforms.com).*$",
}


def replace_df_header_with_row(df, row):
    df.drop(0, inplace=True)
    df.columns = row


def search_and_replace_once(text):
    for search_keyword, replace_fn in {"yes": replace_yes, "bioplatforms_http": replace_bioplatforms_http, "other_http": replace_url}.items():
        if re.search(search_patterns[search_keyword], text):
            return replace_fn(text)
    return None


def replace_yes(text):
    return re.sub(search_patterns["yes"], link_marker, text)


def replace_bioplatforms_http(text):
    text = text.strip()
    separated = [not_empty for not_empty in re.split(r',|\s', text) if not_empty]
    return replace_multi_bioplatform_urls(separated)


def replace_multi_bioplatform_urls(urls):
    ids_text = create_query_parameter("id", urls.pop(0))
    for next_id in urls:
        ids_text += create_query_parameter(" OR id", next_id)
    return (
        '<a target="_blank" rel="noopener noreferrer" href="https://data.bioplatforms.com/dataset?q={0}">{1}</a>'.format(
            ids_text, link_marker))

def replace_url(text):
    url = text.strip()
    return (
        '<a target="_blank" rel="noopener noreferrer" href="{0}">{1}</a>'.format(
            url, link_marker))


def create_query_parameter(query_format, url):
    # get url final path component only and ensure trailing backslash is handled
    last_path = [not_empty for not_empty in urlsplit(url).path.split('/') if not_empty][-1]
    return urllib.quote("{0}:{1}".format(query_format, last_path))


class SummaryController(base.BaseController):
    def index(self):
        if not os.path.exists(summary_table_data_path):
            log.error("Could not find path to summary table data: {0}".format(summary_table_data_path))
        df = pd.read_json(summary_table_data_path)
        first_row = df.iloc[0]
        replace_df_header_with_row(df, first_row)
        bt_header = json.loads(first_row.to_json(orient="records"))
        # indexed_json = json.loads(df.to_json(orient="index"))
        for row in df.itertuples():
            for index in range(4, len(row)):
                replaced = search_and_replace_once(row[index])
                if replaced:
                    # // ensure any quotes are escaped before passing 'python' JSON into front-end
                    df.at[row.Index, first_row[index-1]] = h.escape_js(replaced)
        bt_json = df.to_json(orient="records")
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
