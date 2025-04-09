import datetime
import os
from collections import OrderedDict
import json
import operator
import re
import bitmath
from urllib.parse import urlparse
from ckan.common import c
import ckan.authz as authz

from ckan.common import g, c, _, config
import ckan.lib.helpers as h
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from markupsafe import Markup
from ckan.lib.webassets_tools import render_assets

import ckanext.scheming.helpers as sh

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
    """Retuns a list of organization slugs ordered from
    highest rank to lowest,
    newest to oldest"""

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


def find_organizations_for_user():
    organizations = toolkit.get_action("organization_list")(
        data_dict={
            "all_fields": True,
            "include_extras": True,
            "include_dataset_count": False,
            "include_groups": True,
        }
    )

    if authz.is_sysadmin(c.user):    # user is a sysadmin, return them all
        # admin user, return them all
        return organizations
    else:
        allowed_organizations = toolkit.get_action("organization_list_for_user")(
            data_dict={
                "all_fields": True,
                "include_extras": True,
                "include_dataset_count": False,
                "include_groups": True,
            }
        )
        for org in organizations:
            if org not in allowed_organizations:
                org_allowed = True
                for extra in org.get("extras"):
                    if extra.get("key") == "Private" and extra.get("value") == "True":
                        org_allowed = False
                if org_allowed:
                    allowed_organizations.append(org)
        return allowed_organizations

def find_autoregister_organizations():

    all_organizations = toolkit.get_action("organization_list")(
        data_dict={
            "all_fields": True,
            "include_extras": False,
            "include_dataset_count": False,
            "include_groups": False,
            }
        )

    allowed_organizations = []
    for org in all_organizations:
        if org["name"] in config.get('ckanext.ytp_request.autoregister').split():
            allowed_organizations.append(org)

    return allowed_organizations

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
        # anything in recognised, plus any doi / http / https link
        if x:
            links.append((item, x.group(0), x.group(1), x.group(2)))
        else:
            description.append(item)

    response = "<p>" + " ".join(description) + "</p>"
    if links:
        response += "<ul>"
        for link in links:
            response += "<li>"
            key = link[2]
            if key in recognised:
                key_name = recognised[key]
                value = link[3]
                if re.match("(bpa_)?(library|dataset|sample)_id", key):
                    # these need to be in ANDS format
                    query = "{}:{}".format(key, make_ands_id(value))
                else:
                    query = link[1]
                response += '<a href="{}">{}</a>'.format(
                    h.url_for("dataset.search", q=query),
                    "{} {}".format(key_name, value),
                )
            elif key in ['doi',]:
                response += '<a href="{}">{}</a>'.format(
                    "https://doi.org/{}".format(link[3]),
                    link[0]
                )
            elif key in ['http','https']:
                response += '<a href="{}">{}</a>'.format(
                    link[0],link[0]
                )
            else:
                response += "{}".format(link[0])
            response += "</li>"
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
                    res_size = 0  # we got a string that wasn't a number
                total_size_in_bytes = total_size_in_bytes + res_size
    return total_size_in_bytes


def get_package_size_for_user(pkg):
    pkg_size_in_bytes = get_pkg_size_in_bytes(pkg)
    if pkg_size_in_bytes > 0:
        package_size = human_readable_size(pkg_size_in_bytes)
        return package_size

    return ""


def human_readable_size(size_in_bytes):

    return bitmath.Byte(bytes=size_in_bytes).best_prefix().format("{value:.2f} {unit}")


def get_bulk_size_warning_limit():
    return toolkit.asint(
        config.get("ckanext.bulk.download_size_warning_bytes", 104857600)
    )

def url_last_segment_matches(url,to_match):
    parsed = urlparse(url.rstrip("/")) # remove any trailing slash on URLs
    segments = parsed.path.split("/")
    if segments[-1] == to_match:
        return True
    return False

