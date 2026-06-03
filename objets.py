# -*- coding: utf-8 -*-
import math
import random
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import (QColor, QPen, QBrush, QFont,
                         QRadialGradient)

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


class Balle:
    RAYON = 30
    FRICTION = 0.988
    SEUIL_ARRET = 0.08
    def __init__(self, couleur, x, y):
        self.couleur = couleur
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.rayon = Balle.RAYON
        self.est_active = True

    def norme_vitesse(self):
        return math.sqrt(self.vx ** 2 + self.vy ** 2)

    def maj_position(self, largeur, hauteur):
        self.x += self.vx
        self.y += self.vy
        self.vx *= self.FRICTION
        self.vy *= self.FRICTION
        r = self.rayon

        if self.x - r <= 0:
            self.x, self.vx = r, abs(self.vx)
        elif self.x + r >= largeur:
            self.x, self.vx = largeur - r, -abs(self.vx)
        if self.y - r <= 0:
            self.y, self.vy = r, abs(self.vy)
        elif self.y + r >= hauteur:
            self.y, self.vy = hauteur - r, -abs(self.vy)

        if self.norme_vitesse() < self.SEUIL_ARRET:
            self.vx = self.vy = 0.0

    def verifier_collision(self, other):
        dx, dy = other.x - self.x, other.y - self.y
        return math.sqrt(dx*dx + dy*dy) < (self.rayon + other.rayon)

    def gerer_collision(self, other):
        dx, dy = other.x - self.x, other.y - self.y
        dist = math.sqrt(dx*dx + dy*dy) or 0.01
        nx, ny = dx / dist, dy / dist

        superposition = (self.rayon + other.rayon - dist) / 2
        self.x -= nx * superposition
        self.y -= ny * superposition
        other.x += nx * superposition
        other.y += ny * superposition

        v1n = self.vx * nx + self.vy * ny
        v2n = other.vx * nx + other.vy * ny
        self.vx  += (v2n - v1n) * nx
        self.vy  += (v2n - v1n) * ny
        other.vx += (v1n - v2n) * nx
        other.vy += (v1n - v2n) * ny

    def draw(self, painter):
        if not self.est_active:
            return
        couleur = COULEURS.get(self.couleur, COULEURS['grey'])
        grad = QRadialGradient(self.x - 3, self.y - 3, self.rayon * 1.2)
        grad.setColorAt(0.0, couleur.lighter(160))
        grad.setColorAt(1.0, couleur.darker(130))
        painter.setPen(QPen(couleur.darker(150), 1))
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(int(self.x - self.rayon), int(self.y - self.rayon),
                            self.rayon * 2, self.rayon * 2)


class BalleBlanche(Balle):
    def __init__(self, x, y):
        super().__init__('white', x, y)

    def barre_visee(self, painter, mx, my):
        dx, dy = self.x - mx, self.y - my
        dist = math.sqrt(dx*dx + dy*dy) or 1
        force = min(dist / 15, 20)
        angle = math.atan2(dy, dx)
        fx = self.x + math.cos(angle) * force * 10
        fy = self.y + math.sin(angle) * force * 10
        pen = QPen(QColor(255, 255, 200, 180), 2)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(int(self.x), int(self.y), int(fx), int(fy))



