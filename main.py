# -*- coding: utf-8 -*-
import sys

from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtWidgets import QApplication, QStackedWidget
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QIcon

from graphisme import MenuAccueil, FenetreJeu

# ── Constantes ────────────────────────────────────────────────────────────────

WIDTH = 2850
HEIGHT = 1700
UI_HEIGHT = 120
FPS = 120


# ── Application principale ────────────────────────────────────────────────────

class ApplicationPrincipale(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BounceBox")
        self.setFixedSize(WIDTH, HEIGHT)
        self.setStyleSheet("QStackedWidget { background: transparent; }")
        self.setWindowIcon(QIcon("logo.ico"))

        self.son_lobby = QSoundEffect()
        self.son_lobby.setSource(QUrl.fromLocalFile("lobby.wav"))
        self.son_lobby.setVolume(0.5)

        self.menu = MenuAccueil(self)
        self.addWidget(self.menu)

    def demarrer_partie(self, nom1, nom2):
        self.jeu = FenetreJeu(self, nom1, nom2, WIDTH, HEIGHT, UI_HEIGHT, FPS)
        self.addWidget(self.jeu)
        self.setCurrentWidget(self.jeu)
        self.son_lobby.stop()

    def retour_menu(self):
        self.setCurrentWidget(self.menu)
        self.menu.maj_affichage_profils()
        if hasattr(self, 'jeu'):
            self.removeWidget(self.jeu)
        self.son_lobby = QSoundEffect()
        self.son_lobby.setSource(QUrl.fromLocalFile("lobby.wav"))
        self.son_lobby.setVolume(0.5)
        self.son_lobby.play()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre_globale = ApplicationPrincipale()
    fenetre_globale.show()
    sys.exit(app.exec_())
