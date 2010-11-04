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
    def __init__(self, date):
        self.template = 'Coordonnees parents.odt'
        if date is None:
            self.date = today
        else:
            self.date = date
        self.default_output = u"Coordonnees parents %s.ods" % GetDateString(self.date, weekday=False)
        
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
                    if inscrit.getInscription(self.date):
                        line = template.cloneNode(1)
                        ReplaceTextFields(line, [('prenom', inscrit.prenom),
                                                 ('papa', GetPrenomNom(inscrit.papa, maj_nom=True)),
                                                 ('maman', GetPrenomNom(inscrit.maman, maj_nom=True)),
                                                 ('commentaire', None)])
                        phoneCell = line.getElementsByTagName('table:table-cell')[2]
                        phoneTemplate = phoneCell.getElementsByTagName('text:p')[0]
                        phones = []
                        for phoneType in ["domicile", "portable", "travail"]:
                            telephone_papa = getattr(inscrit.papa, "telephone_"+phoneType)
                            telephone_maman = getattr(inscrit.maman, "telephone_"+phoneType)
                            if telephone_papa and telephone_maman == telephone_papa:
                                phones.append((telephone_papa, phoneType))
                            else:
                                if telephone_maman:
                                    phones.append((telephone_maman, "%s %s" % (phoneType, GetInitialesPrenom(inscrit.maman))))
                                if telephone_papa:
                                    phones.append((telephone_papa, "%s %s" % (phoneType, GetInitialesPrenom(inscrit.papa))))
                        for phone, remark in phones:
                            phoneLine = phoneTemplate.cloneNode(1)
                            ReplaceTextFields(phoneLine, [('telephone', phone),
                                                          ('remarque', remark)])
                            phoneCell.insertBefore(phoneLine, phoneTemplate)
                        phoneCell.removeChild(phoneTemplate)
                        emailCell = line.getElementsByTagName('table:table-cell')[3]
                        emailTemplate = emailCell.getElementsByTagName('text:p')[0]
                        for email in (inscrit.maman.email, inscrit.papa.email):
                            emailLine = emailTemplate.cloneNode(1)
                            ReplaceTextFields(emailLine, [('email', email)])
                            emailCell.insertBefore(emailLine, emailTemplate)
                        emailCell.removeChild(emailTemplate)
                        table.insertBefore(line, template)
                table.removeChild(template)

            if table.getAttribute('table:name') == 'Employes':
                template = table.getElementsByTagName('table:table-row')[0]
                #print template.toprettyxml()
                for employe in creche.employes:
                    if 1: # TODO
                        line = template.cloneNode(1)
                        ReplaceTextFields(line, [('prenom', employe.prenom),
                                                 ('nom', employe.nom),
                                                 ('domicile', employe.telephone_domicile),
                                                 ('portable', employe.telephone_portable)])
                        table.insertBefore(line, template)
                table.removeChild(template)

        return None


