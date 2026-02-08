PROJET BINGO / LOTO 90 – ADULTES & ENFANTS
=======================================

Ce projet contient un générateur de cartons de Bingo (Loto 90) ainsi qu’un outil de tirage visuel et sonore.
Il est conçu pour être utilisé aussi bien avec des adultes qu’avec de jeunes enfants, grâce à l’utilisation
d’images associées aux numéros.

--------------------------------------------------
STRUCTURE DU DEPOT
--------------------------------------------------

projet-bingo/
|
|-- README_PROJET_BINGO.txt    : Documentation
|-- generateur_bingo.py        : Générateur de cartons
|-- cartons_A800_E300.csv      : contient une génération de 800 cartons Adultes et 300 Enfants
|
|-- cartons/
|   |-- Adultes/               : Cartons adultes générés (images)
|   |-- Enfants/               : Cartons enfants générés (images)
|
|-- Tirage_Loto_V2.py          : Outil de tirage visuel et sonore
|-- images/                    : Images associées aux numéros
|   |-- 00.jpg                 : Image par défaut
|   |-- 01.jpg                 : Image du chiffre 1
|   |-- ...
|   |-- 90.jpg                 : Image du nombre 90
|
|-- tirage.mp3                 : Son joué lors du tirage

--------------------------------------------------
1. GENERATEUR DE CARTONS
--------------------------------------------------

Le script "generateur_bingo.py" permet de générer des cartons de Bingo / Loto 90.

Fonctionnalités principales :
- Génération de cartons au format classique 3 lignes x 9 colonnes
- 15 numéros par carton
- Cartons uniques (pas de doublons)
- Deux types de cartons :
  - Adultes : numéros uniquement
  - Enfants : image + numéro
- Export des cartons sous forme d’images JPG
- Génération d’un fichier CSV récapitulatif
- Possibilité de régénérer les cartons à l’identique depuis un CSV existant

--------------------------------------------------
UTILISATION DU GENERATEUR
--------------------------------------------------

Exemple de commande :

python generateur_bingo.py --adultes 50 --enfants 50

Cette commande génère :
- 50 cartons adultes
- 50 cartons enfants
- Un fichier CSV contenant la composition de tous les cartons

--------------------------------------------------
REGENERATION DES CARTONS
--------------------------------------------------

Il est possible de régénérer les cartons à l’identique à partir d’un fichier CSV existant,
par exemple si les images ont changé :

python generateur_bingo.py --regen-from cartons.csv

--------------------------------------------------
2. DOSSIER IMAGES
--------------------------------------------------

Le dossier "images" doit contenir une image JPG par numéro.

Format attendu :
- Nommage : 0.jpg à 90.jpg
- Format : JPG (.jpg)

Exemple :
images/
0.jpg
1.jpg
2.jpg
...
90.jpg

Contraintes et recommandations :
- Résolution recommandée : minimum 800 x 600 pixels
- Images simples, lisibles et adaptées à de jeunes enfants
- Fond clair recommandé
- L’image "0.jpg" est utilisée comme image par défaut si une image est manquante ou au démarrage du tirage (logo de l'asso ou évenement)

--------------------------------------------------
3. OUTIL DE TIRAGE
--------------------------------------------------

Le script "Tirage_Loto_V2.py" permet d’effectuer le tirage des numéros.

Fonctionnalités :
- Tirage aléatoire sans répétition
- Affichage du numéro tiré et de son image
- Historique des derniers numéros
- Affichage de l’ensemble des numéros sortis
- Tirage automatique avec intervalle réglable
- Lecture d’un son à chaque tirage

--------------------------------------------------
SON DU TIRAGE
--------------------------------------------------

Un son est joué à chaque tirage.
Le fichier audio doit s’appeler :

tirage.mp3

Ce fichier doit être placé à la racine du projet, si il est abscent il n'y aura pas de son.

La lecture du son utilise la bibliothèque pygame.

--------------------------------------------------
DEPENDANCES
--------------------------------------------------

Version de Python recommandée :
- Python 3.10 ou supérieur

Bibliothèques nécessaires :
- Tkinter (inclus par défaut avec Python)
- Pillow
- pygame

Installation des dépendances :

pip install pillow pygame

--------------------------------------------------
INFORMATIONS COMPLEMENTAIRES
--------------------------------------------------

- Les cartons adultes et enfants utilisent le même jeu de numéros (adultes et enfants jouent ensemble avec les mêmes numéros tirés)
- Aucun numéro n’est tiré deux fois
- Les cartons Adultes et Enfants sont indépendant (pas de doublons dans la génération)
- Le projet est adapté à un usage :
  - scolaire
  - associatif
  - familial

--------------------------------------------------
Bon jeu et bonne animation !
--------------------------------------------------
