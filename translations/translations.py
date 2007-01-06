#!/usr/bin/env python

import pickle
import sys
sys.path.insert(1, '..')
from newcommon import *

def LoadFile(filename):
    f = file(filename, 'r')
    creche = pickle.load(f)
    inscrits = pickle.load(f)
    f.close()
    return creche, inscrits

def Translate(old_creche, old_inscrits):
    parents = {}
    for old_inscrit in old_inscrits:
        inscrit = Inscrit()
        inscrit.prenom, inscrit.nom, inscrit.naissance, inscrit.adresse, inscrit.code_postal, inscrit.ville, inscrit.marche = old_inscrit.prenom, old_inscrit.nom, old_inscrit.naissance, old_inscrit.adresse, old_inscrit.code_postal, old_inscrit.ville, old_inscrit.marche
        inscrit.inscriptions[0].delete()
        del inscrit.inscriptions[0]
        for old_inscription in old_inscrit.inscriptions:
            inscription = Inscription(inscrit)
            inscrit.inscriptions.append(inscription)
            inscription.debut, inscription.fin, inscription.mode, inscription.periode_reference = old_inscription.periode.debut, old_inscription.periode.fin, old_inscription.mode, old_inscription.semaine_type
        for parent, old_parent in [(inscrit.papa, old_inscrit.papa), (inscrit.maman, old_inscrit.maman)]:
            parent.prenom, parent.nom, parent.telephone_domicile, parent.telephone_domicile_notes, parent.telephone_portable, parent.telephone_portable_notes, parent.telephone_travail, parent.telephone_travail_notes, parent.email = old_parent.prenom, old_parent.nom, old_parent.telephone_domicile, old_parent.telephone_domicile_notes, old_parent.telephone_portable, old_parent.telephone_portable_notes, old_parent.telephone_travail, old_parent.telephone_travail_notes, old_parent.email
            index = parent.prenom + ' ' + parent.nom
            try:
                parents[str(index)] = parent
            except:
                parents[index] = parent
            parent.revenus[0].delete()
            del parent.revenus[0]
        for old_frere in old_inscrit.freres_soeurs:
            if old_frere.prenom:
                frere = Frere_Soeur(inscrit)
                frere.prenom, frere.naissance, frere.entree, frere.sortie = old_frere.prenom, old_frere.naissance, old_frere.entree_creche, old_frere.sortie_creche
        for old_revenu in old_inscrit.revenus_parents:
            revenu = Revenu(inscrit.papa)
            inscrit.papa.revenus.append(revenu)
            revenu.debut, revenu.fin, revenu.revenu, revenu.chomage, revenu.regime = old_revenu.periode.debut, old_revenu.periode.fin, old_revenu.valeur[0], old_revenu.chomage[0], old_revenu.regime
            revenu = Revenu(inscrit.maman)
            inscrit.maman.revenus.append(revenu)
            revenu.debut, revenu.fin, revenu.revenu, revenu.chomage, revenu.regime = old_revenu.periode.debut, old_revenu.periode.fin, old_revenu.valeur[1], old_revenu.chomage[1], old_revenu.regime
        for date in old_inscrit.presences:
            old_presence = old_inscrit.presences[date]
            presence = Presence(inscrit, date, old_presence.previsionnel, old_presence.value)
            inscrit.presences[date] = presence
            presence.details = old_presence.details
    
    creche = Creche()
    creche.bureaux[0].delete()
    del creche.bureaux[0]
    creche.baremes_caf[0].delete()
    del creche.baremes_caf[0]
    creche.nom, creche.adresse, creche.code_postal, creche.ville = old_creche.nom, old_creche.adresse, old_creche.code_postal, old_creche.ville
    for old_bureau in old_creche.bureaux:
        bureau = Bureau()
        try:
            tmp = u'%s' % old_bureau.vice_president
        except:
            old_bureau.vice_president = old_bureau.vice_president.decode('latin-1')
        try:
            tmp = u'%s' % old_bureau.secretaire
        except:
            old_bureau.secretaire = old_bureau.secretaire.decode('latin-1')
        bureau.debut, bureau.fin, bureau.president, bureau.vice_president, bureau.tresorier, bureau.secretaire = old_bureau.periode.debut, old_bureau.periode.fin, parents[old_bureau.president], parents[old_bureau.vice_president], parents[old_bureau.tresorier], parents[old_bureau.secretaire]
    for old_bareme in old_creche.baremes_caf:
        bareme = BaremeCAF()
        bareme.debut, bareme.fin, bareme.plancher, bareme.plafond = old_bareme.periode.debut, old_bareme.periode.fin, old_bareme.plancher, old_bareme.plafond
        
    connection.close()

    
if __name__ == '__main__':
    old_creche, old_inscrits = LoadFile('../current/petits-potes_2005.gtu')
    Translate(old_creche, old_inscrits)
    print 'End'

