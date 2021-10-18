from ckan import model
from ckan.common import c, _
import ckan.logic
import ckan.plugins.toolkit as toolkit
from ckan.logic.action.create import user_create
from ckan.lib.helpers import flash_success

import logging

log = logging.getLogger(__name__)


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
    orgs = toolkit.get_action("get_available_organizations")({}, {})

    for org in orgs:
        id = "org-{}".format(org["name"])
        log.debug("looking for {}".format(id))
        if id in data_dict:
            log.debug("found {}".format(id))
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

    flash_success(_("Membership created.  You have been logged in."))

    return newuser
