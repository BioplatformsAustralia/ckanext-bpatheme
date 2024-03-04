# encoding: utf-8
import json
import os
import re
from logging import getLogger

# Python 2 to 3
from six.moves import urllib
from six.moves.urllib.parse import urlsplit

import ckan.lib.helpers as h
import pandas as pd

log = getLogger(__name__)

summary_table_data_path = os.environ.get("SUMMARY_TABLE_DATA_PATH")
link_marker = '<i class="fa fa-circle" aria-hidden="true"></i>'
link_format = '<a target="_blank" rel="noopener noreferrer" href="{0}">{1}</a>'
search_patterns = {
    "yes": r"^[\s]*yes.*",
    "bioplatforms_http": r"^[\s]*http[s]?:\/\/data.bioplatforms.com.*$",
    "other_http": r"^[\s]*http[s]?:\/\/(?!data.bioplatforms.com).*$",
    "mailTo": r"^[\s]*mailTo:.*$",
    "||": r"[||]{2}|\|",
}


def replace_df_header_with_row(df, row):
    df.drop(0, inplace=True)
    df.columns = row


def search_and_replace_once(text):
    for search_keyword, replace_fn in list(
        {
            "yes": replace_yes,
            "bioplatforms_http": replace_bioplatforms_http,
            "other_http": replace_url_with_bullet,
            "mailTo": replace_mail_to,
            "||": replace_url_with_text,
        }.items()
    ):
        if re.search(search_patterns[search_keyword], text):
            return replace_fn(text)
    return None


def replace_yes(text):
    return re.sub(search_patterns["yes"], link_marker, text)


def replace_bioplatforms_http(text):
    text = text.strip()
    separated = [not_empty for not_empty in re.split(r",|\s", text) if not_empty]
    if len(separated) == 1:
        return replace_url_with_bullet(text)
    return replace_multi_bioplatform_urls(separated)


def replace_multi_bioplatform_urls(urls):
    ids_text = create_query_parameter("id", urls.pop(0))
    for next_id in urls:
        ids_text += create_query_parameter(" OR id", next_id)
    return '<a target="_blank" rel="noopener noreferrer" href="https://data.bioplatforms.com/dataset?q={0}">{1}</a>'.format(
        ids_text, link_marker
    )


def replace_url(text, display):
    url = text.strip()
    return '<a target="_blank" rel="noopener noreferrer" href="{0}">{1}</a>'.format(
        url, display
    )

def replace_url_with_bullet(text):
    return replace_url(text, link_marker)


def replace_url_with_text(text):
    text = text.strip()
    url_pairs = [not_empty for not_empty in re.split(r",", text) if not_empty]
    url_string = ""
    for pair in url_pairs:
        split_value =pair.split('||')
        url_string = url_string + replace_url(split_value[1], split_value[0]) + "<br />"
    return url_string


def replace_mail_to(text):
    return '<a href="{0}"> {1}</a>'.format(
        text, link_marker
    )


def create_query_parameter(query_format, url):
    # get url final path component only and ensure trailing backslash is handled
    last_path = [not_empty for not_empty in urlsplit(url).path.split("/") if not_empty][
        -1
    ]
    return urllib.parse.quote("{0}:{1}".format(query_format, last_path))


def generate_summary():
    if not os.path.exists(summary_table_data_path):
        log.error(
            "Could not find path to summary table data: {0}".format(
                summary_table_data_path
            )
        )
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
                df.at[row.Index, first_row[index - 1]] = h.escape_js(replaced)
    bt_json = df.to_json(orient="records")
    return bt_json, bt_header
