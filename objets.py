# -*- coding: utf-8 -*-
"""
Module physique du jeu BounceBox.
Contient les classes gérant les balles, la mécanique des collisions (avec NumPy)
et la logique globale du plateau de jeu.
"""

import math
import random
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen


# ── Balles ────────────────────────────────────────────────────────────────────

class Balle:
    """
    Classe de base représentant une balle sur le plateau.
    Gère la physique spatiale, les vitesses et les collisions.
    """
    RAYON = 60
    FRICTION = 0.995
    SEUIL_ARRET = 0.08

    def __init__(self, couleur, x, y):
        """
        Initialise une nouvelle balle.
        :param couleur: Chaîne de caractères ('red', 'blue', 'grey', 'white').
        :param x: Position initiale en X.
        :param y: Position initiale en Y.
        """
        self.couleur = couleur
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.rayon = Balle.RAYON
        self.est_active = True

    def norme_vitesse(self):
        """
        Calcule la vitesse absolue actuelle de la balle grâce au calcul vectoriel NumPy.
        :return: Float représentant la norme du vecteur vitesse.
        """
        return float(np.linalg.norm([self.vx, self.vy]))

    def maj_position(self, largeur, hauteur):
        """
        Met à jour les coordonnées de la balle en fonction de sa vitesse,
        applique la friction et gère les rebonds élastiques sur les bords.
        :param largeur: Largeur totale de la zone de jeu.
        :param hauteur: Hauteur totale de la zone de jeu.
        """
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
        """
        Vérifie mathématiquement si cette balle entre en collision avec une autre.
        :param other: Instance d'une autre Balle.
        :return: Booléen (True si les balles se chevauchent).
        """
        delta = np.array([other.x - self.x, other.y - self.y])
        return float(np.linalg.norm(delta)) < (self.rayon + other.rayon)

    def gerer_collision(self, other):
        """
        Applique un choc élastique parfait entre deux balles via transfert 
        de quantité de mouvement sur le vecteur normal. Utilise NumPy.
        :param other: L'autre Balle impliquée dans la collision.
        """
        delta = np.array([other.x - self.x, other.y - self.y])
        dist = float(np.linalg.norm(delta)) or 0.01
        n = delta / dist

        # Correction de superposition pour éviter que les balles ne fusionnent
        superposition = (self.rayon + other.rayon - dist) / 2
        self.x  -= n[0] * superposition
        self.y  -= n[1] * superposition
        other.x += n[0] * superposition
        other.y += n[1] * superposition

        v1 = np.array([self.vx, self.vy])
        v2 = np.array([other.vx, other.vy])
        v1n = float(np.dot(v1, n))
        v2n = float(np.dot(v2, n))

        # Échange des vitesses sur l'axe normal
        self.vx  += (v2n - v1n) * n[0]
        self.vy  += (v2n - v1n) * n[1]
        other.vx += (v1n - v2n) * n[0]
        other.vy += (v1n - v2n) * n[1]


class BalleBlanche(Balle):
    """
    Hérite de Balle. Représente la balle maîtresse contrôlée par les joueurs.
    Implémente les calculs de trajectoire prédictifs.
    """
    def __init__(self, x, y):
        super().__init__('white', x, y)

    def barre_visee(self, painter, mx, my, couleurs, largeur=850, hauteur_jeu=580):
        """
        Initialise le calcul de la ligne de visée en fonction du curseur de la souris.
        :param painter: Objet QPainter de l'interface graphique.
        :param mx, my: Coordonnées X et Y de la souris.
        """
        dx, dy = self.x - mx, self.y - my
        dist = math.sqrt(dx*dx + dy*dy) or 1
        force = min(dist / 15, 20)
        angle = math.atan2(dy, dx)
        vx = math.cos(angle) * force
        vy = math.sin(angle) * force
        
        pen = QPen(QColor(255, 255, 200, 180), 2)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        self._calculer_trajectoire_recursive(painter, self.x, self.y, vx, vy,
                                             rebonds_restants=3,
                                             largeur=largeur, hauteur_jeu=hauteur_jeu)

    def _calculer_trajectoire_recursive(self, painter, x, y, vx, vy, rebonds_restants, largeur, hauteur_jeu):
        """
        Méthode récursive traçant la ligne de visée en prédisant les rebonds sur les murs.
        S'arrête lorsque le nombre de rebonds maximum est atteint.
        """
        if rebonds_restants < 0 or (abs(vx) < 0.1 and abs(vy) < 0.1):
            return

        temps = []
        if vx > 0:   temps.append((largeur     - Balle.RAYON - x) / vx)
        elif vx < 0: temps.append((Balle.RAYON - x) / vx)
        if vy > 0:   temps.append((hauteur_jeu  - Balle.RAYON - y) / vy)
        elif vy < 0: temps.append((Balle.RAYON  - y) / vy)

        if not temps:
            return

        t = min(t for t in temps if t > 0.001)
        t = min(t, 80)

        nx2, ny2 = x + vx * t, y + vy * t
        painter.drawLine(int(x), int(y), int(nx2), int(ny2))

        if t >= 80:
            return

        nvx, nvy = vx, vy
        if abs(nx2 - Balle.RAYON) < 1 or abs(nx2 - (largeur - Balle.RAYON)) < 1:
            nvx = -vx
        if abs(ny2 - Balle.RAYON) < 1 or abs(ny2 - (hauteur_jeu - Balle.RAYON)) < 1:
            nvy = -vy

        self._calculer_trajectoire_recursive(painter, nx2, ny2, nvx, nvy,
                                             rebonds_restants - 1, largeur, hauteur_jeu)


