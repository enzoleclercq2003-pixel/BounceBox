# -*- coding: utf-8 -*-
"""
Module graphique du jeu BounceBox.
Sépare la logique de rendu visuel (QPainter) et d'interface graphique (QtDesigner)
de la logique physique métier contenue dans objets.py.
"""
import math
import os
import time

from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, QTimer, QUrl
from PyQt5.QtGui import (QPainter, QPixmap, QColor, QPen, QBrush,
                         QFont, QRadialGradient)
from PyQt5 import uic

from database import get_all_profiles, charger_profil, enregistrer_victoire
from objets import Plateau

COULEURS = {
    'background': QColor(20, 20, 35),
    'table':      QColor(34, 85, 50),
    'border':     QColor(80, 50, 20),
    'white':      QColor(245, 245, 245),
    'grey':       QColor(160, 160, 160),
    'red':        QColor(220, 60, 60),
    'blue':       QColor(60, 130, 220),
    'ui_bg':      QColor(15, 15, 28),
    'text':       QColor(220, 220, 200),
}


# ── Fonctions de dessin du plateau ────────────────────────────────────────────

def draw_balle(painter, balle):
    """Dessine une balle individuelle avec un effet de gradient radial pour le relief."""
    if not balle.est_active:
        return
    couleur = COULEURS.get(balle.couleur, COULEURS['grey'])
    grad = QRadialGradient(balle.x - 3, balle.y - 3, balle.rayon * 1.2)
    grad.setColorAt(0.0, couleur.lighter(160))
    grad.setColorAt(1.0, couleur.darker(130))
    painter.setPen(QPen(couleur.darker(150), 1))
    painter.setBrush(QBrush(grad))
    painter.drawEllipse(int(balle.x - balle.rayon), int(balle.y - balle.rayon),
                        balle.rayon * 2, balle.rayon * 2)

def dessiner_plateau(painter, plateau, image_fond=None):
    """Peint le fond de la table (image ou couleur unie) et les bordures massives."""
    if image_fond and not image_fond.isNull():
        painter.drawPixmap(0, 0, plateau.largeur, plateau.hauteur_jeu, image_fond)
        painter.setPen(QPen(COULEURS['border'], 12))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(0, 0, plateau.largeur, plateau.hauteur_jeu)
    else:
        painter.setPen(QPen(COULEURS['border'], 12))
        painter.setBrush(QBrush(COULEURS['table']))
        painter.drawRoundedRect(0, 0, plateau.largeur, plateau.hauteur_jeu, 8, 8)

def dessiner_balles(painter, plateau):
    """Itère sur toutes les balles du plateau pour les dessiner."""
    for b in plateau.balles:
        draw_balle(painter, b)

def dessiner_visee(painter, plateau, pos_souris):
    """Déclenche le dessin de la ligne prédictive partant de la balle blanche."""
    plateau.balle_blanche.barre_visee(painter, *pos_souris, COULEURS,
                                      largeur=plateau.largeur,
                                      hauteur_jeu=plateau.hauteur_jeu)

