# -*- coding: utf-8 -*-
import sys
import time
import math
import json
import os

from PyQt5.QtWidgets import QApplication, QWidget, QStackedWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPixmap, QColor, QIcon
from PyQt5 import uic

from objets import Plateau, COULEURS

WIDTH = 1200
HEIGHT = 800
UI_HEIGHT = 120
FPS = 120

# ── BASE DE DONNÉES ───────────────────────────────────────────────────────────
def get_all_profiles():
    if not os.path.exists("data_game.json"):
        return {}
    with open("data_game.json", "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def charger_profil(pseudo):
    data = get_all_profiles()
    return data.get(pseudo, {"victoires": 0})

def enregistrer_victoire(pseudo):
    data = get_all_profiles()
    if pseudo not in data:
        data[pseudo] = {"victoires": 0}
    data[pseudo]["victoires"] += 1
    with open("data_game.json", "w") as f:
        json.dump(data, f, indent=4)


# ── MENU D'ACCUEIL ────────────────────────────────────────────────────────────
class MenuAccueil(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        uic.loadUi('menu.ui', self)

        dossier = os.path.dirname(os.path.abspath(__file__))
        self.fond = QPixmap(os.path.join(dossier, "fond_menu.png"))

        self.setAutoFillBackground(False)
        self.btn_jouer.clicked.connect(self.lancer_jeu)
        self.maj_affichage_profils()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.fond.isNull():
            painter.drawPixmap(0, 0, self.width(), self.height(), self.fond)
        else:
            painter.fillRect(self.rect(), QColor(20, 20, 35))
        painter.end()
        super().paintEvent(event)

    def maj_affichage_profils(self):
        profils = get_all_profiles()
        if not profils:
            self.label_profils.setText("Aucun joueur n'a encore combattu.")
        else:
            texte = "🏆 MEILLEURS JOUEURS 🏆\n"
            profils_tries = sorted(profils.items(), key=lambda item: item[1].get('victoires', 0), reverse=True)
            for pseudo, stats in profils_tries[:5]:
                # On n'affiche plus que les victoires
                texte += f"• {pseudo} : {stats.get('victoires', 0)} victoire(s)\n"
            self.label_profils.setText(texte.strip())

    def lancer_jeu(self):
        nom1 = self.input_j1.text().strip() or "Joueur 1"
        nom2 = self.input_j2.text().strip() or "Joueur 2"
        self.main_app.demarrer_partie(nom1, nom2)


# ── FENÊTRE DE JEU ────────────────────────────────────────────────────────────
class FenetreJeu(QWidget):
    def __init__(self, main_app, nom_j1, nom_j2):
        super().__init__()
        self.main_app = main_app
        self.nom_j1 = nom_j1
        self.nom_j2 = nom_j2
        self.setFixedSize(WIDTH, HEIGHT)
        self.setMouseTracking(True)

        self.fond_personnalise = QPixmap("fond_jeu.jpg")
        
        self.profil_j1 = charger_profil(self.nom_j1)
        self.profil_j2 = charger_profil(self.nom_j2)

        self._reset()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000 // FPS)

    def _reset(self):
        # On ne passe plus les niveaux au Plateau
        self.plateau = Plateau(
            WIDTH, HEIGHT, UI_HEIGHT,
            self.nom_j1, self.nom_j2,
            parent=self
        )
        self.simulating = False
        self.aiming = True
        self.game_over = False
        self.start_time = time.time()
        self.mouse_x = WIDTH // 2
        self.mouse_y = HEIGHT // 2

    def _tick(self):
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
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), COULEURS['background'])

        self.plateau.dessiner_plateau(painter, self.fond_personnalise)
        self.plateau.dessiner_balles(painter)

        if self.aiming and not self.simulating and not self.game_over:
            my = min(self.mouse_y, HEIGHT - UI_HEIGHT - 1)
            self.plateau.dessiner_visee(painter, (self.mouse_x, my))

        bw = self.plateau.balle_blanche
        dx, dy = bw.x - self.mouse_x, bw.y - self.mouse_y
        force = min(math.sqrt(dx*dx + dy*dy) / 15, 20) if (self.aiming and not self.game_over) else 0
        self.plateau.dessiner_barre_visee(painter, force)

        if self.game_over:
            winner = self.plateau.verifier_vainqueur()
            if winner:
                self.plateau.afficher_vainqueur(painter, winner)
        painter.end()

    def mouseMoveEvent(self, event):
        self.mouse_x, self.mouse_y = event.x(), event.y()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.game_over and not self.simulating and self.aiming:
            my = min(event.y(), HEIGHT - UI_HEIGHT - 1)
            self.plateau.jouer_coup_souris(event.x(), my)
            self.simulating = True
            self.aiming = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self.profil_j1 = charger_profil(self.nom_j1)
            self.profil_j2 = charger_profil(self.nom_j2)
            self._reset()
        elif event.key() == Qt.Key_Escape:
            self.timer.stop()
            self.main_app.retour_menu()


# ── GESTIONNAIRE PRINCIPAL ────────────────────────────────────────────────────
class ApplicationPrincipale(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BounceBox")
        self.setFixedSize(WIDTH, HEIGHT)
        self.setStyleSheet("QStackedWidget { background: transparent; }")
        
        # Ajout d'une icône pour la fenêtre si tu as un fichier logo.ico
        self.setWindowIcon(QIcon("logo.ico"))

        self.menu = MenuAccueil(self)
        self.addWidget(self.menu)

    def demarrer_partie(self, nom1, nom2):
        self.jeu = FenetreJeu(self, nom1, nom2)
        self.addWidget(self.jeu)
        self.setCurrentWidget(self.jeu)

    def retour_menu(self):
        self.setCurrentWidget(self.menu)
        self.menu.maj_affichage_profils()
        if hasattr(self, 'jeu'):
            self.removeWidget(self.jeu)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre_globale = ApplicationPrincipale()
    fenetre_globale.show()
    sys.exit(app.exec_())