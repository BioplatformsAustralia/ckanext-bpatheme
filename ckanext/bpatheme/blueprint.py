# encoding: utf-8

from flask import Blueprint

import json
import os
import time
import hmac
from logging import getLogger

from ckan.common import g
import ckan.lib.helpers as h
import ckan.logic as logic
from ckan.plugins.toolkit import (
    render,
    abort,
)

log = getLogger(__name__)

from ckanext.bpatheme import summary


bpatheme = Blueprint("bpatheme", __name__)

# Data summary page
def summary_index():
    bt_json, bt_header = summary.generate_summary()
    return render(
        "summary/index.html",
        extra_vars={"spreadsheet_data": bt_json, "spreadsheet_columns": bt_header},
    )


# BPA Contact information
def contact_index():
    return render("home/contact.html")


# BPA Behaviour after login
def route_after_login():
     # login redirect to homepage bpa-archive-ops/issues#770
     route = u'home.index' if g.user else u'user.login'
     return h.redirect_to(route)


# Token for BPA OTU application
def bioplatforms_webtoken():
    # bpa-otu auth
    if not g.user:
        abort(403, "Please log into CKAN.")

    user_details = {"user": g.user, "auth_user_obj": g.userobj}

    user_id = {"id": g.userobj.id}
    user_data = logic.get_action("user_show")(user_details, user_id)

    organisations = []

    user_organisations = h.organizations_available(permission="read")
    for uo in user_organisations:
        organisations.append(uo["name"])

    data_portion = {
        "email": user_data["email"],
        "timestamp": time.time(),
        "organisations": organisations,
    }

    data_portion = json.dumps(data_portion)

    secret_key = os.environ.get("BPAOTU_AUTH_SECRET_KEY")
    digest_maker = hmac.new(secret_key)
    digest_maker.update(data_portion)
    digest = digest_maker.hexdigest()

    return digest + "||" + data_portion


bpatheme.add_url_rule("/summary", view_func=summary_index)
bpatheme.add_url_rule("/contact", view_func=contact_index)
bpatheme.add_url_rule(
    "/user/private/api/bpa/check_permissions", view_func=bioplatforms_webtoken
)
bpatheme.add_url_rule("/after_login", view_func=route_after_login)
