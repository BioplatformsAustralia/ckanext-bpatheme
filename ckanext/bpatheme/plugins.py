import datetime
import os
from collections import OrderedDict
import json
import operator
import re
import bitmath

from ckan.common import c, _, config
import ckan.lib.helpers as h
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from markupsafe import Markup

import ckanext.scheming.helpers as sh

from ckanext.bpatheme import action

import logging

log = logging.getLogger(__name__)


def get_current_year():
    return datetime.datetime.today().year


def wa_license_icon(id):
    icons = {
        "cc-by": ["cc", "cc-by"],
        "cc-nc": ["cc", "cc-by", "cc-nc"],
        "cc-by-sa": ["cc", "cc-by", "cc-sa"],
        "cc-zero": ["cc", "cc-zero"],
    }
    if id not in icons:
        return ""
    # return h.url_for_static('license-{}.png'.format(id))
    return Markup(
        "".join(
            '<img width=20 src="{}">'.format(h.url_for_static("{}.png".format(icon)))
            for icon in icons[id]
        )
    )


def datawa_scheming_select_options(field_name):
    schema = sh.scheming_get_dataset_schema("dataset")
    try:
        access_level_options = sh.scheming_field_by_name(
            schema["dataset_fields"], field_name
        )["choices"]
        options = {i["value"]: i["label"] for i in access_level_options}
    except Exception as e:
        raise e
    return options


def datawa_get_option_label(options, option):
    if option in options:
        option_label = options[option]
        return option_label
    return option


def access_level_text(access_level=None, all=False, as_json=False):
    access_level_text = {
        "open": "This dataset is available for use by everyone",
        "open_login": "This dataset is available for use by everyone - login required",
        "fees_apply": "This dataset is available for use subject to payment",
        "restricted": "This dataset is available for use subject to approval",
        "govt_only": "This dataset is available for government use only",
        "mixed": "A variety of access levels apply to this dataset's resources",
    }
    if all:
        return json.dumps(access_level_text) if as_json else access_level_text
    if access_level in access_level_text:
        return access_level_text[access_level]
    return ""


def license_data(pkg):
    license_id = ""
    license_icon = ""
    license_title = ""
    license_url = ""
    license_specified = True

    if "license_id" in pkg and pkg["license_id"]:
        license_id = pkg["license_id"]
        license_title = pkg["license_title"]
        if license_id.startswith("custom"):
            license_icon = "custom"
            if "custom_license_url" in pkg and pkg["custom_license_url"]:
                license_url = pkg["custom_license_url"]
            else:
                license_title = "Custom licence not supplied"
                license_specified = False
        else:
            license_icon = license_id
            if "license_url" in pkg:
                license_url = pkg["license_url"]
    else:
        license_id = "not_specified"
        license_icon = "not_specified"
        license_title = "Licence not supplied"
        license_specified = False

    license_data = {
        "license_id": license_id,
        "license_icon": license_icon,
        "license_title": license_title,
        "license_url": license_url,
        "license_specified": license_specified,
    }

    return license_data


def organization_slugs_by_creation():
    """ Retuns a list of organization slugs ordered from newest to oldest """

    # Get a list of all the site's organizations from CKAN
    organizations = toolkit.get_action("organization_list")(
        data_dict={
            "sort": "package_count desc",
            "all_fields": True,
            "include_dataset_count": True,
            "include_groups": True,
        }
    )

    # FIXME Not sure why this only returns organisations that have packages in them

    # return slugs
    return [
        s["name"]
        for s in sorted(organizations, reverse=True, key=lambda k: k["created"])
    ]


def organization_slugs_by_creation_and_rank():
    """ Retuns a list of organization slugs ordered from 
        highest rank to lowest,
        newest to oldest """

    def multisort(xs, specs):
        for key, reverse in reversed(specs):
            xs.sort(key=operator.itemgetter(key), reverse=reverse)
        return xs

    # Get a list of all the site's organizations from CKAN
    organizations = toolkit.get_action("organization_list")(
        data_dict={
            "sort": "package_count desc",
            "all_fields": True,
            "include_extras": True,
            "include_dataset_count": True,
            "include_groups": True,
        }
    )

    # FIXME Not sure why this only returns organisations that have packages in them

    # generate a list of dicts - slug, creation, rank
    #
    # Add a 'rank' key under the Custom Fields for the organization
    # with either a positive or negative value to manually
    # promote (postive values greater than 1) or demote (values less than 1)
    orgs = []
    for o in organizations:
        rank = 1
        if "extras" in o:
            for e in o["extras"]:
                if e["key"] == "rank":
                    try:
                        rank = int(e["value"])
                    except ValueError:
                        rank = 1
        orgs.append({"slug": o["name"], "created": o["created"], "rank": rank})

    # return slugs sorted by rank, then by created date
    return [
        s["slug"] for s in multisort(list(orgs), (("rank", True), ("created", True)))
    ]


