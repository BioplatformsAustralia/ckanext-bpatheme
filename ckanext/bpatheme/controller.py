# encoding: utf-8
import json
import os
from logging import getLogger
import ckan.lib.base as base
import pandas as pd

log = getLogger(__name__)


def replace_df_header_with_row(df, row):
    df.drop(0, inplace=True)
    df.columns = row

summary_table_data_path = os.environ.get('SUMMARY_TABLE_DATA_PATH')

class SummaryController(base.BaseController):

    def index(self):
        if not os.path.exists(summary_table_data_path):
            log.error("Could not find path to summary table data: {0}".format(summary_table_data_path))
        df = pd.read_json(summary_table_data_path)
        first_row = df.iloc[0]
        # raise Exception("first row is: {}".format(first_row))
        replace_df_header_with_row(df, first_row)
        # raise Exception("df is now: {}".format(df))
        bt_data = df.to_json()
        raise Exception("data is now: {}".format(bt_data))
        bt_header = json.loads(first_row.to_json(orient="records"))

        return base.render('summary/index.html',
                           extra_vars={'spreadsheet_data': bt_data, 'spreadsheet_columns': bt_header})