def external_styles():
    # This is hacky as CKAN webassets doesn't directly expose the list of 
    # paths/URLS for CSS or Javascript
    paths = []
    base_url = config.get('ckan.site_url', "")

    regex = r"^<link href=\"(.*)\" rel=\"stylesheet\"\/>$"

    assets = render_assets('style')

    matches = re.finditer(regex, assets, re.MULTILINE)

    for matchNum, match in enumerate(matches, start=1):
        for groupNum in range(0, len(match.groups())):
            groupNum = groupNum + 1
            paths.append(match.group(groupNum))

    return ''.join(f"@import url('{base_url}{path}');\n" for path in paths)


def is_orgname_in_list(name, allowed_orgs):
    in_list = False
    for org in allowed_orgs:
        if org["name"] == name:
            in_list = True

    return in_list


def order_schema_fields(fields):
    """
    This method will sort the incoming fields in the following order:
    If the field name is in a list of the "Show first fields",  these fields should appear first in the returned list,
    in the order of the "show first list".
    If the field name is in a list of the "Show last fields", these fields should appear last inn the returned list, in
    the order of the show last list.
    If the field name is in neither list, it should appear wih others of its ilk, in alphabetical order.
    NB: also, a field will not appear on the rendered page if it appears in the "exclude_fields" list in
     ckanext-scheming/ckanext/scheming/templates/scheming/package/snippets/additional_info.html
    """
    first_list = []
    last_list = []

    """
    Remove these list as initially proposed by Sophie, until after revisit of metadata spreadsheet standardization
    first_list = [
        "bioplatforms_project_code",
        "bioplatforms_sample_id",
        "bioplaforms_library_id",
        "bioplatforms_dataset_id",
        "sample_id",
        "library_id",
        "dataset_id",
        "bpa_sample_id",
        "bpa_library_id",
        "bpa_dataset_id",
        "taxonomic_group",
        "common_name",
        "scientific_name",
        "phylum",
        "class",
        "order",
        "family",
        "genus",
        "species",
        "taxon_id",
        "specimen_id",
        "tissue_number",
        "sample_custodian",
        "state_or_region",
        "wild_captive",
        "data_context",
        "data_custodian",
        "sequencing_facility",
        "data_type",
        "sequencing_model",
        "date_of_transfer",
        "date_generated",
    ]

    last_list = [
        "ala_specimen_url",
        "ancillary_notes",
        "associated_media",
        "sequencing_kit_chemistry",
        "analysis_software",
        "analysis_software_version",
        "model_base_caller",
        "fast5_compression"
        "work_order",
        "ticket",
        "folder_name",
        "access_control_reason",
        "access_control_date",
        "access_control_mode",
        "archive_ingestion_date",
        "base_url",
        "resource_permissions",
    ]
    """
    first_fields = [field for field_name in first_list for field in fields if field_name == field["field_name"]]

    last_fields = [field for field_name in last_list for field in fields if field_name == field["field_name"]]

    difference = [x for x in fields if x not in (first_fields + last_fields)]
    ordered_fields = first_fields + difference + last_fields

    return ordered_fields


