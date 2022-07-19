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

from ckanext.bpatheme import (
    action,
    helper,
    blueprint,
)

import logging

log = logging.getLogger(__name__)


class CustomTheme(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IBlueprint)

    # IActions
    def get_actions(self):
        return {"user_create": action.custom_user_create}

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
        toolkit.add_resource("assets", "ckanext-bpatheme")

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator("ignore_missing")
        unicode_safe = toolkit.get_validator("unicode_safe")
        schema.update(
            {
                "ckanext.datawa.slip_harvester_token": [ignore_missing, str],
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
            "get_current_year": helper.get_current_year,
            "wa_license_icon": helper.wa_license_icon,
            "access_level_text": helper.access_level_text,
            "license_data": helper.license_data,
            "datawa_scheming_select_options": helper.datawa_scheming_select_options,
            "datawa_get_option_label": helper.datawa_get_option_label,
            "organization_slugs_by_creation": helper.organization_slugs_by_creation,
            "organization_slugs_by_creation_and_rank": helper.organization_slugs_by_creation_and_rank,
            "get_os_env_value": helper.get_os_env_value,
            "has_embargo": helper.has_embargo,
            "has_timed_embargo": helper.has_timed_embargo,
            "has_embargo_reason": helper.has_embargo_reason,
            "get_embargo_reason": helper.get_embargo_reason,
            "get_embargo_date": helper.get_embargo_date,
            "has_related_data": helper.has_related_data,
            "render_related_data": helper.render_related_data,
            "human_readable_size": helper.human_readable_size,
            "get_pkg_size_in_bytes": helper.get_pkg_size_in_bytes,
            "get_search_size_in_bytes": helper.get_search_size_in_bytes,
            "get_bulk_size_warning_limit": helper.get_bulk_size_warning_limit,
            "get_package_size_for_user": helper.get_package_size_for_user,
        }

    # Ifacets
    def dataset_facets(self, facets_dict, package_type):
        ## In addtion to the defaults, we want these facets
        facets_dict["organization"] = _("Initiative")
        facets_dict["sequence_data_type"] = _("Sequence Data Type")

        ## We want the facets to appear in this order, with any others at the end
        facet_order = ["organization", "sequence_data_type", "res_format", "tags"]

        ## Updating facet positions
        fct_keys = [key for key in list(facets_dict.keys())]
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

        fct_keys = [key for key in list(facets_dict.keys())]
        if "organization" in fct_keys:
            del facets_dict["organization"]

        return facets_dict

    # IBlueprint
    def get_blueprint(self):
        return blueprint.bpatheme
