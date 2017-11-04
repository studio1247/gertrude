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

from constants import *
from globals import *
import datetime
from functions import GetPrenomNom
from facture import GetRetardDePaiement
from config import config
from helpers import GetDateIntersection, GetDateMinus


def GetAlertes(fresh_only=False):
    alertes = []

    def add_alerte(date, message):
        ack = message in database.creche.alertes
        if not fresh_only or not ack:
            alertes.append((date, message, ack))

    today = datetime.date.today()
    for inscription in database.creche.select_inscriptions(today, today):
        inscrit = inscription.inscrit
        if (database.creche.masque_alertes & ALERTE_3MOIS_AVANT_AGE_MAXIMUM) and inscrit.naissance:
            date = GetDateMinus(inscrit.naissance, years=-database.creche.age_maximum, months=3)
            if today > date:
                message = "%s %s aura %d ans dans 3 mois" % (inscrit.prenom, inscrit.nom, database.creche.age_maximum)
                add_alerte(date, message)
        if (database.creche.masque_alertes & ALERTE_1AN_APRES_INSCRIPTION) and inscription.debut:
            date = datetime.date(inscription.debut.year+1, inscription.debut.month, inscription.debut.day)
            if today > date:
                message = "L'inscription de %s %s passe un an aujourd'hui" % (inscrit.prenom, inscrit.nom)
                add_alerte(date, message)
        if (database.creche.masque_alertes & ALERTE_2MOIS_AVANT_FIN_INSCRIPTION) and inscription.fin:
            date = GetDateMinus(inscription.fin, years=0, months=2)
            if today > date:
                message = "L'inscription de %s %s se terminera dans 2 mois" % (inscrit.prenom, inscrit.nom)
                add_alerte(date, message)
        if config.options & ALERTES_NON_PAIEMENT:
            # On ne calcule les retards de paiement que si la clôture est activée, sinon surcharge appli !
            if GetRetardDePaiement(inscrit.famille):
                add_alerte(today, "Le solde de %s est négatif depuis plus de 30 jours" % GetPrenomNom(inscrit))

    for inscrit in database.creche.inscrits:
        for inscription in inscrit.inscriptions:
            if inscription.debut and inscription.fin and inscription.fin < inscription.debut:
                add_alerte(inscription.debut, "Période incorrecte pour %s %s" % (inscrit.prenom, inscrit.nom))
        date = GetDateIntersection(inscrit.inscriptions)
        if date:
            add_alerte(date, "%s %s a 2 contrats actifs à la même date" % (inscrit.prenom, inscrit.nom))

    for salarie in database.creche.salaries:
        for contrat in salarie.contrats:
            if contrat.debut and contrat.fin and contrat.fin < contrat.debut:
                add_alerte(contrat.debut, "Période incorrecte pour %s %s" % (salarie.prenom, salarie.nom))
        date = GetDateIntersection(salarie.contrats)
        if date:
            add_alerte(date, "%s %s a 2 contrats actifs à la même date" % (salarie.prenom, salarie.nom))

    if config.options & ALERTES_NON_PAIEMENT:
        for reservataire in creche.reservataires:
            if GetRetardDePaiement(reservataire):
                add_alerte(today, "Le solde de %s est négatif depuis plus de %d jours" % (reservataire.nom, reservataire.delai_paiement if reservataire.delai_paiement else 0))

    alertes.sort(key=lambda alerte: alerte[0], reverse=True)
    return alertes

