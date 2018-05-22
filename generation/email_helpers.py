# -*- coding: utf-8 -*-

#    This file is part of Gertrude.
#
#    Gertrude is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    Gertrude is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Gertrude; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
from __future__ import print_function

import os
import smtplib
import math
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from helpers import strip_accents, get_emails, ENVOI_PARENTS, ENVOI_CAF, ENVOI_SALARIES


def send_email(creche_from, emails_to, subject, introduction, attachments=[], debug=False):
    COMMASPACE = ", "

    smtp_server = creche_from.smtp_server if creche_from.smtp_server else "localhost"

    if not emails_to:
        return 0, "Email TO manquant!"

    emails_from = get_emails(creche_from.email)
    if not emails_from:
        return 0, "Email FROM manquant!"

    msg = MIMEMultipart()
    msg['Subject'] = subject
    if smtp_server == "localhost":
        msg_from = "saas@gertrude-logiciel.org"
        msg["Reply-to"] = emails_from[0]
        msg["Return-path"] = emails_from[0]
    else:
        msg_from = emails_from[0]
    msg['From'] = msg_from
    msg['To'] = COMMASPACE.join(emails_to)
    msg['CC'] = COMMASPACE.join(emails_from)

    if introduction:
        if debug:
            print("Introduction email:", introduction)
        part = MIMEMultipart('alternative')
        html = "<html><head><meta charset='UTF-8'></head><body><p>" + introduction.replace("\n", "<br>") + "</p></body></html>"
        part.attach(MIMEText(introduction, 'plain', _charset='UTF-8'))
        part.attach(MIMEText(html, 'html', _charset='UTF-8'))
        msg.attach(part)

    for attachment in attachments:
        with open(attachment, "rb") as f:
            doc = MIMEBase("application", "octet-stream")
            doc.set_payload(f.read())
            encoders.encode_base64(doc)
            doc.add_header("Content-Disposition", "attachment", filename=strip_accents(os.path.split(attachment)[1]))
            msg.attach(doc)

    port, login, password = 25, None, None

    if "/" in smtp_server:
        smtp_server, login, password = smtp_server.split("/")
    if ":" in smtp_server:
        smtp_server, port = smtp_server.split(":")
        port = int(port)

    if debug:
        print("From: %(From)s, To: %(To)s, CC: %(CC)s" % msg)
        print(msg.as_string()[:1200], '...')
    else:
        s = smtplib.SMTP(smtp_server, port)
        if "gmail" in smtp_server:
            s.starttls()
        if login and password:
            s.login(login, password)
        s.sendmail(msg_from, emails_to + emails_from, msg.as_string())
        s.quit()

    return 1, "Email envoyé"


def send_email_to_parents(famille, subject, introduction, attachments, debug=False):
    emails_to = list(set([parent.email for parent in famille.parents if parent and parent.email]))
    return send_email(famille.creche, emails_to, subject, introduction, attachments, debug)


class SendToParentsMixin:
    def __init__(self, subject, introduction_filename, attachments=[], success_message="Message envoyé"):
        self.parents_subject = subject
        self.parents_introduction_filename = introduction_filename
        self.parents_attachments = attachments
        self.parents_success_message = success_message
        self.destination_emails[ENVOI_PARENTS] = [(inscrit, bool(inscrit.famille.get_parents_emails())) for inscrit in self.inscrits]

    def send_to_parents(self, debug=False):
        if len(self.inscrits) == 1:
            if not self.default_output:
                return send_email_to_parents(self.inscrits[0].famille, self.parents_subject,
                                             self.generate_introduction(self.parents_introduction_filename),
                                             self.parents_attachments, debug=debug)
            elif self.generate() and self.convert_to_pdf():
                return send_email_to_parents(self.inscrits[0].famille, self.parents_subject, self.generate_introduction(self.parents_introduction_filename), [self.pdf_output] + self.parents_attachments, debug=debug)
            else:
                return 0, str(self.errors)
        else:
            result = 0
            for inscrit in self.inscrits:
                document = self.split(inscrit)
                status, message = document.send_to_parents(debug=debug)
                # TODO error cases ...
                result += status
            return result, self.parents_success_message % {"count": result}


class SendToSalariesMixin(object):
    def __init__(self, subject, introduction_filename, success_message):
        self.salaries_subject = subject
        self.salaries_introduction_filename = introduction_filename
        self.salaries_success_message = success_message
        self.destination_emails[ENVOI_SALARIES] = [(salarie, bool(salarie.email)) for salarie in self.salaries]

    def send_to_salaries(self, debug=False):
        if len(self.salaries) == 1:
            if self.generate() and self.convert_to_pdf():
                return send_email(self.salaries[0].creche, [self.salaries[0].email], self.salaries_subject, self.generate_introduction(self.salaries_introduction_filename), [self.pdf_output], debug=debug)
            else:
                return 0, str(self.errors)
        else:
            result = 0
            for salarie in self.salaries:
                document = self.split(salarie)
                status, message = document.send_to_salaries(debug=debug)
                # TODO error cases ...
                result += status
            return result, self.salaries_success_message % {"count": result}


class SendToCAFMixin:
    def __init__(self, subject, introduction_filename, success_message):
        self.caf_subject = subject
        self.caf_introduction_filename = introduction_filename
        self.caf_success_message = success_message
        self.caf_packet_size = 5
        if self.creche.caf_email:
            self.destination_emails[ENVOI_CAF] = [(inscrit, True) for inscrit in self.inscrits if inscrit.famille.autorisation_attestation_paje]

    def send_to_caf(self, debug=False):
        if self.creche.caf_email:
            result, index, count = 0, 0, math.ceil(len(self.inscrits) / self.caf_packet_size)
            for i in range(0, len(self.inscrits), self.caf_packet_size):
                index += 1
                files = []
                for inscrit in self.inscrits[i:i+self.caf_packet_size]:
                    attestation = self.split(inscrit)
                    if attestation.generate() and attestation.convert_to_pdf():
                        files.append(attestation.pdf_output)
                status, message = send_email(self.creche, [self.creche.caf_email], self.caf_subject % {"index": index, "count": count}, self.generate_introduction(self.caf_introduction_filename), files, debug=debug)
                result += status
            return result, self.caf_success_message % {"count": result}
        else:
            return False, "Pas d'email CAF"
