# encoding: utf-8

from flask import Blueprint, make_response

import json
import os
import time
import hmac
import hashlib
from logging import getLogger

from ckan.common import g
import ckan.lib.base as base
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

    secret_key = os.environ.get("BPAOTU_AUTH_SECRET_KEY").encode('utf-8')
    digest_maker = hmac.new(secret_key, digestmod=hashlib.md5)
    digest_maker.update(data_portion.encode('utf-8'))
    digest = digest_maker.hexdigest()

    return '{}||{}'.format(digest, data_portion)

# BPA Styles for external websites 
def external_styles_index():
    '''display external.css'''
    resp = make_response(base.render('external/external.css'))
    resp.headers['Content-Type'] = "text/css; charset=utf-8"
    return resp
# Cart
#  Main page:
def cart_index(target_user):
    if g.userobj is None:
        return h.redirect_to('user.login')

    site_user = logic.get_action("get_site_user")({'ignore_auth': True}, {})["name"]
    ctx = {"ignore_auth": True, "user": site_user }
    # Only admins can view another user's cart
    username = g.userobj.name
    if g.userobj.name != target_user:
        if g.userobj.sysadmin is True:
            username = target_user
        else:
            return h.redirect_to(f"/cart/{username}")
            
    user_dict = logic.get_action("user_show")(ctx, {"include_num_followers":True, "include_plugin_extras": True, "id": username})
    return render("shopping_cart/cart.html",extra_vars={ "user_dict": user_dict })


bpatheme.add_url_rule("/summary", view_func=summary_index)
bpatheme.add_url_rule("/contact", view_func=contact_index)
bpatheme.add_url_rule(
    "/user/private/api/bpa/check_permissions", view_func=bioplatforms_webtoken
)
bpatheme.add_url_rule("/after_login", view_func=route_after_login)
bpatheme.add_url_rule("/external_styles.css", view_func=external_styles_index)
# Cart
bpatheme.add_url_rule("/cart/<target_user>", endpoint="cart", view_func=cart_index)