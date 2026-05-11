# -*- coding: utf-8 -*-
import sys
import time
import math
import datetime

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter

from objets import Plateau, COULEURS

WIDTH, HEIGHT = 1600, 1400
FPS = 120
UI_HEIGHT = 120


def save_game_stats(winner, scores, duration):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open("game_history.csv", "a") as f:
        f.write(f"{date_str};{winner};{scores['red']};{scores['blue']};{duration:.2f}\n")


class fenetreJeu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BounceBox")
        self.setFixedSize(WIDTH, HEIGHT)
        self.setMouseTracking(True)
        self._reset()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000 // FPS)

    def _reset(self):
        self.plateau = Plateau(WIDTH, HEIGHT, UI_HEIGHT)
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
                winner = self.plateau.verifier_vainqueur()
                if winner:
                    self.game_over = True
                    save_game_stats(winner, self.plateau.scores, time.time() - self.start_time)
        self.update()

    # Les méthodes ci-dessous (paintEvent, etc.) gardent leur notation camelCase 
    # car elles appartiennent à la bibliothèque PyQt5 et sont écrasées (override) ici.
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), COULEURS['background'])

        self.plateau.dessiner_plateau(painter)
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
            self._reset()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = fenetreJeu() # Corrigé ici aussi
    win.show()
    sys.exit(app.exec_())
    
