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

from facture import *
from document_dialog import *
from controls import *
from database import Site, Creche, NumeroFacture, Correction
from generation.facture_mensuelle import FactureModifications
from generation.export_compta import ExportComptaCotisationsModifications, ExportComptaReglementsModifications
from generation.attestation_paiement import AttestationModifications
from generation.appel_cotisations import AppelCotisationsModifications
from generation.export_sepa import ExportSepaModifications


class CorrectionsTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        # la selection du mois et le numéro de facture
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.monthchoice = wx.Choice(self)
        AddMonthsToChoice(self.monthchoice)
        self.Bind(wx.EVT_CHOICE, self.OnMonthChoice, self.monthchoice)
        sizer.Add(self.monthchoice, 1, wx.EXPAND, 5)
        self.numfacture = AutoNumericCtrl(self, None, 'valeur', precision=0)
        sizer.AddMany([(wx.StaticText(self, -1, 'Premier numéro de facture :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (self.numfacture, 0, wx.ALIGN_CENTER_VERTICAL)])
        self.sizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.corrections_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.corrections_sizer, 0, wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.UpdateContents()
        self.Layout()
        
    def OnMonthChoice(self, evt=None):
        if sys.platform == 'win32':
            self.Hide()
        while len(self.corrections_sizer.GetChildren()):
            sizer = self.corrections_sizer.GetItem(0)
            sizer.DeleteWindows()
            self.corrections_sizer.Detach(0)
            
        date = self.monthchoice.GetClientData(self.monthchoice.GetSelection())
        if date not in database.creche.numeros_facture:
            database.creche.numeros_facture[date] = NumeroFacture()
        self.numfacture.SetInstance(database.creche.numeros_facture[date])
        
        if database.creche.tri_planning == TRI_PRENOM:
            inscrits = GetEnfantsTriesParPrenom()
        else:
            inscrits = GetEnfantsTriesParNom()

        for inscrit in inscrits:
            if inscrit.has_facture(date):  # TODO and date not in inscrit.clotures:
                if date not in inscrit.corrections:
                    inscrit.corrections[date] = Correction(inscrit=inscrit, date=date)
                sizer = wx.BoxSizer(wx.HORIZONTAL)
                sizer.Add(wx.StaticText(self, -1, GetPrenomNom(inscrit), size=(200, -1)), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 15)
                sizer.AddMany([(wx.StaticText(self, -1, 'Libellé :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, inscrit.corrections[date], 'libelle')])
                sizer.AddMany([(wx.StaticText(self, -1, 'Valeur :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoNumericCtrl(self, inscrit.corrections[date], 'valeur', precision=2)])
                self.corrections_sizer.Add(sizer)
        
        AutoTab.UpdateContents(self)
        self.sizer.FitInside(self)
        if sys.platform == 'win32':
            self.Show()

    def UpdateContents(self):
        self.OnMonthChoice()


class FacturationTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.inscrits_choice = {}
        
        # Les appels de cotisations
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Edition des appels de cotisation'), wx.HORIZONTAL)
        self.appels_monthchoice = wx.Choice(self)
        AddMonthsToChoice(self.appels_monthchoice)
        button = wx.Button(self, -1, 'Génération')
        self.Bind(wx.EVT_BUTTON, self.OnGenerationAppelCotisations, button)
        box_sizer.AddMany([(self.appels_monthchoice, 1, wx.ALL|wx.EXPAND, 5), (button, 0, wx.ALL, 5)])
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)

        # Les factures
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Clôture et édition des factures'), wx.HORIZONTAL)
        self.inscrits_choice["factures"] = wx.Choice(self)
        self.factures_monthchoice = wx.Choice(self)
        self.Bind(wx.EVT_CHOICE, self.OnFacturesInscritChoice, self.inscrits_choice["factures"])
        self.Bind(wx.EVT_CHOICE, self.OnFacturesMonthChoice, self.factures_monthchoice)
        self.cloture_button = wx.Button(self, -1, 'Clôture')
        self.Bind(wx.EVT_BUTTON, self.OnClotureFacture, self.cloture_button)
        generation_button = wx.Button(self, -1, 'Génération')
        self.Bind(wx.EVT_BUTTON, self.OnGenerationFacture, generation_button)        
        box_sizer.AddMany([(self.inscrits_choice["factures"], 1, wx.ALL|wx.EXPAND, 5), (self.factures_monthchoice, 1, wx.ALL|wx.EXPAND, 5), (self.cloture_button, 0, wx.ALL, 5), (generation_button, 0, wx.ALL, 5)])
        if config.options & PRELEVEMENTS_AUTOMATIQUES:
            sepa_button = wx.Button(self, -1, 'Virements SEPA')
            self.Bind(wx.EVT_BUTTON, self.OnExportSepa, sepa_button)
            box_sizer.Add(sepa_button, 0, wx.ALL, 5)
        if IsTemplateFile("Export compta cotisations.txt"):
            exportButton = wx.Button(self, -1, 'Export compta cotisations')
            self.Bind(wx.EVT_BUTTON, self.OnExportComptaCotisations, exportButton)
            box_sizer.Add(exportButton, 0, wx.ALL, 5)
        if IsTemplateFile("Export compta reglements.txt"):
            exportButton = wx.Button(self, -1, 'Export compta règlements')
            self.Bind(wx.EVT_BUTTON, self.OnExportComptaReglements, exportButton)
            box_sizer.Add(exportButton, 0, wx.ALL, 5)
        if config.options & DECLOTURE:
            self.decloture_button = wx.Button(self, -1, 'Dé-clôture')
            self.Bind(wx.EVT_BUTTON, self.OnDeclotureFacture, self.decloture_button)
            box_sizer.Add(self.decloture_button, 0, wx.ALL, 5)
        sizer.Add(box_sizer, 0, wx.EXPAND | wx.BOTTOM, 10)

        # Les attestations de paiement
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Edition des attestations de paiement'), wx.HORIZONTAL)
        self.inscrits_choice["attestations"] = wx.Choice(self)
        self.attestations_periodechoice = wx.Choice(self)
        self.attestations_endchoice = wx.Choice(self)
        self.attestations_endchoice.Disable()
        self.Bind(wx.EVT_CHOICE, self.OnAttestationsInscritChoice, self.inscrits_choice["attestations"])
        self.Bind(wx.EVT_CHOICE, self.OnAttestationsPeriodeChoice, self.attestations_periodechoice)
        button = wx.Button(self, -1, 'Génération')
        self.Bind(wx.EVT_BUTTON, self.OnGenerationAttestation, button)
        box_sizer.AddMany([(self.inscrits_choice["attestations"], 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5),
                           (self.attestations_periodechoice, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)])
        box_sizer.AddMany([(wx.StaticText(self, -1, '-'), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5),
                           (self.attestations_endchoice, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)])
        box_sizer.AddMany([(button, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)])
        sizer.Add(box_sizer, 0, wx.EXPAND | wx.BOTTOM, 10)

        # Les attestations de paiement mensuelles
        if IsTemplateFile("Attestation mensuelle.odt"):
            box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Edition des attestations de paiement mensuelles'), wx.HORIZONTAL)
            self.inscrits_choice["attestations-mensuelles"] = wx.Choice(self)
            self.attestations_mensuelles_periodechoice = wx.Choice(self)
            self.Bind(wx.EVT_CHOICE, self.OnAttestationsMensuellesInscritChoice, self.inscrits_choice["attestations-mensuelles"])
            button = wx.Button(self, -1, 'Génération')
            self.Bind(wx.EVT_BUTTON, self.OnGenerationAttestationMensuelle, button)
            box_sizer.AddMany([(self.inscrits_choice["attestations-mensuelles"], 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5),
                               (self.attestations_mensuelles_periodechoice, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)])
            box_sizer.AddMany([(button, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)])
            sizer.Add(box_sizer, 0, wx.EXPAND | wx.BOTTOM, 10)

        self.SetSizer(sizer)
        self.UpdateContents()
        self.Layout()

    def OnFacturesInscritChoice(self, _):
        self.factures_monthchoice.Clear()
        who = self.inscrits_choice["factures"].GetClientData(self.inscrits_choice["factures"].GetSelection())
        for date in who.get_factures_list():
            self.factures_monthchoice.Append('%s %d' % (months[date.month - 1], date.year), date)
        self.factures_monthchoice.SetSelection(self.factures_monthchoice.GetCount()-1)
        self.OnFacturesMonthChoice()
        
    def OnFacturesMonthChoice(self, _=None):
        inscrits, periode = self.__GetFactureSelection()
        for inscrit in inscrits:
            if inscrit.has_facture(periode) and periode not in inscrit.clotures and (database.creche.temps_facturation != FACTURATION_FIN_MOIS or GetMonthEnd(periode) not in inscrit.clotures):
                self.cloture_button.Enable()
                break
        else:
            self.cloture_button.Disable()

    def OnAttestationsInscritChoice(self, evt):
        self.attestations_periodechoice.Clear()
        inscrit = self.inscrits_choice["attestations"].GetClientData(self.inscrits_choice["attestations"].GetSelection())
        if isinstance(inscrit, Inscrit):
            for year in range(today.year-10, today.year):
                if inscrit.get_inscriptions(datetime.date(year, 1, 1), datetime.date(year, 12, 31)):
                    self.attestations_periodechoice.Append(u"Année %d" % year, (datetime.date(year, 1, 1), datetime.date(year, 12, 31)))
            for year in range(today.year-10, today.year):
                if inscrit.get_inscriptions(datetime.date(year - 1, 12, 1), datetime.date(year, 11, 30)):
                    self.attestations_periodechoice.Append(u"Décembre %d - Novembre %d" % (year - 1, year), (datetime.date(year - 1, 12, 1), datetime.date(year, 11, 30)))
            if inscrit.get_inscriptions(datetime.date(today.year, 1, 1), GetMonthEnd(today)):
                debut = 1
                while not inscrit.get_inscriptions(datetime.date(today.year, debut, 1), GetMonthEnd(datetime.date(today.year, debut, 1))) and debut < today.month:
                    debut += 1
                if debut == today.month:
                    self.attestations_periodechoice.Append("%s %d" % (months[debut - 1], today.year), (datetime.date(today.year, debut, 1), GetMonthEnd(datetime.date(today.year, debut, 1))))
                else:
                    self.attestations_periodechoice.Append(u"%s - %s %d" % (months[debut - 1], months[today.month-1], today.year), (datetime.date(today.year, debut, 1), datetime.date(today.year, today.month, 1)))
        else:
            for year in range(today.year - 3, today.year):
                self.attestations_periodechoice.Append(u"Année %d" % year, (datetime.date(year, 1, 1), datetime.date(year, 12, 31)))
            for year in range(today.year - 3, today.year):
                self.attestations_periodechoice.Append(u"Décembre %d - Novembre %d" % (year - 1, year), (datetime.date(year - 1, 12, 1), datetime.date(year, 11, 30)))
            if today.month == 1:
                self.attestations_periodechoice.Append("Janvier %d" % today.year, (datetime.date(today.year, 1, 1), datetime.date(today.year, 1, 31)))
            else:
                self.attestations_periodechoice.Append(u"Janvier - %s %d" % (months[today.month - 1], today.year), (datetime.date(today.year, 1, 1), datetime.date(today.year, today.month, 1)))
        
        date = config.get_first_monday()
        while date < today:
            if not isinstance(inscrit, Inscrit) or inscrit.get_inscriptions(datetime.date(date.year, date.month, 1), GetMonthEnd(date)):
                self.attestations_periodechoice.Append('%s %d' % (months[date.month - 1], date.year), (datetime.date(date.year, date.month, 1), GetMonthEnd(date)))
            date = GetNextMonthStart(date)
        self.attestations_periodechoice.SetSelection(0)
        self.OnAttestationsPeriodeChoice(evt)

    def OnAttestationsPeriodeChoice(self, _):
        inscrit = self.inscrits_choice["attestations"].GetClientData(self.inscrits_choice["attestations"].GetSelection())
        periode = self.attestations_periodechoice.GetClientData(self.attestations_periodechoice.GetSelection())
        self.attestations_endchoice.Clear()
        if periode:
            debut, fin = periode
            if debut.month == fin.month and debut < today:
                date = debut
                while date < today:
                    if not isinstance(inscrit, Inscrit) or inscrit.get_inscriptions(datetime.date(date.year, date.month, 1), GetMonthEnd(date)):
                        self.attestations_endchoice.Append('%s %d' % (months[date.month - 1], date.year), (datetime.date(date.year, date.month, 1), GetMonthEnd(date)))
                    date = GetNextMonthStart(date)
                self.attestations_endchoice.Enable()
                self.attestations_endchoice.SetSelection(0)
            else:
                self.attestations_endchoice.Disable()

    def OnAttestationsMensuellesInscritChoice(self, _):
        if "attestations-mensuelles" in self.inscrits_choice:
            self.attestations_mensuelles_periodechoice.Clear()
            inscrit = self.inscrits_choice["attestations-mensuelles"].GetClientData(self.inscrits_choice["attestations-mensuelles"].GetSelection())
            date = config.get_first_monday()
            while date < today:
                if not isinstance(inscrit, Inscrit) or inscrit.get_inscriptions(datetime.date(date.year, date.month, 1), GetMonthEnd(date)):
                    self.attestations_mensuelles_periodechoice.Append('%s %d' % (months[date.month - 1], date.year), (datetime.date(date.year, date.month, 1), GetMonthEnd(date)))
                date = GetNextMonthStart(date)
            self.attestations_mensuelles_periodechoice.SetSelection(0)

    def UpdateContents(self):
        for choice in self.inscrits_choice.values():
            choice.Clear()
            choice.Append("Tous les enfants", database.creche)
            if len(database.creche.sites) > 1:
                for site in database.creche.sites:
                    choice.Append("Enfants du site %s" % site.get_name(), site)

        inscrits = {}
        autres = {}
        for inscrit in database.creche.inscrits:
            if inscrit.get_inscription(datetime.date.today()) is not None:
                inscrits[GetPrenomNom(inscrit)] = inscrit
            else:
                autres[GetPrenomNom(inscrit)] = inscrit
        
        keys = list(inscrits.keys())
        keys.sort()
        for key in keys:
            for choice in self.inscrits_choice.values():
                choice.Append(key, inscrits[key])
        
        if len(inscrits) > 0 and len(autres) > 0:
            for choice in self.inscrits_choice.values():
                choice.Append(20 * '-', None)
        
        keys = list(autres.keys())
        keys.sort()
        for key in keys:
            for choice in self.inscrits_choice.values():
                choice.Append(key, autres[key])
            
        for choice in self.inscrits_choice.values():
            choice.SetSelection(0)
        
        self.cloture_button.Show(database.creche.cloture_facturation)

        self.OnFacturesInscritChoice(None)
        self.OnAttestationsInscritChoice(None)
        self.OnAttestationsMensuellesInscritChoice(None)

        self.Layout()

    def OnGenerationAppelCotisations(self, _):
        periode = self.appels_monthchoice.GetClientData(self.appels_monthchoice.GetSelection())
        DocumentDialog(self, AppelCotisationsModifications(periode, options=NO_NOM)).ShowModal()

    def __GetSelection(self, periode, data):
        if isinstance(data, Creche):
            inscrits = [inscrit for inscrit in database.creche.inscrits if inscrit.has_facture(periode)]
        elif isinstance(data, Site):
            inscrits = [inscrit for inscrit in database.creche.select_inscrits(GetMonthStart(periode), GetMonthEnd(periode), site=data) if inscrit.has_facture(periode)]
        else:
            inscrits = [data]
        return inscrits, periode
        
    def __GetFactureSelection(self):
        periode = self.factures_monthchoice.GetClientData(self.factures_monthchoice.GetSelection())
        data = self.inscrits_choice["factures"].GetClientData(self.inscrits_choice["factures"].GetSelection())
        if isinstance(data, Creche):
            inscrits = [inscrit for inscrit in database.creche.inscrits if inscrit.has_facture(periode)]
        elif isinstance(data, Site):
            inscrits = [inscrit for inscrit in database.creche.select_inscrits(GetMonthStart(periode), GetMonthEnd(periode), site=data) if inscrit.has_facture(periode)]
        else:
            inscrits = [data]
        return inscrits, periode

    def show_cloture_errors(self, message, errors):
        message += " :\n"
        for label in errors.keys():
            message += '\n' + label + ' :\n  '
            message += '\n  '.join(errors[label])
        wx.MessageDialog(self, message, 'Message', wx.OK | wx.ICON_WARNING).ShowModal()

    def OnClotureFacture(self, _):
        inscrits, periode = self.__GetFactureSelection()
        errors = ClotureFactures(inscrits, periode, True)
        if errors:
            self.show_cloture_errors("Erreurs lors de la clôture", errors)
        self.OnFacturesMonthChoice()

    def OnDeclotureFacture(self, _):
        inscrits, periode = self.__GetFactureSelection()
        errors = ClotureFactures(inscrits, periode, False)
        if errors:
            self.show_cloture_errors("Erreurs lors de la dé-clôture", errors)
        self.OnFacturesMonthChoice()

    def OnGenerationFacture(self, _):
        inscrits, periode = self.__GetFactureSelection()
        if len(inscrits) > 0:
            DocumentDialog(self, FactureModifications(inscrits, periode)).ShowModal()
        else:
            wx.MessageDialog(self, 'Aucune facture pour cette période', 'Message', wx.OK | wx.ICON_WARNING).ShowModal()

    def OnGenerationAttestation(self, _):
        inscrits = self.inscrits_choice["attestations"].GetClientData(self.inscrits_choice["attestations"].GetSelection())
        debut, fin = self.attestations_periodechoice.GetClientData(self.attestations_periodechoice.GetSelection())
        if self.attestations_endchoice.IsEnabled():
            fin = self.attestations_endchoice.GetClientData(self.attestations_endchoice.GetSelection())[1]
        DocumentDialog(self, AttestationModifications(inscrits, debut, fin, attestation_mensuelle=False)).ShowModal()
        
    def OnGenerationAttestationMensuelle(self, _):
        inscrits = self.inscrits_choice["attestations-mensuelles"].GetClientData(self.inscrits_choice["attestations-mensuelles"].GetSelection())
        debut, fin = self.attestations_mensuelles_periodechoice.GetClientData(self.attestations_mensuelles_periodechoice.GetSelection())
        DocumentDialog(self, AttestationModifications(inscrits, debut, fin, attestation_mensuelle=True)).ShowModal()

    def OnExportComptaCotisations(self, _):
        inscrits, periode = self.__GetFactureSelection()
        if len(inscrits) > 0:
            DocumentDialog(self, ExportComptaCotisationsModifications(inscrits, periode)).ShowModal()

    def OnExportComptaReglements(self, _):
        inscrits, periode = self.__GetFactureSelection()
        if len(inscrits) > 0:
            DocumentDialog(self, ExportComptaReglementsModifications(inscrits, periode)).ShowModal()

    def OnExportSepa(self, _):
        inscrits, periode = self.__GetFactureSelection()
        if len(inscrits) > 0:
            DocumentDialog(self, ExportSepaModifications(inscrits, periode)).ShowModal()


class ReglementsTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.inscrit = None
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.choice = wx.Choice(self)
        self.Bind(wx.EVT_CHOICE, self.OnInscritChoice, self.choice)
        self.sizer.Add(self.choice, 0, wx.ALL|wx.EXPAND, 5)
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(0, 4)
        self.grid.EnableEditing(False)
        self.grid.SetRowLabelSize(50)
        self.grid.SetColLabelValue(0, "Date")
        self.grid.SetColLabelValue(1, "Type")
        self.grid.SetColLabelValue(2, "Montant")
        self.grid.SetColLabelValue(3, "Total")
        self.grid.SetColSize(0, 200)
        self.grid.SetColSize(1, 200)
        self.grid.SetColSize(2, 200)
        self.grid.SetColSize(3, 200)
        self.sizer.Add(self.grid, -1, wx.EXPAND|wx.ALL, 5)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnClickDroitLabel, self.grid)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_date = DateCtrl(self)
        self.add_montant = NumericCtrl(self, precision=2)
        self.add_moyen_paiement = ChoiceCtrl(self, items=ModeEncaissementItems)  
        sizer.AddMany([(wx.StaticText(self, -1, 'Date :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), self.add_date])
        sizer.AddMany([(wx.StaticText(self, -1, 'Montant :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), self.add_montant])
        sizer.AddMany([(wx.StaticText(self, -1, 'Moyen de paiement :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), self.add_moyen_paiement])
        global addbmp
        addbmp = wx.Bitmap(GetBitmapFile("plus.png"), wx.BITMAP_TYPE_PNG)
        self.add_button = wx.BitmapButton(self, -1, addbmp)
        sizer.Add(self.add_button, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutReglement, self.add_button)
        self.sizer.Add(sizer, 0, wx.EXPAND+wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.UpdateContents()

    def UpdateContents(self):
        AddInscritsToChoice(self.choice)
        if len(database.creche.inscrits) > 0 and self.inscrit is not None and self.inscrit in database.creche.inscrits:
            SelectValueInChoice(self.choice, self.inscrit)
            self.AfficheLignes()
        else:
            self.Disable()            
        self.sizer.Layout()
        AutoTab.UpdateContents(self)

    def AjouteLigne(self, ligne):
        index = self.grid.GetNumberRows()
        self.grid.AppendRows(1)
        self.grid.SetCellAlignment(index, 2, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
        self.grid.SetCellAlignment(index, 3, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
        if isinstance(ligne, EncaissementFamille):
            moyen = ligne.moyen_paiement if isinstance(ligne.moyen_paiement, str) else ModesEncaissement[ligne.moyen_paiement] if ligne.moyen_paiement is not None else ""
            valeur = ligne.valeur
            self.index += 1
            self.grid.SetRowLabelValue(index, str(self.index))
        else:
            moyen = "Facture %s" % ligne.inscrit.prenom
            valeur = -ligne.total_facture
            self.grid.SetRowLabelValue(index, "")
        if isinstance(valeur, float):
            self.total += valeur
            self.grid.SetCellValue(index, 2, "%.02f €" % valeur)
        else:
            self.grid.SetCellValue(index, 2, valeur)
        self.grid.SetCellValue(index, 0, date2str(ligne.date))
        self.grid.SetCellValue(index, 1, moyen)
        self.grid.SetCellValue(index, 3, "%.02f €" % self.total)
            
    def Disable(self):
        self.EffaceLignes()
        self.EnableLigneAjout(False)
    
    def EnableLigneAjout(self, enable=True):        
        self.add_date.Enable(enable)
        self.add_montant.Enable(enable)
        self.add_moyen_paiement.Enable(enable)
        self.add_button.Enable(enable)
        
    def EffaceLignes(self):
        if self.grid.GetNumberRows() > 0:
            self.grid.DeleteRows(0, self.grid.GetNumberRows())

    def AfficheLignes(self):
        self.EnableLigneAjout()
        self.EffaceLignes()
        self.lignes = GetHistoriqueSolde(self.inscrit.famille, today)
        self.lignes.sort(key=lambda ligne: ligne.date if ligne.date else today)
        self.index = 0
        self.total = 0
        for ligne in self.lignes:
            self.AjouteLigne(ligne)
            
    def OnInscritChoice(self, event):
        selected = self.choice.GetSelection()
        self.inscrit = self.choice.GetClientData(selected)
        if self.inscrit:
            self.AfficheLignes()
        else:
            self.Disable()
            
    def OnClickDroitLabel(self, event):
        line = self.lignes[event.GetRow()]
        if isinstance(line, EncaissementFamille):
            self.current_line = line
            menu = wx.Menu()
            menu.Append(0, "Supprimer")
            wx.EVT_MENU(menu, 0, self.OnSuppressionReglement)
            self.grid.PopupMenu(menu, event.GetPosition())
            menu.Destroy()
    
    def OnAjoutReglement(self, _):
        if self.add_date.GetValue() <= today:
            history.Append(Delete(self.inscrit.famille.encaissements, -1))
            self.inscrit.famille.encaissements.append(EncaissementFamille(famille=self.inscrit.famille, date=self.add_date.GetValue(), valeur=self.add_montant.GetValue(), moyen_paiement=self.add_moyen_paiement.GetValue()))
            self.AfficheLignes()
        else:
            dlg = wx.MessageDialog(None, "Date erronée", 'Erreur', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

    def OnSuppressionReglement(self, _):
        history.Append(None)
        self.inscrit.famille.encaissements.remove(self.current_line)
        self.AfficheLignes()


class FacturationNotebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT)
        self.AddPage(FacturationTab(self), "Edition")
        self.AddPage(CorrectionsTab(self), "Corrections")
        self.AddPage(ReglementsTab(self), "Règlements")
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def UpdateContents(self):
        self.OnPageChanged(None)

    def OnPageChanged(self, evt):
        self.GetCurrentPage().UpdateContents()
        if evt:
            evt.Skip()


class FacturationPanel(GPanel):
    name = "Facturation"
    bitmap = GetBitmapFile("facturation.png")
    profil = PROFIL_FACTURATION

    def __init__(self, parent):
        GPanel.__init__(self, parent, 'Facturation')
        self.notebook = FacturationNotebook(self)
        self.sizer.Add(self.notebook, 1, wx.EXPAND)

    def UpdateContents(self):
        self.notebook.UpdateContents()

