import math
import random

class Balle:
    RAYON = 30
    FRICTION = 0.988
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
        
    def norme_vitesse(self):
        return math.sqrt(self.vx ** 2 + self.vy ** 2)
    
    def maj_position(self, largeur, hauteur):
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
        if self.norme_vitesse() < self.SEUIL_ARRET: # CORRIGÉ : n minuscule
            self.vx = self.vy = 0.0
            
        
    def verifier_collision(self, other):
        # Différence de position de 2 boules
        dx, dy = other.x - self.x, other.y - self.y
        # On vérifie si la distance entre les 2 centres des boules est inférieure à 2R, 
        # Si on renvoit True, il y a collision
        return math.sqrt(dx*dx + dy*dy) < (self.rayon + other.rayon)
    
    
    def gerer_collision(self, other):
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
        
class BalleBlanche(Balle):
    def __init__(self, x, y):
        super().__init__('white', x, y)
        
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
        
    def _initialiser(self):
        self.balle_blanche = BalleBlanche(self.largeur // 2, self.hauteur_jeu // 2)
        self.balles = [self.balle_blanche]
        for couleur in ['grey'] * 9 + ['blue'] * 2:
            self.balles.append(Balle(couleur,random.randint(50, self.largeur - 50),random.randint(50, self.hauteur_jeu - 50)))

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
            if b.est_active and b.norme_vitesse() > 0.05: # CORRIGÉ : n minuscule
                b.maj_position(self.largeur, self.hauteur_jeu) # CORRIGÉ : m minuscule

        for i, b1 in enumerate(self.balles):
            if not b1.est_active:
                continue
            for b2 in self.balles[i+1:]:
                if not b2.est_active:
                    continue
                if b1.verifier_collision(b2): # CORRIGÉ : v minuscule
                    if b1.couleur == 'white' or b2.couleur == 'white':
                        self._appliquer_regles(b2 if b1.couleur == 'white' else b1)
                    b1.gerer_collision(b2)

        return any(b.est_active and b.norme_vitesse() > 0.05 for b in self.balles)

    def changer_tour(self):
        self.joueur_actif = 'blue' if self.joueur_actif == 'red' else 'red'
        self.balles = [b for b in self.balles if b.est_active]

    def verifier_vainqueur(self):
        # Reste à implémenter
        pass
 
        