def get_os_env_value(key):
    config_key = "ckanext.bpatheme." + key.lower()
    return config.get(config_key) or os.environ.get(key, "")


# embargo functions


def _is_embargo_current(pkg):
    # if pkg.get('access_control_date', None) or pkg.get('access_control_reason', None):
    embargo = pkg.get("access_control_date", None)
    if not embargo:
        # not found - assume current
        return True

    try:
        embargo_end = datetime.datetime.strptime(embargo, "%Y-%m-%d")
        if embargo_end < datetime.datetime.now():
            return False
    except ValueError:
        return True

    return True


def has_embargo(pkg):
    mode = pkg.get("access_control_mode", "")
    if mode in ("open"):
        return False

    if mode in ("closed", "date"):
        if mode in ("date") and not _is_embargo_current(pkg):
            return False
        else:
            return True

    if pkg.get("access_control_date", None) or pkg.get("access_control_reason", None):
        return True

    return False


def has_timed_embargo(pkg):
    embargo = pkg.get("access_control_date", None)
    try:
        if embargo and datetime.datetime.strptime(embargo, "%Y-%m-%d"):
            return True
    except ValueError:
        return False

    return False


def has_embargo_reason(pkg):
    if "access_control_reason" in pkg:
        if (
            pkg["access_control_reason"] is not None
            and len(pkg["access_control_reason"]) > 0
        ):
            return True
    return False


def get_embargo_reason(pkg):
    return pkg.get("access_control_reason", "")


def get_embargo_date(pkg):
    return pkg.get("access_control_date", None)


def has_related_data(pkg):
    related = pkg.get("related_data", "")
    if related:
        return True

    return False


def make_ands_id(s):
    "returns a BPA ID with the prefix"

    BPA_PREFIX = "102.100.100/"
    ands_id_re = re.compile(r"^102\.100\.100[/\.](\d+)$")
    ands_id_abbrev_re = re.compile(r"^(\d+)$")

    m = ands_id_re.match(s)
    if m:
        return BPA_PREFIX + m.groups()[0]
    m = ands_id_abbrev_re.match(s)
    if m:
        return BPA_PREFIX + m.groups()[0]
    return s


def render_related_data(pkg):
    recognised = {}
    recognised["sample_id"] = "Sample ID"
    recognised["bpa_sample_id"] = "Sample ID"
    recognised["dataset_id"] = "Dataset ID"
    recognised["bpa_dataset_id"] = "Dataset ID"
    recognised["library_id"] = "Library ID"
    recognised["bpa_library_id"] = "Library ID"
    recognised["ticket"] = "Ticket"

    related = pkg.get("related_data", "")
    words = related.split()
    description = []
    links = []

    for item in words:
        x = re.search("^(\w+):(.*)$", item)
        if x:
            links.append((item, x.group(0), x.group(1), x.group(2)))
        else:
            description.append(item)

    response = "<p>" + " ".join(description) + "</p>"
    if links:
        response += "<ul>"
        for link in links:
            key = link[2]
            if key in recognised:
                key_name = recognised[key]
                value = link[3]
                if re.match("(bpa_)?(library|dataset|sample)_id", key):
                    # these need to be in ANDS format
                    query = "{}:{}".format(key, make_ands_id(value))
                else:
                    query = link[1]
                response += "<li>"
                response += '<a href="{}">{}</a>'.format(
                    h.url_for(controller="package", action="search", q=query),
                    "{} {}".format(key_name, value),
                )
                response += "</li>"
            else:
                response += "<li>{}</li>".format(link[0])
        response += "</ul>"

    return response


def get_search_size_in_bytes(items):
    search_size = 0
    for pkg in items:
        search_size = search_size + get_pkg_size_in_bytes(pkg)
    return search_size


def get_pkg_size_in_bytes(pkg):
    total_size_in_bytes = 0
    resources = pkg.get("resources", None)
    if resources is not None:
        for resource in resources:
            if resource.get("size", None):
                try:
                    res_size = int(resource.get("size", 0))
                except ValueError:
                    res_size = 0   # we got a string that wasn't a number
                total_size_in_bytes = total_size_in_bytes + res_size
    return total_size_in_bytes


def human_readable_size(size_in_bytes):

    return bitmath.Byte(bytes=size_in_bytes).best_prefix().format("{value:.2f} {unit}")


def get_bulk_size_warning_limit():
    return toolkit.asint(config.get("ckanext.bulk.download_size_warning_bytes", 104857600))


