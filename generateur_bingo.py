#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de cartons Bingo (Loto 90) - Adultes & Enfants
---------------------------------------------------------
- Format classique : 3 lignes x 9 colonnes (modifiable ci-dessous).
- Disposition classique (15 numéros par carton, 5 numéros par ligne, colonnes par tranches).
- Unicité des cartons garantie au global (adultes + enfants).
- Sorties :
    * CSV global des cartons générés (adultes + enfants).
    * Dossiers "Adultes/" et "Enfants/" avec images des cartons (.jpg).
- Possibilité de régénérer les images à l'identique à partir d'un CSV existant.
"""

import argparse
import csv
import os
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Set

from PIL import Image, ImageDraw, ImageFont

# =====================
# ⚙️ Paramètres globaux
# =====================

# Format du carton (modifiable si besoin)
NB_LIGNES = 3 
NB_COLONNES = 9 

# Taille des cases et styles
CASE_SIZE = 1000                  # px (largeur = hauteur d'une case) 1000    
Coef = 1.5 						  # ratio Hauteur/largueur des cases
SEPARATEUR_COULEUR = "#003333"    # Couleur des séparateurs de cases "#333333"
GRILLE_FOND = "#FFFFFF"           # Couleur de fond de la grille "#FFFFFF"
TEXTE_COULEUR = "#000000"         # Couleur du texte (numéros)
MARGE_EXTERNE = 12                # épaisseur des traits de la grille (px) 8 
CASE_PADDING = MARGE_EXTERNE+20   # Marge sup pour voir la grille

# Enfants : zone image + zone texte

ENFANT_TEXTE_H = int(0.2*Coef*CASE_SIZE )             # hauteur de la zone texte (numéro)
ENFANT_IMAGE_H = int(Coef*CASE_SIZE)-ENFANT_TEXTE_H            # hauteur de la zone image (sur 1000 de haut)
# CSV
CSV_DEFAUT = "cartons.csv"

# Dossiers de sortie
DIR_ADULTES = "Adultes"
DIR_ENFANTS = "Enfants"
DIR_IMAGES_NUMEROS = "images"     # dossier contenant 0.jpg à 90.jpg (utilisés pour les numéros 1..90)

# Police (on essaie quelques polices connues, puis fallback)
POLICES_TTF = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "arial.ttf",
    "DejaVuSans-Bold.ttf",
    "DejaVuSans.ttf",
]

def charge_police(taille: int) -> ImageFont.ImageFont:
    for chemin in POLICES_TTF:
        try:
            return ImageFont.truetype(chemin, taille)
        except Exception:
            continue
    # Fallback
    return ImageFont.load_default()

# =====================
# 🧩 Modèle de données
# =====================

@dataclass(frozen=True)
class Ticket:
    """Représente un carton 3x9.
    Les cases vides sont 0. Les numéros sont 1..90. 27 cases au total.
    """
    cells: Tuple[int, ...]  # longueur = NB_LIGNES * NB_COLONNES

    def to_row_major(self) -> List[List[int]]:
        g = []
        for r in range(NB_LIGNES):
            row = list(self.cells[r * NB_COLONNES:(r + 1) * NB_COLONNES])
            g.append(row)
        return g

# =====================
# 🎲 Génération tickets
# =====================

def colonne_intervalle(col: int) -> Tuple[int, int]:
    """Intervalle [min, max] inclus pour une colonne du loto 90."""
    if col == 0:
        return 1, 9
    if col == NB_COLONNES - 1:
        return 80, 90
    start = col * 10
    return start, start + 9

def genere_compte_par_colonne() -> List[int]:
    """Retourne une distribution de nombres par colonne (somme = 15, min 1, max 3 par colonne)."""
    comptes = [1] * NB_COLONNES  # 9 déjà placés
    a_ajouter = 15 - NB_COLONNES  # 6 à répartir
    essais = 0
    while a_ajouter > 0 and essais < 1000:
        c = random.randrange(NB_COLONNES)
        if comptes[c] < 3:
            comptes[c] += 1
            a_ajouter -= 1
        essais += 1
    if sum(comptes) != 15 or any(x < 1 or x > 3 for x in comptes):
        # Sécurité : si échec improbable, recommencer
        return genere_compte_par_colonne()
    return comptes

def distribue_positions_sur_lignes(comptes_col: List[int]) -> List[List[int]]:
    """Pour chaque colonne, renvoie la/les lignes où placer les numéros (0,1,2). Garantit 5 numéros par ligne."""
    lignes_par_col = [[] for _ in range(NB_COLONNES)]
    compte_lignes = [0] * NB_LIGNES

    # Colonnes avec 3 numéros -> toutes les lignes
    for col in range(NB_COLONNES):
        if comptes_col[col] == 3:
            lignes_par_col[col] = [0, 1, 2]
            for r in range(3):
                compte_lignes[r] += 1

    # Colonnes avec 2 numéros -> deux lignes les moins chargées
    for col in range(NB_COLONNES):
        if comptes_col[col] == 2:
            lignes = sorted(range(NB_LIGNES), key=lambda r: compte_lignes[r])[:2]
            lignes_par_col[col] = sorted(lignes)
            for r in lignes:
                compte_lignes[r] += 1

    # Colonnes avec 1 numéro -> ligne la moins chargée
    for col in range(NB_COLONNES):
        if comptes_col[col] == 1:
            r = min(range(NB_LIGNES), key=lambda rr: compte_lignes[rr])
            lignes_par_col[col] = [r]
            compte_lignes[r] += 1

    # Correction si une ligne n'a pas exactement 5 (petit ajustement via échanges)
    # On essaie de déplacer des placements 1-numéro entre lignes pour atteindre 5-5-5
    def total_ok() -> bool:
        return compte_lignes == [5, 5, 5]

    essais = 0
    while not total_ok() and essais < 200:
        # Trouver une ligne trop chargée (>5) et une sous-chargée (<5)
        trop = next((i for i, v in enumerate(compte_lignes) if v > 5), None)
        pas_assez = next((i for i, v in enumerate(compte_lignes) if v < 5), None)
        if trop is None or pas_assez is None:
            break
        # Chercher une colonne où la ligne 'trop' possède un placement unique déplaçable
        deplace = False
        for col in range(NB_COLONNES):
            lp = lignes_par_col[col]
            if len(lp) == 1 and lp[0] == trop:
                lignes_par_col[col] = [pas_assez]
                compte_lignes[trop] -= 1
                compte_lignes[pas_assez] += 1
                deplace = True
                break
        if not deplace:
            # essayer une colonne avec 2 numéros: permuter une des deux lignes si possible
            for col in range(NB_COLONNES):
                lp = lignes_par_col[col]
                if len(lp) == 2 and trop in lp and pas_assez not in lp:
                    # remplacer 'trop' par 'pas_assez'
                    lp.remove(trop)
                    lp.append(pas_assez)
                    lp.sort()
                    compte_lignes[trop] -= 1
                    compte_lignes[pas_assez] += 1
                    deplace = True
                    break
        essais += 1

    if compte_lignes != [5, 5, 5]:
        # En cas d'échec rare, recommencer la distribution entière
        return distribue_positions_sur_lignes(comptes_col)

    return lignes_par_col

def genere_ticket_random() -> Ticket:
    """Génère un ticket conforme aux règles usuelles (3x9, 15 numéros, colonnes par tranches)."""
    comptes_col = genere_compte_par_colonne()

    # Tirer les numéros par colonne
    numeros_col = []
    for col in range(NB_COLONNES):
        lo, hi = colonne_intervalle(col)
        count = comptes_col[col]
        nums = sorted(random.sample(range(lo, hi + 1), count))
        numeros_col.append(nums)

    # Répartir sur les lignes
    lignes_par_col = distribue_positions_sur_lignes(comptes_col)

    # Construire la grille vide
    grid = [[0 for _ in range(NB_COLONNES)] for _ in range(NB_LIGNES)]

    # Pour chaque colonne, placer les numéros triés du haut vers le bas
    for col in range(NB_COLONNES):
        rows = lignes_par_col[col]
        nums = numeros_col[col]
        # Associer par ordre croissant aux lignes du haut vers le bas
        rows_sorted = sorted(rows)
        for i, r in enumerate(rows_sorted):
            grid[r][col] = nums[i]

    # Vérifier 5 numéros par ligne
    for r in range(NB_LIGNES):
        if sum(1 for v in grid[r] if v != 0) != 5:
            # Recommencer si non conforme
            return genere_ticket_random()

    # Aplatir
    cells = tuple(v for r in range(NB_LIGNES) for v in grid[r])
    return Ticket(cells=cells)

# =====================
# 🔁 Unicité globale
# =====================

def ticket_signature(t: Ticket) -> Tuple[int, ...]:
    """Signature canonique d'un ticket (les 27 valeurs)."""
    return t.cells

