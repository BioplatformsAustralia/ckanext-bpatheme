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

# Stored by ckanext-oidc-pkce-bpa after Auth0 login
SESSION_GALAXY_ACCESS_TOKEN = "ckanext:bpa:galaxy_access_token"
SESSION_GALAXY_REFRESH_TOKEN = "ckanext:bpa:galaxy_refresh_token"

# Refresh the access token if it expires within this many seconds (5 minutes)
_TOKEN_REFRESH_WINDOW_SECONDS = 5 * 60


def _galaxy_url():
    return (config.get("ckanext.bpatheme.galaxy_url") or
            os.environ.get("GALAXY_AU_URL", "https://usegalaxy.org.au")).rstrip("/")


def _token_exp(token):
    """Decode the JWT payload (no signature check) and return the exp claim, or None."""
    try:
        import base64 as _b64, json as _json
        payload = token.split(".")[1]
        payload += "=" * (4 - len(payload) % 4)
        return _json.loads(_b64.urlsafe_b64decode(payload)).get("exp")
    except Exception:
        return None


def _refresh_access_token_if_needed():
    """If the stored access token is near expiry, use the refresh token to renew it.

    Updates the session in-place. Returns the (possibly refreshed) access token,
    or None if no token is available.
    """
    import time
    token = session.get(SESSION_GALAXY_ACCESS_TOKEN)
    if not token:
        return None

    exp = _token_exp(token)
    if exp and (exp - time.time()) > _TOKEN_REFRESH_WINDOW_SECONDS:
        return token  # still fresh enough

    refresh_token = session.get(SESSION_GALAXY_REFRESH_TOKEN)
    if not refresh_token:
        log.debug("Access token near expiry but no refresh token stored — using as-is")
        return token

    base_url = config.get("ckanext.oidc_pkce.base_url", "").rstrip("/")
    token_path = config.get("ckanext.oidc_pkce.token_path", "/oauth/token")
    client_id = config.get("ckanext.oidc_pkce.client_id", "")
    client_secret = config.get("ckanext.oidc_pkce.client_secret", "")

    try:
        resp = http_requests.post(
            f"{base_url}{token_path}",
            data={
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            new_token = data.get("access_token")
            if new_token:
                session[SESSION_GALAXY_ACCESS_TOKEN] = new_token
                if data.get("refresh_token"):
                    session[SESSION_GALAXY_REFRESH_TOKEN] = data["refresh_token"]
                log.info("galaxy: access token refreshed successfully")
                return new_token
        log.warning("galaxy: token refresh failed (%d): %s", resp.status_code, resp.text[:200])
    except http_requests.RequestException as e:
        log.warning("galaxy: token refresh request failed: %s", e)

    return token  # return old token; Galaxy will 401 if truly expired


def _galaxy_auth_headers():
    """Return Bearer auth headers, refreshing the access token first if near expiry.

    Returns ({}, "none") if no token is available.
    """
    token = _refresh_access_token_if_needed()
    if token:
        return {"Authorization": f"Bearer {token}"}, "bearer"
    return {}, "none"

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


# Galaxy Australia — proxy GET /api/histories using the Auth0 Bearer token.
def galaxy_histories():
    log.info("galaxy_histories: called, g.user=%s", g.user)
    if not g.user:
        log.warning("galaxy_histories: unauthenticated request — returning 403")
        return make_response(json.dumps({"error": "Not authenticated"}), 403)
    auth_headers, auth_method = _galaxy_auth_headers()
    log.info("galaxy_histories: auth_method=%s has_headers=%s", auth_method, bool(auth_headers))
    if not auth_headers:
        log.warning("galaxy_histories: no OIDC token in session")
        return make_response(json.dumps({"error": "No authentication token available. Please log out and log in again."}), 400, {"Content-Type": "application/json"})
    galaxy_url = _galaxy_url()
    log.info("galaxy_histories: proxying to %s/api/histories", galaxy_url)
    try:
        resp = http_requests.get(
            f"{galaxy_url}/api/histories",
            headers=auth_headers,
            params={"limit": 100, "order": "update_time-dsc", "view": "summary"},
            timeout=15,
        )
        log.info("galaxy_histories: Galaxy responded %d", resp.status_code)
    except http_requests.RequestException as e:
        log.error("galaxy_histories: request to Galaxy failed: %s", e)
        return make_response(json.dumps({"error": "Could not reach Galaxy Australia."}), 502, {"Content-Type": "application/json"})
    # Translate Galaxy 4xx to 502 — returning 401/403 triggers repoze.who login redirect
    if resp.status_code in (401, 403):
        msg = "Your login session was not accepted by Galaxy Australia. Please log into Galaxy Australia once using the BioCommons login button to link your account."
        try:
            body = resp.json()
            if body.get("err_msg"):
                log.warning("galaxy_histories: Galaxy auth error: %s", body["err_msg"])
        except Exception:
            pass
        return make_response(json.dumps({"error": msg}), 502, {"Content-Type": "application/json"})
    return make_response(resp.text, resp.status_code, {"Content-Type": "application/json"})


# Galaxy Australia — get presigned S3 URL then proxy a URL-fetch upload to Galaxy.
def galaxy_send():
    log.info("galaxy_send: called, g.user=%s", g.user)
    if not g.user:
        log.warning("galaxy_send: unauthenticated request — returning 403")
        return make_response(json.dumps({"error": "Not authenticated"}), 403)
    auth_headers, auth_method = _galaxy_auth_headers()
    log.info("galaxy_send: auth_method=%s has_headers=%s", auth_method, bool(auth_headers))
    if not auth_headers:
        log.warning("galaxy_send: no OIDC token in session")
        return make_response(json.dumps({"error": "No authentication token available. Please log out and log in again."}), 400, {"Content-Type": "application/json"})

    body = flask_request.get_json(silent=True) or {}
    history_id = body.get("history_id")
    package_id = body.get("package_id")
    resource_id = body.get("resource_id")
    resource_name = body.get("resource_name") or resource_id
    log.info("galaxy_send: history_id=%s resource_id=%s", history_id, resource_id)
    if not history_id or not package_id or not resource_id:
        return make_response(json.dumps({"error": "Missing history_id, package_id or resource_id."}), 400)

    from urllib.parse import urlparse as _urlparse
    hostname = _urlparse(config.get("ckan.site_url", "")).hostname or ""
    drs_uri = f"drs://{hostname}/{resource_id}"
    log.info("galaxy_send: DRS URI=%s", drs_uri)

    galaxy_url = _galaxy_url()
    log.info("galaxy_send: posting to %s/api/tools/fetch", galaxy_url)
    try:
        resp = http_requests.post(
            f"{galaxy_url}/api/tools/fetch",
            headers=auth_headers,
            json={
                "history_id": history_id,
                "targets": [{
                    "destination": {"type": "hdas"},
                    "elements": [{
                        "src": "url",
                        "url": drs_uri,
                        "name": resource_name,
                    }]
                }]
            },
            timeout=30,
        )
        log.info("galaxy_send: Galaxy responded %d", resp.status_code)
    except http_requests.RequestException as e:
        log.error("galaxy_send: request to Galaxy failed: %s", e)
        return make_response(json.dumps({"error": "Could not reach Galaxy Australia."}), 502, {"Content-Type": "application/json"})
    if resp.status_code in (401, 403):
        return make_response(json.dumps({"error": "Your login session was not accepted by Galaxy Australia. Please log into Galaxy Australia once using the BioCommons login button to link your account."}), 502, {"Content-Type": "application/json"})
    return make_response(resp.text, resp.status_code, {"Content-Type": "application/json"})


# Galaxy Australia — send entire package as a DRS bundle to Galaxy.
def galaxy_send_bundle():
    log.info("galaxy_send_bundle: called, g.user=%s", g.user)
    if not g.user:
        return make_response(json.dumps({"error": "Not authenticated"}), 403)
    auth_headers, auth_method = _galaxy_auth_headers()
    if not auth_headers:
        return make_response(json.dumps({"error": "No authentication token available. Please log out and log in again."}), 400, {"Content-Type": "application/json"})

    body = flask_request.get_json(silent=True) or {}
    history_id = body.get("history_id")
    package_id = body.get("package_id")
    log.info("galaxy_send_bundle: history_id=%s package_id=%s", history_id, package_id)
    if not history_id or not package_id:
        return make_response(json.dumps({"error": "Missing history_id or package_id."}), 400)

    from urllib.parse import urlparse as _urlparse
    hostname = _urlparse(config.get("ckan.site_url", "")).hostname or ""

    try:
        pkg = logic.get_action("package_show")({"ignore_auth": False, "user": g.user}, {"id": package_id})
    except logic.NotFound:
        return make_response(json.dumps({"error": f"Package '{package_id}' not found."}), 404, {"Content-Type": "application/json"})
    except logic.NotAuthorized:
        return make_response(json.dumps({"error": "You do not have permission to access this package."}), 403, {"Content-Type": "application/json"})

    resources = pkg.get("resources") or []
    if not resources:
        return make_response(json.dumps({"error": "Package has no resources to transfer."}), 400, {"Content-Type": "application/json"})

    elements = [
        {
            "src": "url",
            "url": f"drs://{hostname}/{r['id']}",
            "name": r.get("name") or r["id"],
        }
        for r in resources
        if r.get("id")
    ]
    collection_name = pkg.get("title") or package_id
    log.info("galaxy_send_bundle: sending %d elements for package %s", len(elements), package_id)

    galaxy_url = _galaxy_url()
    try:
        resp = http_requests.post(
            f"{galaxy_url}/api/tools/fetch",
            headers=auth_headers,
            json={
                "history_id": history_id,
                "targets": [{
                    "destination": {"type": "hdca"},
                    "collection_type": "list",
                    "name": collection_name,
                    "elements": elements,
                }]
            },
            timeout=30,
        )
        log.info("galaxy_send_bundle: Galaxy responded %d", resp.status_code)
    except http_requests.RequestException as e:
        log.error("galaxy_send_bundle: request to Galaxy failed: %s", e)
        return make_response(json.dumps({"error": "Could not reach Galaxy Australia."}), 502, {"Content-Type": "application/json"})
    if resp.status_code in (401, 403):
        return make_response(json.dumps({"error": "Your login session was not accepted by Galaxy Australia. Please log into Galaxy Australia once using the BioCommons login button to link your account."}), 502, {"Content-Type": "application/json"})
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
bpatheme.add_url_rule("/galaxy/histories", endpoint="galaxy_histories", view_func=galaxy_histories, methods=["GET"])
bpatheme.add_url_rule("/galaxy/send", endpoint="galaxy_send", view_func=galaxy_send, methods=["POST"])
bpatheme.add_url_rule("/galaxy/send-bundle", endpoint="galaxy_send_bundle", view_func=galaxy_send_bundle, methods=["POST"])