from ckan import model
from ckan.common import config, c, _
import ckan.logic
import ckan.plugins.toolkit as toolkit
import datetime
from ckan.plugins.toolkit import chained_action
from ckan.logic.action.create import user_create
from ckan.lib.helpers import flash_success, flash_notice

from .mail import mail_welcome_email

import os
import logging

log = logging.getLogger(__name__)

_check_access = ckan.logic.check_access
_get_or_bust = ckan.logic.get_or_bust


class EmailUser:
    pass


def custom_user_create(context, data_dict=None):
    from ckan.logic.auth import create

    newuser = user_create(context, data_dict)

    # log the user in programatically

    # set the auth_user_obj in the context so API calls behave
    # like the new user is logged in
    context["auth_user_obj"] = model.User.get(newuser["name"])
    context["user"] = newuser["name"]
    # stash values
    stash_c_user_obj = getattr(c, "user_obj", None)
    stash_c_user = getattr(c, "user", None)
    # set them during member request create
    c.user_obj = model.User.get(newuser["name"])
    c.user = newuser["name"]

    # find organization check boxes
    membership_requested = False
    orgs = toolkit.get_action("get_available_organizations")({}, {})

    for org in orgs:
        id = "org-{}".format(org["name"])
        log.debug("looking for {}".format(id))
        if id in data_dict:
            log.debug("found {}".format(id))
            membership_requested = True
            create_dict = {}
            create_dict["role"] = "member"
            create_dict["group"] = org.get("name")
            create_dict["message"] = data_dict.get("request_reason", "")

            try:
                request = toolkit.get_action("member_request_create")(
                    context, create_dict
                )
            except Exception as e:
                log.exception("custom_user_create")

    # un stash values
    c.user_obj = stash_c_user_obj
    c.user = stash_c_user

    # if no requests, flash notice
    if not membership_requested:
        flash_notice(
            _(
                'No initiative memberships were requested.  Please request access using the "Memberships" button in the top right.'
            )
        )

    # send welcome to the new user
    url = config.get("ckan.site_url", "")
    site_name = config.get("ckan.site_description", "")
    site_email = os.environ.get(
        "BIOPLATFORMS_HELPDESK_ADDRESS", config.get("error_email_from", "")
    )

    welcome = EmailUser()
    welcome.email = newuser["email"]
    welcome.username = newuser["name"]
    welcome.display_name = newuser["display_name"]

    mail_welcome_email(welcome, site_name, site_email, url)

    flash_success(_("Membership created.  You have been logged in."))

    return newuser


def _timestamp():
    return datetime.datetime.now().strftime("%Y%m%d%H%M")


@chained_action
def user_delete(original_action, context, data_dict=None):
    # CKAN only does a soft delete when users are deleted.
    #
    # For the AAI integration and to avoid future clashes in usernames/email addresses need to alter these on deletion.
    #
    # :param id: the id or usernamename of the user to delete
    # :type id: string
    _check_access("user_delete", context, data_dict)

    timestamp = _timestamp()

    model = context["model"]
    user_id = _get_or_bust(data_dict, "id")
    user = model.User.get(user_id)

    if user is None:
        raise NotFound('User "{id}" was not found.'.format(id=user_id))

    patch_context = {
        "user": ckan.logic.get_action("get_site_user")({"ignore_auth": True}, {})[
            "name"
        ]
    }

    # Prefix the date/time of delete in ISO format to the email.   testme@example.com becomes deleted202402041212-testme@example.com
    #
    perturbed_email = f"deleted{timestamp}-{user.email}"

    ckan.logic.get_action("user_patch")(
        patch_context, {"id": user_id, "email": perturbed_email}
    )

    # Prefix the date/time of delete in ISO format to the username.   testme becomes 202402041212-testme
    # (AAI usernames can’t start with a digit)
    #

    perturbed_username = f"{timestamp}-{user.name[:244]}"

    ckan.logic.get_action("user_patch")(
        patch_context, {"id": user_id, "name": perturbed_username}
    )

    data_dict_with_id = {"id": user_id}

    return original_action(context, data_dict_with_id)