def genere_tickets_uniques(n_total: int, max_essais: int = 100000) -> List[Ticket]:
    """Génère n_total tickets uniques globalement."""
    uniques: Set[Tuple[int, ...]] = set()
    tickets: List[Ticket] = []
    essais = 0
    while len(tickets) < n_total and essais < max_essais:
        t = genere_ticket_random()
        sig = ticket_signature(t)
        if sig not in uniques:
            uniques.add(sig)
            tickets.append(t)
        essais += 1
    if len(tickets) < n_total:
        raise RuntimeError("Impossible de générer le nombre demandé de tickets uniques (essayez un autre seed).")
    return tickets

# =====================
# 🖼️ Rendu des images
# =====================

def dessine_grille_base(draw: ImageDraw.ImageDraw, W: int, H: int):
    # Traits extérieurs
    draw.rectangle([0, 0, W - 1, H - 1], outline=SEPARATEUR_COULEUR, width=MARGE_EXTERNE)
    # Lignes horizontales
    for r in range(1, NB_LIGNES):
        y = r * CASE_SIZE*Coef
        draw.line([(0, y), (W, y)], fill=SEPARATEUR_COULEUR, width=MARGE_EXTERNE)
    # Lignes verticales
    for c in range(1, NB_COLONNES):
        x = c * CASE_SIZE
        draw.line([(x, 0), (x, H)], fill=SEPARATEUR_COULEUR, width=MARGE_EXTERNE)