class Plateau:
    def __init__(self, largeur, hauteur, hauteur_barre_info, pseudo_j1, pseudo_j2, parent=None):
        self.largeur = largeur
        self.hauteur_jeu = hauteur - hauteur_barre_info
        self.hauteur_totale = hauteur
        self.hauteur_barre_info = hauteur_barre_info
        self.parent = parent
        
        self.pseudos = {'red': pseudo_j1, 'blue': pseudo_j2}
        self.scores = {'red': 0, 'blue': 0}
        self.joueur_actif = 'red'
        self.balles = []
        self._initialiser()

    def _initialiser(self):
        self.balle_blanche = BalleBlanche(self.largeur // 2, self.hauteur_jeu // 2)
        self.balles = [self.balle_blanche]
        for couleur in ['grey'] * 9 + ['blue'] * 2:
            self.balles.append(Balle(
                couleur,
                random.randint(100, self.largeur - 100),
                random.randint(100, self.hauteur_jeu - 100)
            ))

    # ── Logique de jeu ────────────────────────────────────────────────────────

    def jouer_coup_souris(self, mx, my):
        dx, dy = self.balle_blanche.x - mx, self.balle_blanche.y - my
        dist = math.sqrt(dx**2 + dy**2)
        force = min(dist / 15, 25)
        angle = math.atan2(dy, dx)
        self.balle_blanche.vx = math.cos(angle) * force
        self.balle_blanche.vy = math.sin(angle) * force

    def _appliquer_regles(self, balle_touchee):
        adversaire = 'blue' if self.joueur_actif == 'red' else 'red'
        if balle_touchee.couleur == 'grey':
            balle_touchee.couleur = self.joueur_actif
        elif balle_touchee.couleur == self.joueur_actif:
            balle_touchee.est_active = False
            self.scores[self.joueur_actif] += 1
        elif balle_touchee.couleur == adversaire:
            balle_touchee.couleur = 'grey'

    def maj_physique(self):
        for b in self.balles:
            if b.est_active and b.norme_vitesse() > 0.05:
                b.maj_position(self.largeur, self.hauteur_jeu)

        for i, b1 in enumerate(self.balles):
            if not b1.est_active:
                continue
            for b2 in self.balles[i+1:]:
                if not b2.est_active:
                    continue
                if b1.verifier_collision(b2):
                    if b1.couleur == 'white' or b2.couleur == 'white':
                        self._appliquer_regles(b2 if b1.couleur == 'white' else b1)
                    b1.gerer_collision(b2)

        return any(b.est_active and b.norme_vitesse() > 0.05 for b in self.balles)

    def changer_tour(self):
        self.joueur_actif = 'blue' if self.joueur_actif == 'red' else 'red'
        self.balles = [b for b in self.balles if b.est_active]

    def verifier_vainqueur(self):
        if self.scores['red'] >= 5:  return "red"
        if self.scores['blue'] >= 5: return "blue"
        return None

    # ── Dessin ────────────────────────────────────────────────────────────────

    def dessiner_plateau(self, painter, image_fond=None):
        if image_fond and not image_fond.isNull():
            painter.drawPixmap(0, 0, self.largeur, self.hauteur_jeu, image_fond)
            painter.setPen(QPen(COULEURS['border'], 12))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(0, 0, self.largeur, self.hauteur_jeu)
        else:
            painter.setPen(QPen(COULEURS['border'], 12))
            painter.setBrush(QBrush(COULEURS['table']))
            painter.drawRoundedRect(0, 0, self.largeur, self.hauteur_jeu, 8, 8)

    def dessiner_balles(self, painter):
        for b in self.balles:
            b.draw(painter)

    def dessiner_visee(self, painter, pos_souris):
        self.balle_blanche.barre_visee(painter, *pos_souris)

    def dessiner_barre_visee(self, painter, force):
        y0 = self.hauteur_jeu
        
        # Fond de la barre
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(COULEURS['ui_bg']))
        painter.drawRect(0, y0, self.largeur, self.hauteur_barre_info)

        # ─── ZONE GAUCHE : Tour et Puissance ───────────────────────────────
        font_tour = QFont("Arial", 14, QFont.Bold)
        painter.setFont(font_tour)
        col_j = COULEURS['red'] if self.joueur_actif == 'red' else COULEURS['blue']
        nom_actif = self.pseudos[self.joueur_actif]
        painter.setPen(col_j)
        painter.drawText(15, y0 + 35, f"Tour : {nom_actif.upper()}")

        # Texte "PUISSANCE"
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.setPen(COULEURS['text'])
        painter.drawText(30, y0 + 65, "PUISSANCE")

        # Jauge de puissance
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(60, 60, 80)))
        painter.drawRoundedRect(30, y0 + 75, 200, 15, 4, 4)
        remplissage = int((force / 20) * 200)
        if remplissage > 0:
            painter.setBrush(QBrush(QColor(80, 200, 80)))
            painter.drawRoundedRect(30, y0 + 75, remplissage, 15, 4, 4)

        # ─── ZONE CENTRE : Pseudos, Niveaux et Scores ──────────────────────
        # Pseudos placés plus haut
        font_pseudo = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font_pseudo)
        
        # Joueur Rouge (décalé à gauche)
        painter.setPen(COULEURS['red'])
        texte_j1 = f"{self.pseudos['red']}"
        painter.drawText(self.largeur // 2 - 260, y0 + 60, texte_j1)
        
        # Joueur Bleu (décalé à droite)
        painter.setPen(COULEURS['blue'])
        texte_j2 = f"{self.pseudos['blue']}"
        painter.drawText(self.largeur // 2 + 110, y0 + 60, texte_j2)

        # Scores placés au centre, bien espacés
        font_score = QFont("Arial", 42, QFont.Bold) 
        painter.setFont(font_score)
        
        painter.setPen(COULEURS['red'])
        painter.drawText(self.largeur // 2 - 120, y0 + 95, str(self.scores['red']))

        # Tiret central
        painter.setPen(COULEURS['text'])
        painter.drawText(self.largeur // 2 - 20, y0 + 95, "-")

        painter.setPen(COULEURS['blue'])
        painter.drawText(self.largeur // 2 + 50, y0 + 95, str(self.scores['blue']))

        # ─── ZONE DROITE : Contrôles ───────────────────────────────────────
        painter.setFont(QFont("Arial", 8))
        painter.setPen(COULEURS['text'])
        painter.drawText(self.largeur - 260, y0 + 45, "[ R ] = Rejouer")
        painter.drawText(self.largeur - 260, y0 + 75, "[ ECHAP ] = Menu principal")

    def afficher_vainqueur(self, painter, id_vainqueur):
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.largeur, self.hauteur_totale)
        col = COULEURS[id_vainqueur]
        nom = self.pseudos[id_vainqueur]
        painter.setFont(QFont("Arial", 40, QFont.Bold))
        painter.setPen(col)
        painter.drawText(QRect(0, self.hauteur_totale // 2 - 60, self.largeur, 80),
                         Qt.AlignCenter, f"VICTOIRE DE {nom.upper()} !")
        painter.setFont(QFont("Arial", 18))
        painter.setPen(COULEURS['text'])
        painter.drawText(QRect(0, self.hauteur_totale // 2 + 30, self.largeur, 40),
                         Qt.AlignCenter, "Appuyez sur R pour rejouer ou ECHAP pour le menu")