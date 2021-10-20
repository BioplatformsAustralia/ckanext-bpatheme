from ckan.lib.mailer import mail_user
from ckan.common import _
import logging

log = logging.getLogger(__name__)

def _MESSAGE_WELCOME_EMAIL():
    return _("""\
Welcome, %(user)s, to the Bioplatforms Australia Data Portal

You can access the portal using the following URL:
    %(siteurl)s

Please log in using your username - %(username)s - with the password 
you provided.  Do not use your email.

For information on how to find or download data from the portal, please see 
our support guides at:
    https://usersupport.bioplatforms.com/

You can request access to additional initiatives at:
    %(siteurl)s/member-request/new

Please make sure you check the Data Use Agreement and Policy for the
initiatives you have request access to.

For datasets less than 12 months old that are still under embargo, we request 
that you reach out to their data custodian for collaboration opportunities.
If you are unsure of who to contact, please let us know and we can facilitate
a conversation.

Use of the Bioplatforms Australia Data Portal is subject to Terms and
Conditions.  These, along with a Privacy statement on data collection, can be
found at:
    https://bioplatforms.com/terms-and-conditions/

Feel free to contact us if you have any questions, and feedback is always
welcome.

 
Best wishes,
%(sitename)s
%(siteemail)s
""")


def _SUBJECT_WELCOME_EMAIL():
    return _(
            "Welcome to the Bioplatforms Australia Data Portal")


def mail_welcome_email(user, site_name, site_email, site_url):
    subject = _SUBJECT_WELCOME_EMAIL()
    message = _MESSAGE_WELCOME_EMAIL() % {
        'user': user.display_name,
        'username': user.username,
        'email': user.email,
        'siteurl': site_url,
        'sitename': site_name,
        'siteemail': site_email,
    }
    headers = {
        'Reply-To': "{} <{}>".format(site_name, site_email),
    }

    try:
        mail_user(user, subject, message, headers)
    except Exception:
        log.exception("Mail could not be sent")