def centre_texte(draw: ImageDraw.ImageDraw, bbox: Tuple[int, int, int, int], texte: str, police: ImageFont.ImageFont, couleur: str):
    x0, y0, x1, y1 = bbox
    w = x1 - x0
    h = y1 - y0
    #tw, th = draw.textsize(texte, font=police)
    bbox = draw.textbbox((0, 0), texte, font=police)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    xx = x0 + (w - tw) // 2
    yy = y0 + (h - th) // 2
    draw.text((xx, yy), texte, fill=couleur, font=police)

def rend_ticket_adulte(ticket: Ticket, sortie: str):
    W, H = NB_COLONNES * CASE_SIZE, int(NB_LIGNES * CASE_SIZE*Coef)
    img = Image.new("RGB", (W, H), GRILLE_FOND)
    draw = ImageDraw.Draw(img)

    # Grille
    dessine_grille_base(draw, W, H)

    # Police adaptée à la taille de case
    police = charge_police(int(CASE_SIZE * 0.5))

    # Numéros
    grid = ticket.to_row_major()
    for r in range(NB_LIGNES):
        for c in range(NB_COLONNES):
            v = grid[r][c]
            x0 = c * CASE_SIZE
            y0 = r * int(CASE_SIZE*Coef)
            x1 = x0 + CASE_SIZE
            y1 = y0 + int(CASE_SIZE*Coef)
            if v != 0:
                centre_texte(draw, (x0, y0, x1, y1), str(v), police, TEXTE_COULEUR)

    img.save(sortie, "JPEG", quality=95)

def rend_ticket_enfant(ticket: Ticket, sortie: str, dossier_images: str):
    W, H = NB_COLONNES * CASE_SIZE, int(NB_LIGNES * int(CASE_SIZE *Coef))
    img = Image.new("RGB", (W, H), GRILLE_FOND)
    draw = ImageDraw.Draw(img)

    # Grille
    dessine_grille_base(draw, W, H)

    # Police pour le numéro sous l'image
    police = charge_police(int(CASE_SIZE * 0.2))

    grid = ticket.to_row_major()
    for r in range(NB_LIGNES):
        for c in range(NB_COLONNES):
            v = grid[r][c]
            x0 = c * int(CASE_SIZE) + CASE_PADDING
            y0 = r * int(Coef*CASE_SIZE) + CASE_PADDING
            x1 = (c + 1) * CASE_SIZE - CASE_PADDING
            y1 = (r + 1) * int(CASE_SIZE*Coef) - CASE_PADDING

            if v == 0:
                # case vide
                continue

            # Charger l'image associée au numéro (v.jpg)
            chemin = os.path.join(dossier_images, f"{v}.jpg")
            if not os.path.isfile(chemin):
                # Tenter 0.jpg comme fallback si fourni, sinon remplir blanc
                alt = os.path.join(dossier_images, "0.jpg")
                if os.path.isfile(alt):
                    chemin = alt
                else:
                    # zone blanche si image manquante
                    pass

            # Zone image (haut)
            zone_img = (x0 , y0, x1, y0 + ENFANT_IMAGE_H)
            # Zone texte (bas)
            zone_txt = (x0, y0 + ENFANT_IMAGE_H, x1, y1)

            # Placer l'image en respectant le cadre 1000x800
            try:
                im = Image.open(chemin).convert("RGB")
                print("Largeur %i, hauteur %i",(im.width,im.height))
                # Ajuster en conservant le ratio, centrée dans 1000x800
                target_w = CASE_SIZE- 2 * CASE_PADDING
                target_h = ENFANT_IMAGE_H
                print("Largeur %i, hauteur %i",(target_w,target_h))
                im.thumbnail((target_w, target_h), Image.LANCZOS)
                # Calcul pour centrer
                print("Largeur %i, hauteur %i",(im.width,im.height))
                pad_x = (target_w - im.width) // 2
                pad_y = (target_h - im.height) // 2
                img.paste(im, (x0 + pad_x, y0 + pad_y))
            except Exception:
                # Si échec de chargement, laisser blanc
                pass

            # Écrire le numéro sous l'image (centré)
            centre_texte(draw, zone_txt, str(v), police, TEXTE_COULEUR)

    img.save(sortie, "JPEG", quality=95)

