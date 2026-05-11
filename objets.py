# -*- coding: utf-8 -*-
import math
import random
from PyQt5.QtCore import QPointF, Qt, QRect
from PyQt5.QtGui import (QColor, QPen, QBrush, QFont,
                         QRadialGradient, QLinearGradient)

COULEURS = {
    'background': QColor(20, 20, 35),
    'table':      QColor(34, 85, 50),
    'border':     QColor(80, 50, 20),
    'white':      QColor(245, 245, 245),
    'grey':       QColor(160, 160, 160),
    'red':        QColor(220, 60, 60),
    'blue':       QColor(60, 130, 220),
    'ui_bg':      QColor(15, 15, 28),
    'text':       QColor(220, 220, 200),}


class Balle:
    RAYON = 30
    FRICTION = 0.985 
    # Modélisation arbitraire du coefficient de friction 
    # pour que la résistance de la balle paraisse réaliste
    SEUIL_ARRET = 0.08
    # seuil d'arrêt utilisée dans maj_position
    def __init__(self, couleur, x, y):
        self.couleur = couleur
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.rayon = Balle.RAYON
        # Pour désigner la balle qui va subir l'action
        self.est_active = True 
        
    def Norme_vitesse(self):
        return math.sqrt(self.vx ** 2 + self.vy ** 2)
    
    def Maj_position(self, largeur, hauteur):
        # Modélisation physique de l'échange des composantes de vitesse 
        # selon l axe de collsion pour un choc élastique entre deux sphères 
        # Actualisation des vexteurs positions suite à une collision
        self.x += self.vx
        self.y += self.vy
        # Coefficient de friction appliqué à la vitesse
        self.vx *= self.FRICTION
        self.vy *= self.FRICTION
        # les Collisions et Rebonds sur les Murs
        r = self.rayon
        # Rebond mur gauche
        if self.x - r <= 0:        
            self.x, self.vx = r, abs(self.vx)
        # Rebond mur droit
        elif self.x + r >= largeur: 
            self.x, self.vx = largeur - r, -abs(self.vx)
        # Rebond mur du bas
        if self.y - r <= 0:        
            self.y, self.vy = r, abs(self.vy)
        # Rebond mur du haut
        elif self.y + r >= hauteur: 
            self.y, self.vy = hauteur - r, -abs(self.vy)
        # On définit un seuil d'arrêt net 
        # puisque la vitesse peut tendre vers 0 sans jamais l'atteindre  
        if self.vitesse_mag() < self.SEUIL_ARRET:
            self.vx = self.vy = 0.0
            
        
    def Verifier_collision(self, other):
        # Différence de position de 2 boules
        dx, dy = other.x - self.x, other.y - self.y
        # On vérifie si la distance entre les 2 centres des boules est inférieure à 2R, 
        # Si on renvoit True, il y a collision
        return math.sqrt(dx*dx + dy*dy) < (self.rayon + other.rayon)
    
    
    def Resoudre_collision(self, other):
        # Étape 1 : Détermination de l'axe de collision
        dx, dy = other.x - self.x, other.y - self.y
        # le or 0.01 résout le problème de la superposition parfaite de 2 boules, 
        # auquel cas la distance serait nulle et on risquerait de diviser par 0
        dist = math.sqrt(dx*dx + dy*dy) or 0.01
        nx, ny = dx / dist, dy / dist
        # Étape 2 : Séparer les balles qui se chevauchent
        superposition = (self.rayon + other.rayon - dist) / 2
        self.x -= nx * superposition 
        self.y -= ny * superposition
        other.x += nx * superposition 
        other.y += ny * superposition
        # Étape 3 : Calcul de la vitesse d'impact
        v1n = self.vx * nx + self.vy * ny
        v2n = other.vx * nx + other.vy * ny
        # Étape 4 : Échange des composantes de vitesse le long de la normale
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
    def Barre_visee(self, painter, mx, my):
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
    def __init__(self, largeur, hauteur, hauteur_barre_info):
        self.largeur = largeur
        self.hauteur_jeu = hauteur - hauteur_barre_info
        self.hauteur_totale = hauteur
        self.hauteur_barre_info = hauteur_barre_info
        self.balles = []
        self.scores = {'red': 0, 'blue': 0}
        self.joueur_actif = 'red'
        self._initialiser()

    #On initialise le plateau selon les regles BounceBox
    def _initialiser(self):
        self.balle_blanche = BalleBlanche(self.largeur // 2, self.hauteur_jeu // 2)
        self.balles = [self.balle_blanche]
        for couleur in ['grey'] * 9 + ['blue'] * 2:
            self.balles.append(Balle(
                couleur,
                random.randint(50, self.largeur - 50),
                random.randint(50, self.hauteur_jeu - 50)
            ))

    # ── Logique de jeu ────────────────────────────────────────────────────────
  
    def jouer_coup_souris(self, mx, my):
        #On calcul la distance
        dx, dy = self.balle_blanche.x - mx, self.balle_blanche.y - my
        #
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
            if b.est_active and b.vitesse_mag() > 0.05:
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
                    b1.resoudre_collision(b2)

        return any(b.est_active and b.vitesse_mag() > 0.05 for b in self.balles)

    def changer_tour(self):
        self.joueur_actif = 'blue' if self.joueur_actif == 'red' else 'red'
        self.balles = [b for b in self.balles if b.est_active]

    def verifier_vainqueur(self):
        if self.scores['red'] >= 5:  return "ROUGE"
        if self.scores['blue'] >= 5: return "BLEU"
        return None

    # ── Dessin ────────────────────────────────────────────────────────────────

    def dessiner_plateau(self, painter):
        painter.setPen(QPen(COULEURS['border'], 12))
        painter.setBrush(QBrush(COULEURS['table']))
        painter.drawRoundedRect(0, 0, self.largeur, self.hauteur_jeu, 8, 8)

    def dessiner_balles(self, painter):
        for b in self.balles:
            b.draw(painter)

    def dessiner_visee(self, painter, pos_souris):
        self.balle_blanche.Barre_visee(painter, *pos_souris)

    def dessiner_barre_visee(self, painter, force):
        y0 = self.hauteur_jeu
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(COULEURS['ui_bg']))
        painter.drawRect(0, y0, self.largeur, self.hauteur_barre_info)

        font = QFont("Arial", 14, QFont.Bold)
        painter.setFont(font)

        col_j = COULEURS['red'] if self.joueur_actif == 'red' else COULEURS['blue']
        painter.setPen(col_j)
        painter.drawText(20, y0 + 34, f"TOUR : {self.joueur_actif.upper()}")

        painter.setPen(COULEURS['red'])
        painter.drawText(self.largeur // 2 - 130, y0 + 50, f"ROUGE : {self.scores['red']}")
        painter.setPen(COULEURS['blue'])
        painter.drawText(self.largeur // 2 + 130,  y0 + 50, f"BLEU : {self.scores['blue']}")

        # Barre de force
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(60, 60, 80)))
        painter.drawRoundedRect(20, y0 + 45, 200, 12, 4, 4)
        remplissage = int((force / 20) * 200)
        if remplissage > 0:
            painter.setBrush(QBrush(QColor(80, 200, 80)))
            painter.drawRoundedRect(20, y0 + 45, remplissage, 12, 4, 4)

        painter.setPen(COULEURS['text'])
        painter.setFont(QFont("Arial", 10))
        painter.drawText(20, y0 + 92, "R = Rejouer")

    def afficher_vainqueur(self, painter, nom):
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.largeur, self.hauteur_totale)

        col = COULEURS['red'] if nom == "ROUGE" else COULEURS['blue']
        painter.setFont(QFont("Arial", 40, QFont.Bold))
        painter.setPen(col)
        painter.drawText(QRect(0, self.hauteur_totale // 2 - 60, self.largeur, 80),
                         Qt.AlignCenter, f"VICTOIRE DE {nom} !")

        painter.setFont(QFont("Arial", 18))
        painter.setPen(COULEURS['text'])
        painter.drawText(QRect(0, self.hauteur_totale // 2 + 30, self.largeur, 40),
                         Qt.AlignCenter, "Appuyez sur R pour rejouer")