def dessiner_barre_visee(painter, plateau, force):
    """
    Dessine l'IHM inférieure (HUD) : jauge de puissance dynamique, 
    pseudos des joueurs, tour actif et score géant central.
    """
    y0 = plateau.hauteur_jeu

    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(COULEURS['ui_bg']))
    painter.drawRect(0, y0, plateau.largeur, plateau.hauteur_barre_info)

    # Zone gauche : tour + jauge puissance
    painter.setFont(QFont("Arial", 14, QFont.Bold))
    col_j = COULEURS['red'] if plateau.joueur_actif == 'red' else COULEURS['blue']
    painter.setPen(col_j)
    painter.drawText(15, y0 + 35, f"Tour : {plateau.pseudos[plateau.joueur_actif].upper()}")

    painter.setFont(QFont("Arial", 10, QFont.Bold))
    painter.setPen(COULEURS['text'])
    painter.drawText(30, y0 + 65, "PUISSANCE")

    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(QColor(60, 60, 80)))
    painter.drawRoundedRect(30, y0 + 75, 200, 15, 4, 4)
    remplissage = int((force / 20) * 200)
    if remplissage > 0:
        painter.setBrush(QBrush(QColor(80, 200, 80)))
        painter.drawRoundedRect(30, y0 + 75, remplissage, 15, 4, 4)

    # Zone centre : pseudos + scores
    painter.setFont(QFont("Arial", 12, QFont.Bold))
    painter.setPen(COULEURS['red'])
    painter.drawText(plateau.largeur // 2 - 260, y0 + 60, plateau.pseudos['red'])
    painter.setPen(COULEURS['blue'])
    painter.drawText(plateau.largeur // 2 + 110, y0 + 60, plateau.pseudos['blue'])

    painter.setFont(QFont("Arial", 42, QFont.Bold))
    painter.setPen(COULEURS['red'])
    painter.drawText(plateau.largeur // 2 - 120, y0 + 95, str(plateau.scores['red']))
    painter.setPen(COULEURS['text'])
    painter.drawText(plateau.largeur // 2 - 20,  y0 + 95, "-")
    painter.setPen(COULEURS['blue'])
    painter.drawText(plateau.largeur // 2 + 50,  y0 + 95, str(plateau.scores['blue']))

    # Zone droite : contrôles
    painter.setFont(QFont("Arial", 8))
    painter.setPen(COULEURS['text'])
    painter.drawText(plateau.largeur - 260, y0 + 45, "[ R ] = Rejouer")
    painter.drawText(plateau.largeur - 260, y0 + 75, "[ ECHAP ] = Menu principal")

def afficher_vainqueur(painter, plateau, id_vainqueur):
    """Superpose un écran sombre de victoire à la fin de la partie."""
    painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
    painter.setPen(Qt.NoPen)
    painter.drawRect(0, 0, plateau.largeur, plateau.hauteur_totale)
    col = COULEURS[id_vainqueur]
    nom = plateau.pseudos[id_vainqueur]
    painter.setFont(QFont("Arial", 40, QFont.Bold))
    painter.setPen(col)
    painter.drawText(QRect(0, plateau.hauteur_totale // 2 - 60, plateau.largeur, 80),
                     Qt.AlignCenter, f"VICTOIRE DE {nom.upper()} !")
    painter.setFont(QFont("Arial", 18))
    painter.setPen(COULEURS['text'])
    painter.drawText(QRect(0, plateau.hauteur_totale // 2 + 30, plateau.largeur, 40),
                     Qt.AlignCenter, "Appuyez sur R pour rejouer ou ECHAP pour le menu")


# ── MenuAccueil ───────────────────────────────────────────────────────────────

class MenuAccueil(QWidget):
    """
    Vue statique de l'interface chargée depuis le fichier XML généré par QtDesigner.
    Gère la saisie des pseudos et l'affichage du classement (JSON).
    """
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        uic.loadUi('menu.ui', self)

        dossier = os.path.dirname(os.path.abspath(__file__))
        self.fond = QPixmap(os.path.join(dossier, "fond_menu.png"))

        self.setAutoFillBackground(False)
        self.btn_jouer.clicked.connect(self.lancer_jeu)
        self.maj_affichage_profils()

        self.son_lobby = QSoundEffect()
        self.son_lobby.setSource(QUrl.fromLocalFile("lobby.wav"))
        self.son_lobby.setVolume(0.5)
        self.son_lobby.play()

    def paintEvent(self, event):
        """Surcharge du dessin pour intégrer l'image de fond du menu."""
        painter = QPainter(self)
        if not self.fond.isNull():
            painter.drawPixmap(0, 0, self.width(), self.height(), self.fond)
        else:
            painter.fillRect(self.rect(), QColor(20, 20, 35))
        painter.end()
        super().paintEvent(event)

    def maj_affichage_profils(self):
        """Charge le top des joueurs depuis la BDD JSON et actualise l'UI."""
        profils = get_all_profiles()
        if not profils:
            self.label_profils.setText("Aucun joueur n'a encore combattu.")
        else:
            texte = "🏆 MEILLEURS JOUEURS 🏆\n"
            profils_tries = sorted(profils.items(),
                                   key=lambda item: item[1].get('victoires', 0),
                                   reverse=True)
            for pseudo, stats in profils_tries[:5]:
                texte += f"• {pseudo} : {stats.get('victoires', 0)} victoire(s)\n"
            self.label_profils.setText(texte.strip())

    def lancer_jeu(self):
        """Récupère les entrées utilisateur et demande le changement de vue."""
        self.son_lobby.setSource(QUrl())
        nom1 = self.input_j1.text().strip() or "Joueur 1"
        nom2 = self.input_j2.text().strip() or "Joueur 2"
        self.main_app.demarrer_partie(nom1, nom2)


# ── FenetreJeu ────────────────────────────────────────────────────────────────

class FenetreJeu(QWidget):
    """
    Vue dynamique du jeu. Gère la boucle de rafraîchissement (QTimer)
    et les événements d'interaction en temps réel de l'utilisateur.
    """
    def __init__(self, main_app, nom_j1, nom_j2, width, height, ui_height, fps):
        super().__init__()
        self.main_app = main_app
        self.nom_j1 = nom_j1
        self.nom_j2 = nom_j2
        self.WIDTH = width
        self.HEIGHT = height
        self.UI_HEIGHT = ui_height
        self.FPS = fps

        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setMouseTracking(True)

        self.fond_personnalise = QPixmap("fond_jeu.jpg")
        self.profil_j1 = charger_profil(self.nom_j1)
        self.profil_j2 = charger_profil(self.nom_j2)

        self._reset()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000 // self.FPS)

        self.son_tir = QSoundEffect()
        self.son_tir.setSource(QUrl.fromLocalFile("tir.wav"))
        self.son_tir.setVolume(0.5)

    def _reset(self):
        """Réinstancie un plateau vierge (utilisé pour Nouvelle Partie)."""
        self.plateau = Plateau(self.WIDTH, self.HEIGHT, self.UI_HEIGHT,
                               self.nom_j1, self.nom_j2, parent=self)
        self.simulating = False
        self.aiming = True
        self.game_over = False
        self.start_time = time.time()
        self.mouse_x = self.WIDTH // 2
        self.mouse_y = self.HEIGHT // 2

    def _tick(self):
        """Méthode de la boucle principale appelée à chaque frame (FPS)."""
        if self.simulating:
            if not self.plateau.maj_physique():
                self.simulating = False
                self.aiming = True
                self.plateau.changer_tour()
                winner_id = self.plateau.verifier_vainqueur()
                if winner_id:
                    self.game_over = True
                    enregistrer_victoire(self.plateau.pseudos[winner_id])
        self.update()

    def paintEvent(self, event):
        """Moteur de rendu. Efface l'écran et redessine l'ensemble des éléments."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), COULEURS['background'])

        dessiner_plateau(painter, self.plateau, self.fond_personnalise)
        dessiner_balles(painter, self.plateau)

        if self.aiming and not self.simulating and not self.game_over:
            my = min(self.mouse_y, self.HEIGHT - self.UI_HEIGHT - 1)
            dessiner_visee(painter, self.plateau, (self.mouse_x, my))

        bw = self.plateau.balle_blanche
        dx, dy = bw.x - self.mouse_x, bw.y - self.mouse_y
        force = min(math.sqrt(dx*dx + dy*dy) / 15, 20) if (self.aiming and not self.game_over) else 0
        dessiner_barre_visee(painter, self.plateau, force)

        if self.game_over:
            winner = self.plateau.verifier_vainqueur()
            if winner:
                afficher_vainqueur(painter, self.plateau, winner)
        painter.end()

    def mouseMoveEvent(self, event):
        """Capte en temps réel la position du curseur pour la visée."""
        self.mouse_x, self.mouse_y = event.x(), event.y()

    def mousePressEvent(self, event):
        """Valide le tir lors d'un clic gauche et déclenche la simulation physique."""
        if event.button() == Qt.LeftButton and not self.game_over and not self.simulating and self.aiming:
            my = min(event.y(), self.HEIGHT - self.UI_HEIGHT - 1)
            self.plateau.jouer_coup_souris(event.x(), my)
            self.simulating = True
            self.son_tir.play()
            self.aiming = False

    def keyPressEvent(self, event):
        """Capte les raccourcis clavier pour rejouer (R) ou revenir au menu (ECHAP)."""
        if event.key() == Qt.Key_R:
            self.profil_j1 = charger_profil(self.nom_j1)
            self.profil_j2 = charger_profil(self.nom_j2)
            self._reset()
        elif event.key() == Qt.Key_Escape:
            self.timer.stop()
            self.main_app.retour_menu()