# =====================
# 📄 CSV I/O
# =====================

def ecrit_csv(path: str, rows: List[Tuple[str, str, Ticket]]):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    header = ["id", "type"] + [f"cell_{i+1}" for i in range(NB_LIGNES * NB_COLONNES)]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for id_, typ, ticket in rows:
            w.writerow([id_, typ] + list(ticket.cells))

def lit_csv(path: str) -> List[Tuple[str, str, Ticket]]:
    out = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            id_ = row["id"]
            typ = row["type"]
            cells = []
            for i in range(NB_LIGNES * NB_COLONNES):
                v = int(row[f"cell_{i+1}"])
                cells.append(v)
            out.append((id_, typ, Ticket(tuple(cells))))
    return out

# =====================
# 🧪 Utilitaires
# =====================

def formate_id(prefix: str, idx: int, width: int = 5) -> str:
    return f"{prefix}{idx:0{width}d}"

# =====================
# 🚀 Main
# =====================

def main():
    parser = argparse.ArgumentParser(description="Générateur de cartons Bingo (Loto 90) adultes & enfants.")
    parser.add_argument("--adultes", type=int, default=0, help="Nombre de cartons adultes à générer.")
    parser.add_argument("--enfants", type=int, default=0, help="Nombre de cartons enfants à générer.")
    parser.add_argument("--seed", type=int, default=None, help="Seed aléatoire pour reproductibilité.")
    parser.add_argument("--csv", type=str, default=CSV_DEFAUT, help="Chemin du CSV de sortie (ou d'entrée pour --regen-from).")
    parser.add_argument("--images", type=str, default=DIR_IMAGES_NUMEROS, help="Dossier des images numérotées (enfants).")
    parser.add_argument("--regen-from", type=str, default=None, help="Régénère les images à partir d'un CSV existant (ignore --adultes/--enfants).")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Mode régénération depuis CSV
    if args.regen_from:
        rows = lit_csv(args.regen_from)
        # Créer dossiers
        os.makedirs(DIR_ADULTES, exist_ok=True)
        os.makedirs(DIR_ENFANTS, exist_ok=True)

        for id_, typ, ticket in rows:
            if typ == "adulte":
                sortie = os.path.join(DIR_ADULTES, f"{id_}.jpg")
                rend_ticket_adulte(ticket, sortie)
            elif typ == "enfant":
                sortie = os.path.join(DIR_ENFANTS, f"{id_}.jpg")
                rend_ticket_enfant(ticket, sortie, args.images)
        print(f"Régénération terminée depuis {args.regen_from}.")
        return

    n_adultes = max(0, int(args.adultes))
    n_enfants = max(0, int(args.enfants))
    n_total = n_adultes + n_enfants

    if n_total <= 0:
        print("Aucun carton demandé. Utilisez --adultes N et/ou --enfants N.")
        return

    # Générer tickets uniques globaux
    tickets = genere_tickets_uniques(n_total)

    # Assigner types et IDs
    rows_csv: List[Tuple[str, str, Ticket]] = []
    os.makedirs(DIR_ADULTES, exist_ok=True)
    os.makedirs(DIR_ENFANTS, exist_ok=True)

    # Adultes d'abord
    for i in range(n_adultes):
        t = tickets[i]
        id_ = formate_id("A", i + 1)
        rows_csv.append((id_, "adulte", t))
        sortie = os.path.join(DIR_ADULTES, f"{id_}.jpg")
        rend_ticket_adulte(t, sortie)

    # Enfants ensuite
    for j in range(n_enfants):
        t = tickets[n_adultes + j]
        id_ = formate_id("E", j + 1)
        rows_csv.append((id_, "enfant", t))
        sortie = os.path.join(DIR_ENFANTS, f"{id_}.jpg")
        rend_ticket_enfant(t, sortie, args.images)

    # Écrire CSV global
    ecrit_csv(args.csv, rows_csv)

    print(f"Génération terminée : {n_adultes} adultes, {n_enfants} enfants.")
    print(f"- CSV : {args.csv}")
    print(f"- Dossiers : {DIR_ADULTES}/ et {DIR_ENFANTS}/")
    print("Astuce : utilisez --regen-from CSV pour régénérer les images plus tard.")
    

if __name__ == "__main__":
    main()
