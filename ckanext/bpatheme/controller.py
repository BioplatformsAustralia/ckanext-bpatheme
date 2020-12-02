# encoding: utf-8
import json
from logging import getLogger
import ckan.lib.base as base
import pandas as pd

log = getLogger(__name__)


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
