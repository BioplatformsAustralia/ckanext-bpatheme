# encoding: utf-8

from flask import Blueprint, make_response, request as flask_request

import json
import os
import time
import hmac
import hashlib
import requests as http_requests
from logging import getLogger

from ckan.common import g, session, config
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.logic as logic
from ckan.plugins.toolkit import (
    render,
    abort,
)

SESSION_GALAXY_API_KEY = "ckanext:bpa:galaxy_api_key"


def _galaxy_url():
    return (config.get("ckanext.bpatheme.galaxy_url") or
            os.environ.get("GALAXY_AU_URL", "https://usegalaxy.org.au")).rstrip("/")


def _galaxy_fallback_key():
    return (config.get("ckanext.bpatheme.galaxy_api_key") or
            os.environ.get("GALAXY_API_KEY", ""))

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

def all_projects_index():
    return render("home/all_projects.html")



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


# Galaxy Australia — store the user's Galaxy API key in their CKAN session.
def galaxy_set_api_key():
    log.info("galaxy_set_api_key: called, g.user=%s", g.user)
    if not g.user:
        log.warning("galaxy_set_api_key: unauthenticated request")
        return make_response(json.dumps({"error": "Not authenticated"}), 403)
    body = flask_request.get_json(silent=True) or {}
    api_key = (body.get("api_key") or "").strip()
    if api_key:
        session[SESSION_GALAXY_API_KEY] = api_key
        log.info("galaxy_set_api_key: stored key for user=%s (len=%d)", g.user, len(api_key))
    else:
        session.pop(SESSION_GALAXY_API_KEY, None)
        log.info("galaxy_set_api_key: cleared key for user=%s", g.user)
    return make_response(json.dumps({"ok": True}), 200, {"Content-Type": "application/json"})


# Galaxy Australia — proxy GET /api/histories using the stored API key.
def galaxy_histories():
    log.info("galaxy_histories: called, g.user=%s", g.user)
    if not g.user:
        log.warning("galaxy_histories: unauthenticated request — returning 403")
        return make_response(json.dumps({"error": "Not authenticated"}), 403)
    session_key = session.get(SESSION_GALAXY_API_KEY)
    fallback_key = _galaxy_fallback_key()
    api_key = session_key or fallback_key
    log.info("galaxy_histories: session_key=%s fallback=%s using_key_len=%d",
             bool(session_key), bool(fallback_key), len(api_key) if api_key else 0)
    if not api_key:
        log.warning("galaxy_histories: no API key available — returning 401")
        return make_response(json.dumps({"error": "no_api_key"}), 401, {"Content-Type": "application/json"})
    galaxy_url = _galaxy_url()
    log.info("galaxy_histories: proxying to %s/api/histories", galaxy_url)
    try:
        resp = http_requests.get(
            f"{galaxy_url}/api/histories",
            headers={"x-api-key": api_key},
            params={"limit": 100, "order": "update_time-dsc", "view": "summary"},
            timeout=15,
        )
        log.info("galaxy_histories: Galaxy responded %d, body_len=%d", resp.status_code, len(resp.text))
    except http_requests.RequestException as e:
        log.error("galaxy_histories: request to Galaxy failed: %s", e)
        return make_response(json.dumps({"error": "Could not reach Galaxy Australia."}), 502)
    return make_response(resp.text, resp.status_code, {"Content-Type": "application/json"})


# Galaxy Australia — get presigned S3 URL then proxy a URL-fetch upload to Galaxy.
def galaxy_send():
    log.info("galaxy_send: called, g.user=%s", g.user)
    if not g.user:
        log.warning("galaxy_send: unauthenticated request — returning 403")
        return make_response(json.dumps({"error": "Not authenticated"}), 403)
    session_key = session.get(SESSION_GALAXY_API_KEY)
    fallback_key = _galaxy_fallback_key()
    api_key = session_key or fallback_key
    log.info("galaxy_send: session_key=%s fallback=%s", bool(session_key), bool(fallback_key))
    if not api_key:
        log.warning("galaxy_send: no API key available — returning 401")
        return make_response(json.dumps({"error": "no_api_key"}), 401, {"Content-Type": "application/json"})

    body = flask_request.get_json(silent=True) or {}
    history_id = body.get("history_id")
    package_id = body.get("package_id")
    resource_id = body.get("resource_id")
    log.info("galaxy_send: history_id=%s package_id=%s resource_id=%s", history_id, package_id, resource_id)
    if not history_id or not package_id or not resource_id:
        return make_response(json.dumps({"error": "Missing history_id, package_id or resource_id."}), 400)

    try:
        ctx = {"user": g.user, "auth_user_obj": g.userobj}
        download_info = logic.get_action("download_window")(ctx, {"package_id": package_id, "resource_id": resource_id})
        log.info("galaxy_send: download_window returned keys=%s", list(download_info.keys()))
    except Exception as e:
        log.error("galaxy_send: download_window error for %s/%s: %s", package_id, resource_id, e)
        return make_response(json.dumps({"error": f"Could not generate download URL: {e}"}), 500)

    download_url = download_info.get("url")
    log.info("galaxy_send: download_url present=%s", bool(download_url))
    if not download_url:
        return make_response(json.dumps({"error": "No download URL available for this resource."}), 404)

    galaxy_url = _galaxy_url()
    log.info("galaxy_send: posting to %s/api/tools", galaxy_url)
    try:
        resp = http_requests.post(
            f"{galaxy_url}/api/tools",
            headers={"x-api-key": api_key},
            data={
                "history_id": history_id,
                "tool_id": "upload1",
                "inputs": json.dumps({
                    "file_type": "auto",
                    "dbkey": "?",
                    "files_0|type": "upload_dataset",
                    "files_0|url_paste": download_url,
                    "files_0|NAME": download_info.get("filename") or resource_id,
                }),
            },
            timeout=30,
        )
        log.info("galaxy_send: Galaxy responded %d", resp.status_code)
    except http_requests.RequestException as e:
        log.error("galaxy_send: request to Galaxy failed: %s", e)
        return make_response(json.dumps({"error": "Could not reach Galaxy Australia."}), 502)
    return make_response(resp.text, resp.status_code, {"Content-Type": "application/json"})


bpatheme.add_url_rule("/summary", view_func=summary_index)
bpatheme.add_url_rule("/contact", view_func=contact_index)
bpatheme.add_url_rule("/all_projects", view_func=all_projects_index)
bpatheme.add_url_rule(
    "/user/private/api/bpa/check_permissions", view_func=bioplatforms_webtoken
)
bpatheme.add_url_rule("/after_login", view_func=route_after_login)
bpatheme.add_url_rule("/external_styles.css", view_func=external_styles_index)
# Cart
bpatheme.add_url_rule("/cart/<target_user>", endpoint="cart", view_func=cart_index)
# Galaxy Australia
bpatheme.add_url_rule("/galaxy/set-api-key", endpoint="galaxy_set_api_key", view_func=galaxy_set_api_key, methods=["POST"])
bpatheme.add_url_rule("/galaxy/histories", endpoint="galaxy_histories", view_func=galaxy_histories, methods=["GET"])
bpatheme.add_url_rule("/galaxy/send", endpoint="galaxy_send", view_func=galaxy_send, methods=["POST"])