class CustomTheme(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IActions)

    # IActions
    def get_actions(self):
        return {"user_create": action.custom_user_create}

    # IRoutes
    def after_map(self, map):
        map.connect(
            "bpatheme_summary",
            "/summary",
            controller="ckanext.bpatheme.controller:SummaryController",
            action="index",
        )

        map.connect(
            "bpatheme_contact",
            "/contact",
            controller="ckanext.bpatheme.controller:ContactController",
            action="index",
        )

        map.connect(
            "bpatheme_webtoken",
            "/user/private/api/bpa/check_permissions",
            controller="ckanext.bpatheme.controller:TokenController",
            action="bioplatforms_webtoken",
        )

        return map

    # IPackageController
    def before_search(self, search_params):
        def make_insensitive(query):
            twiddled = []

            for c in query:
                if c.isalpha():
                    twiddled.append("[")
                    twiddled.append(c.upper())
                    twiddled.append(c.lower())
                    twiddled.append("]")
                else:
                    twiddled.append(c)

            output = u""

            return output.join(twiddled)

        # fix for ckanext-hierarchy required by migration to 2.8
        try:
            c.fields
        except AttributeError:
            c.fields = []

        # Search by fields for BPA Data Portal

        extras = search_params.get("extras")
        if not extras:
            # There are no extras in the search params, so do nothing.
            return search_params
        search_by = extras.get("ext_search_by")
        if not search_by:
            # The user didn't specify a specific field, so do nothing
            return search_params

        # Prepend the field name to the query
        q = search_params["q"]
        q = make_insensitive(q)
        search_terms = []
        for term in q.split():
            search_terms.append(
                "{search_by}:/.*{q}.*/".format(q=term, search_by=search_by)
            )
        q = " AND ".join(search_terms)
        search_params["q"] = q

        return search_params

    # IConfigurer
    def update_config(self, config):
        toolkit.add_template_directory(config, "templates")
        toolkit.add_public_directory(config, "static")
        toolkit.add_resource("fanstatic", "bpatheme")

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator("ignore_missing")
        unicode_safe = toolkit.get_validator("unicode_safe")
        schema.update(
            {
                "ckanext.datawa.slip_harvester_token": [ignore_missing, unicode],
                "ckanext.bpatheme.comms_message": [ignore_missing, unicode_safe],
                "ckanext.bpatheme.comms_title": [ignore_missing, unicode_safe],
                "ckanext.bpatheme.comms_link_href": [ignore_missing, unicode_safe],
                "ckanext.bpatheme.comms_link_text": [ignore_missing, unicode_safe],
                "ckanext.bpatheme.comms_owner": [ignore_missing, unicode_safe],
            }
        )
        return schema

    # ITemplateHelpers
    def get_helpers(self):
        return {
            "get_current_year": get_current_year,
            "wa_license_icon": wa_license_icon,
            "access_level_text": access_level_text,
            "license_data": license_data,
            "datawa_scheming_select_options": datawa_scheming_select_options,
            "datawa_get_option_label": datawa_get_option_label,
            "organization_slugs_by_creation": organization_slugs_by_creation,
            "organization_slugs_by_creation_and_rank": organization_slugs_by_creation_and_rank,
            "get_os_env_value": get_os_env_value,
            "has_embargo": has_embargo,
            "has_timed_embargo": has_timed_embargo,
            "has_embargo_reason": has_embargo_reason,
            "get_embargo_reason": get_embargo_reason,
            "get_embargo_date": get_embargo_date,
            "has_related_data": has_related_data,
            "render_related_data": render_related_data,
            "human_readable_size": human_readable_size,
            "get_pkg_size_in_bytes": get_pkg_size_in_bytes,
            "get_search_size_in_bytes": get_search_size_in_bytes,
            "get_bulk_size_warning_limit": get_bulk_size_warning_limit,
        }

    # Ifacets
    def dataset_facets(self, facets_dict, package_type):
        ## In addtion to the defaults, we want these facets
        facets_dict["organization"] = _("Initiative")
        facets_dict["sequence_data_type"] = _("Sequence Data Type")

        ## We want the facets to appear in this order, with any others at the end
        facet_order = ["organization", "sequence_data_type", "res_format", "tags"]

        ## Updating facet positions
        fct_keys = [key for key in facets_dict.keys()]
        # remove any items from facet_order not in fct_keys
        facet_order = [item for item in facet_order if item in fct_keys]
        # generate new order of facet_keys following facet_order
        for item in facet_order:
            fct_keys.insert(facet_order.index(item), fct_keys.pop(fct_keys.index(item)))
        # create OrderedDict of facets
        updated_facet_dict = OrderedDict([(key, facets_dict[key]) for key in fct_keys])
        facets_dict = updated_facet_dict

        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        facets_dict = self.dataset_facets(facets_dict, package_type)

        fct_keys = [key for key in facets_dict.keys()]
        if "organization" in fct_keys:
            del facets_dict["organization"]

        return facets_dict
