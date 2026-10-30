"""Génération des fichiers mensuels destinés au comptable (Excel et CSV)."""

import csv
import io
from datetime import datetime, timedelta

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.services.mois import ENTETES_RECAP, format_nombre_fr, libelle_mois, lignes_recap
from app.utils import format_date_fr

_ENTETE_FONT = Font(bold=True, color='FFFFFF')
_ENTETE_FILL = PatternFill('solid', fgColor='2E7D32')
_WEEKEND_FILL = PatternFill('solid', fgColor='EEEEEE')
_FORMAT_NOMBRE = '0.00'


def _jours(debut, fin):
    return [debut + timedelta(days=n) for n in range((fin - debut).days + 1)]


def _feuille(wb, titre, sous_titre, entetes, premiere=False):
    ws = wb.active if premiere else wb.create_sheet()
    ws.title = titre
    ws.append([sous_titre])
    ws['A1'].font = Font(bold=True, size=14)
    ws.append([f'Généré le {datetime.now().strftime("%d/%m/%Y à %H:%M")}'])
    ws['A2'].font = Font(italic=True, color='666666')
    ws.append([])
    ws.append(entetes)
    for cellule in ws[4]:
        cellule.font = _ENTETE_FONT
        cellule.fill = _ENTETE_FILL
        cellule.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.freeze_panes = 'C5'
    return ws


def _largeurs(ws, largeurs):
    for index, largeur in enumerate(largeurs, start=1):
        ws.column_dimensions[get_column_letter(index)].width = largeur


def generer_excel(debut, fin, lignes):
    titre = f'État préparatoire — {libelle_mois(debut)}'
    wb = Workbook()

    ws = _feuille(wb, 'Récapitulatif', titre, ENTETES_RECAP, premiere=True)
    for valeurs in lignes_recap(debut, fin, lignes):
        ws.append(valeurs)
        for colonne in (3, 4, 6):
            cellule = ws.cell(row=ws.max_row, column=colonne)
            if isinstance(cellule.value, float):
                cellule.number_format = _FORMAT_NOMBRE
        for colonne in (5, 7):
            ws.cell(row=ws.max_row, column=colonne).alignment = Alignment(wrap_text=True, vertical='top')
    _largeurs(ws, [18, 14, 16, 14, 60, 16, 26])

    ws = _feuille(wb, 'Absences', titre, ['Nom', 'Prénom', "Jour d'absence", 'Jour de reprise', 'Motif', 'Commentaire'])
    for ligne in lignes:
        for absence in ligne['absences']:
            ws.append([
                ligne['employe'].nom.upper(),
                ligne['employe'].prenom,
                absence.date_debut,
                absence.date_reprise or 'en cours',
                absence.motif.libelle,
                absence.commentaire,
            ])
            for colonne in (3, 4):
                cellule = ws.cell(row=ws.max_row, column=colonne)
                if not isinstance(cellule.value, str):
                    cellule.number_format = 'DD/MM/YYYY'
    _largeurs(ws, [18, 14, 16, 16, 22, 40])

    jours = _jours(debut, fin)
    ws = _feuille(wb, 'Heures en plus', titre, ['Nom', 'Prénom'] + [j.day for j in jours] + ['Total'])
    for index, jour in enumerate(jours, start=3):
        if jour.weekday() == 6:
            ws.cell(row=4, column=index).fill = PatternFill('solid', fgColor='757575')
    for ligne in lignes:
        valeurs = [ligne['heures'].get(jour) for jour in jours]
        ws.append([ligne['employe'].nom.upper(), ligne['employe'].prenom] + valeurs + [ligne['total_heures']])
        for index, jour in enumerate(jours, start=3):
            cellule = ws.cell(row=ws.max_row, column=index)
            if jour.weekday() == 6:
                cellule.fill = _WEEKEND_FILL
        ws.cell(row=ws.max_row, column=len(jours) + 3).font = Font(bold=True)
    _largeurs(ws, [18, 14] + [5] * len(jours) + [8])

    ws = _feuille(wb, 'Déplacements', titre, ['Nom', 'Prénom', 'Date', 'Départ', 'Arrivée', 'Motif', 'Km'])
    for ligne in lignes:
        for deplacement in ligne['deplacements_valides']:
            ws.append([
                ligne['employe'].nom.upper(),
                ligne['employe'].prenom,
                deplacement.date,
                deplacement.depart,
                deplacement.arrivee,
                deplacement.motif,
                float(deplacement.km),
            ])
            ws.cell(row=ws.max_row, column=3).number_format = 'DD/MM/YYYY'
    _largeurs(ws, [18, 14, 12, 24, 24, 40, 8])

    flux = io.BytesIO()
    wb.save(flux)
    return flux.getvalue()


def _csv(entetes, lignes):
    flux = io.StringIO()
    writer = csv.writer(flux, delimiter=';', lineterminator='\r\n')
    writer.writerow(entetes)
    writer.writerows(lignes)
    # BOM UTF-8 : indispensable pour qu'Excel (FR) ouvre correctement les accents.
    return ('\ufeff' + flux.getvalue()).encode('utf-8')


def _cellule_csv(valeur):
    if valeur is None:
        return ''
    if isinstance(valeur, float):
        return format_nombre_fr(valeur)
    return valeur


def generer_csv_recap(debut, fin, lignes):
    return _csv(ENTETES_RECAP, [[_cellule_csv(v) for v in valeurs] for valeurs in lignes_recap(debut, fin, lignes)])


def generer_csv_heures(debut, fin, lignes):
    resultat = []
    for ligne in lignes:
        for jour, valeur in sorted(ligne['heures'].items()):
            resultat.append([ligne['employe'].nom.upper(), ligne['employe'].prenom, format_date_fr(jour), format_nombre_fr(valeur)])
    return _csv(['Nom', 'Prénom', 'Date', 'Heures en plus'], resultat)
