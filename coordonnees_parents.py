# -*- coding: utf-8 -*-

##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 3 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, see <http://www.gnu.org/licenses/>.

from constants import *
from functions import *
from facture import *
from ooffice import *

class CoordonneesModifications(object):
    def __init__(self, site, date):
        self.multi = False
        self.template = 'Coordonnees parents.odt'
        self.site = site
        if date is None:
            self.date = today
        else:
            self.date = date
        self.default_output = u"Coordonnees parents %s.ods" % GetDateString(self.date, weekday=False)
        self.email = None
        self.site = None
        
    def execute(self, filename, dom):
        # print dom.toprettyxml()
        if filename != 'content.xml':
            return None

        fields = [('nom-creche', creche.nom),
                  ('adresse-creche', creche.adresse),
                  ('code-postal-creche', str(creche.code_postal)),
                  ('ville-creche', creche.ville),
                  ('telephone-creche', creche.telephone),
                  ('email-creche', creche.email),
                  ('date', '%.2d/%.2d/%d' % (self.date.day, self.date.month, self.date.year))
                 ]
        ReplaceTextFields(dom, fields)
        
        for table in dom.getElementsByTagName('table:table'):
            if table.getAttribute('table:name') == 'Enfants':                
                template = table.getElementsByTagName('table:table-row')[1]
                #print template.toprettyxml()
                for inscrit in creche.inscrits:
                    inscription = inscrit.GetInscription(self.date) 
                    if inscription and (self.site == None or inscription.site == self.site):
                        line = template.cloneNode(1)
                        referents = [GetPrenomNom(referent) for referent in inscrit.referents]
                        parents = [GetPrenomNom(parent) for parent in inscrit.parents.values() if parent is not None]
                        ReplaceTextFields(line, [('prenom', inscrit.prenom),
                                                 ('parents', parents),
                                                 ('referents', referents),
                                                 ('commentaire', None)])
                        phoneCell = line.getElementsByTagName('table:table-cell')[2]
                        phoneTemplate = phoneCell.getElementsByTagName('text:p')[0]
                        phones = { } # clé: [téléphone, initiales, ?travail]
                        emails = set()
                        for parent in inscrit.parents.values():
                            if parent:
                                emails.add(parent.email)
                                for phoneType in ["domicile", "portable", "travail"]:
                                    phone = getattr(parent, "telephone_"+phoneType)
                                    if phone:
                                        if phone in phones.keys():
                                            phones[phone][1] = ""
                                        else:
                                            phones[phone] = [phone, GetInitialesPrenom(parent), phoneType=="travail"]
                        for phone, initiales, phoneType in phones.values():
                            remark = initiales
                            if initiales and phoneType:
                                remark = "(%s travail)" % initiales
                            elif initiales:
                                remark = "(%s)" % initiales
                            elif phoneType:
                                remark = "(travail)"
                            else:
                                remark = ""
                            phoneLine = phoneTemplate.cloneNode(1)
                            ReplaceTextFields(phoneLine, [('telephone', phone),
                                                          ('remarque', remark)])
                            phoneCell.insertBefore(phoneLine, phoneTemplate)
                        phoneCell.removeChild(phoneTemplate)
                        emailCell = line.getElementsByTagName('table:table-cell')[3]
                        emailTemplate = emailCell.getElementsByTagName('text:p')[0]
                        for email in emails:
                            emailLine = emailTemplate.cloneNode(1)
                            ReplaceTextFields(emailLine, [('email', email)])
                            emailCell.insertBefore(emailLine, emailTemplate)
                        emailCell.removeChild(emailTemplate)
                        table.insertBefore(line, template)
                table.removeChild(template)

            if table.getAttribute('table:name') == 'Employes':
                template = table.getElementsByTagName('table:table-row')[0]
                #print template.toprettyxml()
                for salarie in creche.salaries:
                    if 1: # TODO
                        line = template.cloneNode(1)
                        ReplaceTextFields(line, [('prenom', salarie.prenom),
                                                 ('nom', salarie.nom),
                                                 ('domicile', salarie.telephone_domicile),
                                                 ('portable', salarie.telephone_portable)])
                        table.insertBefore(line, template)
                table.removeChild(template)

        return None