class BalleFactory:
    """
    Design Pattern Factory (Fabrique).
    Délègue et simplifie l'instanciation des différents types de balles.
    """
    @staticmethod
    def creer_balle(type_balle, x=0, y=0):
        """
        Génère une balle selon le type demandé.
        :param type_balle: 'white' pour la balle contrôlée, sinon couleur classique.
        :return: Instance de BalleBlanche ou Balle.
        """
        if type_balle == 'white':
            return BalleBlanche(x, y)
        return Balle(type_balle, x, y)


# ── Plateau ───────────────────────────────────────────────────────────────────

class Plateau:
    """
    Classe centrale gérant l'arène, la logique de jeu, le score et les tours.
    Comporte la liste globale des objets physiques en jeu.
    """
    def __init__(self, largeur, hauteur, hauteur_barre_info, pseudo_j1, pseudo_j2, parent=None):
        """Initialise le plateau et lance le placement initial des balles."""
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
        """Place la balle blanche au centre et répartit les balles grises et bleues aléatoirement."""
        self.balle_blanche = BalleFactory.creer_balle('white', self.largeur // 2, self.hauteur_jeu // 2)
        self.balles = [self.balle_blanche]
        for couleur in ['grey'] * 9 + ['blue'] * 2:
            while True:
                x = random.randint(100, self.largeur - 100)
                y = random.randint(100, self.hauteur_jeu - 100)
                b = BalleFactory.creer_balle(couleur, x, y)
                if not any(b.verifier_collision(existing) for existing in self.balles):
                    self.balles.append(b)
                    break

    def jouer_coup_souris(self, mx, my):
        """
        Donne une impulsion initiale à la balle blanche en fonction du curseur.
        :param mx, my: Coordonnées de la souris au clic.
        """
        dx, dy = self.balle_blanche.x - mx, self.balle_blanche.y - my
        dist = math.sqrt(dx**2 + dy**2)
        force = min(dist / 15, 25)
        angle = math.atan2(dy, dx)
        self.balle_blanche.vx = math.cos(angle) * force
        self.balle_blanche.vy = math.sin(angle) * force

    def _appliquer_regles(self, balle_touchee):
        """
        Applique les règles de possession, de destruction et de points
        lors d'un contact avec la balle blanche.
        """
        adversaire = 'blue' if self.joueur_actif == 'red' else 'red'
        if balle_touchee.couleur == 'grey':
            balle_touchee.couleur = self.joueur_actif
        elif balle_touchee.couleur == self.joueur_actif:
            balle_touchee.est_active = False
            self.scores[self.joueur_actif] += 1
        elif balle_touchee.couleur == adversaire:
            balle_touchee.couleur = 'grey'

    def maj_physique(self):
        """
        Avance la simulation d'une image : déplace toutes les balles
        et résout les collisions croisées.
        :return: Booléen (True tant qu'au moins une balle est en mouvement).
        """
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
        """Bascule le joueur actif et nettoie les balles détruites."""
        self.joueur_actif = 'blue' if self.joueur_actif == 'red' else 'red'
        self.balles = [b for b in self.balles if b.est_active]

    def verifier_vainqueur(self):
        """
        Vérifie la condition de victoire.
        :return: L'ID du vainqueur ('red' ou 'blue') ou None.
        """
        if self.scores['red'] >= 5:  return 'red'
        if self.scores['blue'] >= 5: return 'blue'
        return None