def get_projects_in_reverse_ranking_order():
    projects = []

    amdb = {'logo' : "new_ausmicro_logo.webp",
            'has_logo' : "true",
            'icon' : "icon_amd.webp",
            'iconalt' : "icon_amd.png",
            'slug' : "australian-microbiome",
            'url' : "https://bioplatforms.com/projects/australian-microbiome/",
            'title' : "Australian Microbiome",
            'description' : "The Australian Microbiome Database is a collaborative project to create a public " \
                "resource containing microbial genome and associated site specific metadata information from a "\
                "range of Australian environments including soils, marine and freshwater.",
            }
    projects.append(amdb)

    sepsis = {'logo' : "sepsis.webp",
              'icon' : "icon_sepsis.webp",
              'iconalt' : "icon_sepsis.png",
              'slug' : "bpa-sepsis",
              'url' : "https://bioplatforms.com/projects/sepsis/",
              'title' : "Antibiotic Resistant Sepsis Pathogens",
              'description' : "The Antibiotic Resistant Sepsis Pathogens Framework Initiative aims to develop a "\
                   "framework dataset that will enable identification of core targets common to "\
                   "antibiotic-resistant sepsis pathogens.",
            }
    projects.append(sepsis)

    omg = {'logo' : "omg-logo.webp",
           'has_logo' : "true",
           'special_class' : "no-circular-logo",
           'icon' : "icon_omg.webp",
           'iconalt' : "icon_omg.png",
           'slug' : "bpa-omg",
           'url' : "https://bioplatforms.com/oz-mammals/",
           'title' : "Oz Mammals Genomics Initiative",
           'description' : "The Oz Mammals Genomics Initiative is an Australia-wide collaboration involving "\
               "researchers from more than 30 institutions, which aims to develop genomic resources for Australia's "\
               "mammals.",
           }
    projects.append(omg)

    gap = {'logo' : "Logo_plants_updown.webp",
           'has_logo' : "true",
           'special_class' : "no-circular-logo",
           'icon' : "icon_gap.webp",
           'iconalt' : "icon_gap.png",
           'slug' : "bpa-plants",
           'url' : "https://bioplatforms.com/projects/genomics-for-australian-plants/",
           'title' : "Genomics for Australian Plants",
           'description' : "The Genomics for Australian Plants Initiative is a national collaborative project, which "\
               "aims to develop genomic resources for the Australian plants community.",
           }
    projects.append(gap)

    ausarg = {'logo' : "AusARG-Logo-RGB-150dpi-Transparent.webp",
              'has_logo' : "true",
              'icon' : "icon_arg.webp",
              'iconalt' : "icon_arg.png",
              'slug' : "ausarg",
              'url' : "https://bioplatforms.com/projects/reptiles-and-amphibians/",
              'title' : "Australian Amphibian and Reptile Genomics Initiative",
              'description' : "The Australian Amphibian and Reptile Genomics Initiative is a national collaborative "\
                  "project that that will facilitate research using genomics approaches towards a more thorough "\
                  "understanding of evolution and conservation of Australia’s unique native Amphibians and Reptiles.",
              }
    projects.append(ausarg)

    tsi = {'logo' : "Threatened-Species-Initiative-Logo-150dpi-RGB.webp",
           'has_logo' : "true",
           'icon' : "icon_tsi.webp",
           'iconalt' : "icon_tsi.png",
           'slug' : "threatened-species",
            'url' : "https://bioplatforms.com/projects/threatened-species/",
            'title' : "Threatened Species Initiative",
            'description' : "The Threatened Species Initiative (TSI) will create a national library of genomic data "\
                 "to support decision-making for biodiversity conservation.",
            }
    projects.append(tsi)

    gbr = {'logo' : "coral.webp",
           'icon' : "icon_gbr.webp",
           'iconalt' : "icon_gbr.png",
           'slug' : "bpa-great-barrier-reef",
           'url' : "https://bioplatforms.com/projects/great-barrier-reef/",
           'title' : "Great Barrier Reef",
           'description' : "The Sea-quence Project is generating core genetic data for corals from the Great Barrier "\
                           "Reef and Red Sea to ultimately help guide reef management practices.",
           }
    projects.append(gbr)

    melanoma = {'logo' : "melanoma.webp",
                'icon' : "icon_melanoma.webp",
                'iconalt' : "icon_melanoma.png",
                'slug' : "bpa-melanoma",
                'url' : "https://bioplatforms.com/melanoma",
                'title' : "Melanoma",
                'description' : "The Melanoma Genomics Project aims to whole genome sequence approximately 500 "\
                "melanoma patients.",
               }
    projects.append(melanoma)

    wpt = {'logo' : "fusarium_head_blight_infected_ear.webp",
           'icon' : "icon_wheat_pathogens_transcript.webp",
           'iconalt' : "icon_wheat_pathogens_transcript.png",
           'slug' : "bpa-wheat-pathogens-transcript",
           'url' : "https://bioplatforms.com/wheat-datasets",
           'title' : "Wheat Pathogens Transcript",
           'description' : "This dataset contains transcript sequence data from 8 different fungal pathogen species "\
                "of wheat.",
           }
    projects.append(wpt)

    wpg = {'logo' : "stagonospora_nodorum.webp",
           'icon' :"icon_wheat_pathogens_genomes.webp",
           'iconalt' :"icon_wheat_pathogens_genomes.png",
           'slug' : "bpa-wheat-pathogens-genomes",
           'url' : "https://bioplatforms.com/wheat-datasets",
           'title' : "Wheat Pathogens Genomes",
           'description' : "This dataset contains the genomic sequence from 10 fungal and 2 bacterial pathogen "\
                "species.Among the pathogens sequenced are the causal agents of stripe rust, stem rust, tan spot, "\
                "glume blotch, septoria leaf blotch, bare patch and crown rot/head blight.",
            }
    projects.append(wpg)

    wc = {'logo' : "wheat.webp",
          'icon' : "icon_wheat.webp",
          'iconalt' : "icon_wheat.png",
          'slug' : "bpa-wheat-cultivars",
          'url' : "https://bioplatforms.com/wheat-datasets",
          'title' : "Wheat Cultivars",
          'description' : "This dataset contains genomic sequence information from 16 wheat varieties of importance "\
              "to Australia selected and prioritised by the major stakeholders of the Australian grains research "\
              "community based on availability of mapping populations and genetic diversity.",
          }
    projects.append(wc)

    stemcells = {'logo' : "stemcell.webp",
                 'icon' : "icon_stemcells.webp",
                 'iconalt' : "icon_stemcells.png",
                 'slug' : "bpa-stemcells",
                 'url' : "https://bioplatforms.com/stem-cells",
                 'title' : "Stem Cells",
                 'description' : "Stem cells allow us to study fundamental processes in tissue growth, "\
                      "development, aging and disease.",
            }
    projects.append(stemcells)

    grasslands = {'logo' : "Australian-Grasslands.webp",
                  'icon' : "icon_grasslands.webp",
                  'iconalt' : "icon_grasslands.png",
                  'slug' : "grasslands",
                  'url' : "https://bioplatforms.com/projects/australian-grasslands/",
                  'title' : "Australian Grasslands",
                  'description' : "The Australian Grasslands Initiative is a national collaborative project, which "\
                      "aims to identify mechanisms of adaptation in grasses to Australia's diverse range of soils "\
                      "and climates.",
                  }
    projects.append(grasslands)

    pp = {'logo' : "plant_pathogen.webp",
          'icon' : "icon_plant_pathogen.webp",
          'iconalt' : "icon_plant_pathogen.png",
          'slug' : "plant-pathogen",
          'url' : "https://bioplatforms.com/projects/plant-pathogen-omics/",
          'title' : "Plant Pathogen 'Omics",
          'description' : "The Plant Pathogen ‘Omics Initiative is a national collaborative project, which aims to "\
              "generate high quality molecular reference data for plant  pathogens in Australia to support "\
              "fundamental research and development in plant protection and contribute to an effective national "\
              "biosecurity surveillance system.",
          }
    projects.append(pp)

    fungi = {'logo' : "fungi.webp",
             'icon' : "fungi.webp",
             'iconalt' : "fungi.png",
             'slug' : "fungi",
             'url' : "https://bioplatforms.com/projects/fungi/",
             'title' : "Fungi Functional 'Omics",
             'description' : "The fungal kingdom sits taxonomically separated from plants and animals. They have "\
                 "unique characteristics including structure, metabolites, nutritional properties and ecological "\
                 "functions.<br\\> Globally, currently 148,000 species of fungi are recognised, the majority in "\
                 "the phyla Ascomycota and Basidiomycota. The vast majority of the total estimated 2.2-3.8 million "\
                 "fungal species, over 90%, are currently unknown to science. The majority of the knowledge on the "\
                 "species in Australia stems from alignment of species commonly thought to have originated, or be "\
                 "analogues to northern hemisphere fungal species. Australian mycologists have attempted to study "\
                 "native fungi relying primarily on classical morphology, which has often led to the incorrect "\
                 "identification of taxa or identification by alignment to northern hemisphere taxa. <br /> <br />"\
                 "The generation of omics data will enable the discovery of native fungal functions that may provide "\
                 "new avenues for emerging industries, in particular for native foods or to demonstrate provenance of "\
                 "foods, biologically active discoveries, biomaterial engineering, land restoration, waste management "\
                 "and circular economies. Additionally, characterising organisms, substrates and growth environments "\
                 "could accelerate the development of fungal based products or processors while, simultaneously, "\
                 "benefitting basic microbiological science and the engineering of biological systems.",
            }
    projects.append(fungi)

    cipps = {'logo' : "cipps.webp",
             'icon' : "cipps.webp",
             'iconalt' : "cipps.png",
             'slug' : "cipps",
             'url' : "https://cipps.org.au/",
             'title' : "ARC Centre of Excellence for Innovations in Peptide and Protein Science (CIPPS)",
             'description' : "The ARC Centre of Excellence for Innovations in Peptide and Protein Science (CIPPS) is "\
                 "a national research centre funded through the Australian Research Council's Centres of Excellence "\
                 "scheme. CIPPS' vision is to discover new proteins and peptides from Australia's diverse flora and "\
                 "fauna, decode their biological functions, and develop new proteins and peptides to address "\
                 "challenges in health, agriculture and industry. Together with industry partners and international "\
                 "collaborators CIPPS are working to unleash the power of peptides and proteins for the benefit of "\
                 "humankind. CIPPS is developing research and outreach programs to promote peptide and protein "\
                 "science, and is deeply committed to nurturing the next generation of researchers.<br />"\
                 "For more information on the Centre please look at their website https://cipps.org.au/<br />"\
                 "Bioplatforms Australia establishes ongoing partnerships with Australian Research Council Centres of "\
                 "Excellence (ARC CoE). These large programs generate varied data resources that have potential for "\
                 "reuse by the  research community.<br />"\
                 "These datasets are under embargo with moderated access to allow for the prioritisation of the "\
                 "activities of the relevant Centres. The length of embargo is defined with the project leads in view "\
                 "of releasing the datasets for public access in due time, fulfilling the remit of Bioplatforms "\
                 "Australia (enabled through NCRIS).<br/>"\
                 "If any of these datasets presents interest to you, please contact us through help@bioplatforms.com "\
                 "and we will assist with communication to the project lead(s) to discuss potential collaboration and "\
                 "data access at their discretion.",
            }
    projects.append(cipps)

    ppa = {'logo' : "ppa.webp",
             'icon' : "ppa.webp",
             'iconalt' : "ppa.png",
             'slug' : "ppa",
             'url' : "https://bioplatforms.com/projects/plant-protein-atlas-initiative/",
             'title' : "Plant Protein Atlas",
             'description' : "The Plant Protein Atlas Initiative will use targeted ‘omics technologies, including "\
                 "genomics, proteomics, metabolomics and phenomics (with the NCRIS-enabled Australian Plant Phenomics "\
                 "Facility) to guide and support progress in genetic and agronomy research towards the optimisation "\
                 "of pulse crops for protein harvest and processing, underpinning an ongoing effort in developing a "\
                 "quality Australian plant protein production industry.",
            }
    projects.append(ppa)

    fish = {'logo' : "fish.webp",
             'icon' : "fish.webp",
             'iconalt' : "fish.png",
             'slug' : "aus-fish",
             'url' : "https://bioplatforms.com/projects/australian-fish-genomics-initiative/",
             'title' : "Australian Fish Genomics",
             'description' : "The Australian Fish Genomics Initiative aims to build a foundation of genomic data, "\
                 "including phylogenomics, reference genomes, population genetics, to advance our understanding and "\
                 "conservation of Australia’s unique native fish.",
            }
    projects.append(fish)

    avian = {'logo' : "avian.webp",
             'icon' : "avian.webp",
             'iconalt' : "avian.png",
             'slug' : "aus-avian",
             'url' : "https://bioplatforms.com/projects/australian-avian-genomics-initiative/",
             'title' : "Australian Avian Genomics",
             'description' : "The Australian Avian Genomics Initiative aims to build a foundation of genomic data, "\
                  "including phylogenomics, reference genomes, population genetics, to advance our understanding and "\
                  "conservation of Australia’s unique native birds.",
            }
    projects.append(avian)

    ipm = {'logo' : "Integrated Pest Management Logo.webp",
           'has_logo': "true",
           'special_class': "no-circular-logo",
             'icon' : "ipm.webp",
             'iconalt' : "ipm.png",
             'slug' : "bpa-ipm",
             'url' : "https://bioplatforms.com/projects/integrated-pest-management-omics-initiative/",
             'title' : "Integrated Pest Management 'Omics Initiative (IPM Omics)",
             'description' : "The Integrated Pest Management Omics initiative is a national program set to transform "\
                  "our understanding of Australia’s diverse pest and beneficial insect populations and will play a "\
                  "pivotal role in supporting data informed integrated pest management (IPM) strategies in Australia.",
            }
    projects.append(ipm)

    forest_resilience = {'logo' : "forest_resilience.webp",
           'has_logo': "true",
           'special_class': "no-circular-logo",
             'icon' : "forest_resilience.webp",
             'iconalt' : "forest_resilience.png",
             'slug' : "forest-resilience",
             'url' : "https://bioplatforms.com/projects/forest-resilience/",
             'title' : "Genomics for Forest Resilience",
             'description' : "The Genomics for Forest Resilience Initiative a national collaborative project which "\
                  "seeks to accelerate the creation of referential and population genomic data for Australia’s forest "\
                  "species to support effective restoration and management strategies for Australia’s diverse and "\
                  "distinct forest ecosystems. ",
         }
    projects.append(forest_resilience)
    ranking = organization_slugs_by_creation_and_rank()

    for p in projects:
        order = 0
        if p["slug"] in ranking:
            order = len(ranking) - ranking.index(p["slug"])
        p.update({'order': order})

    return sorted(projects, key=lambda x: x.get('order'), reverse=True)


def check_user_dataset_access():
    # helper method to determine if the "Datasets" tab should appear for the given user
    # If the user is an Admin, then, yes, always
    if authz.is_sysadmin(c.user):
        return True
    # If the user has any owned/created datasets, then yes.
    #todo - how to figure out if we own any datasets...
    # otherwise no
    return False


def is_bioproject(ncbi_bioproject_accession):
    "Checks if passed argument looks like a NCBI Bioproject Access identifier"
    # Example format is PRJNA512907

    bioproject_re = re.compile(r"^PRJNA(\d+)$")

    m = bioproject_re.match(ncbi_bioproject_accession)
    if m:
        return True

    return False

def render_ncbi_bioproject_url(ncbi_bioproject_accession):
    # Example format is https://www.ncbi.nlm.nih.gov/bioproject/PRJNA512907/

    if not is_bioproject(ncbi_bioproject_accession):
        return ""

    return "https://www.ncbi.nlm.nih.gov/bioproject/%s/" % (ncbi_bioproject_accession,)
