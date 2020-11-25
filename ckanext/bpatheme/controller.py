# encoding: utf-8
import json
from os import path

import ckan.lib.base as base
import ckan.lib.helpers as h
# import requests
import pandas as pd
import numpy as np
from logging import getLogger

log = getLogger(__name__)

CACHE_PARAMETERS = ['__cache', '__no_cache__']


def replace_df_header_with_row(df, row):
    df.drop(0, inplace=True)
    df.columns = row


class SummaryController(base.BaseController):

    def index(self):
        spreadsheet_data_path = '/tmp/googlesheet.json'
        df = pd.read_json(spreadsheet_data_path)
        first_row = df.iloc[0]
        replace_df_header_with_row(df, first_row)
        bt_data = df.to_json(orient="records")
        bt_header = json.loads(first_row.to_json(orient="records"))

        return base.render('summary/index.html',
                           extra_vars={'spreadsheet_data': bt_data, 'spreadsheet_columns': bt_header})
