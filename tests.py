# -*- coding: utf-8 -*-
"""
Tests unitaires BounceBox — 8 tests du rapport
Exécution : python tests.py
"""
import math
import unittest
from objets import Balle, Plateau

# ─────────────────────────────────────────────────────────────────────────────
#  TESTS CLASSE BALLE (4 tests)
# ─────────────────────────────────────────────────────────────────────────────

class TestBalle(unittest.TestCase):

    def test_deplacement_basique(self):
        """
        Vérifie qu'une balle avec une vitesse initiale se déplace correctement
        et que sa vitesse ralentit à cause de la friction après maj_position().
        """
        balle = Balle('grey', 200, 200)
        balle.vx = 5.0
        balle.vy = 3.0

        balle.maj_position(largeur=800, hauteur=600)

        self.assertAlmostEqual(balle.x, 200 + 5.0, places=3)
        self.assertAlmostEqual(balle.y, 200 + 3.0, places=3)
        self.assertAlmostEqual(balle.vx, 5.0 * Balle.FRICTION, places=3)
        self.assertAlmostEqual(balle.vy, 3.0 * Balle.FRICTION, places=3)

    def test_detection_collision(self):
        """
        Vérifie que verifier_collision() retourne True si deux balles se touchent
        (distance < 2*RAYON) et False sinon.
        """
        b1 = Balle('grey', 100, 100)
        b2 = Balle('grey', 100, 100)  
        self.assertTrue(b1.verifier_collision(b2))

        b2.x = 100 + 3 * Balle.RAYON
        self.assertFalse(b1.verifier_collision(b2))

        b2.x = 100 + 2 * Balle.RAYON
        self.assertFalse(b1.verifier_collision(b2))

    def test_rebond_murs(self):
        """
        Vérifie qu'une balle sortant des limites du plateau est recalée
        contre le bord et que sa vitesse perpendiculaire est inversée.
        """
        LARGEUR, HAUTEUR = 800, 600

        # — Rebond mur gauche —
        b = Balle('grey', 5, 300)   
        b.vx = -10.0                
        b.vy = 0.0
        b.maj_position(LARGEUR, HAUTEUR)
        self.assertGreaterEqual(b.x, Balle.RAYON)   
        self.assertGreater(b.vx, 0)                  

        # — Rebond mur droit —
        b = Balle('grey', LARGEUR - 5, 300)
        b.vx = 10.0
        b.vy = 0.0
        b.maj_position(LARGEUR, HAUTEUR)
        self.assertLessEqual(b.x, LARGEUR - Balle.RAYON)
        self.assertLess(b.vx, 0)                     

        # — Rebond mur haut —
        b = Balle('grey', 300, 5)
        b.vx = 0.0
        b.vy = -10.0
        b.maj_position(LARGEUR, HAUTEUR)
        self.assertGreaterEqual(b.y, Balle.RAYON)
        self.assertGreater(b.vy, 0)

        # — Rebond mur bas —
        b = Balle('grey', 300, HAUTEUR - 5)
        b.vx = 0.0
        b.vy = 10.0
        b.maj_position(LARGEUR, HAUTEUR)
        self.assertLessEqual(b.y, HAUTEUR - Balle.RAYON)
        self.assertLess(b.vy, 0)

    def test_resolution_collision(self):
        """
        Vérifie qu'après gerer_collision(), les deux balles ne se chevauchent plus
        et que leurs vitesses sur l'axe de collision ont été échangées (choc élastique).
        """
        b1 = Balle('grey', 100, 100)
        b2 = Balle('grey', 100 + 2 * Balle.RAYON - 5, 100)  

        b1.vx, b1.vy = 8.0, 0.0
        b2.vx, b2.vy = -4.0, 0.0

        b1.gerer_collision(b2)

        dist = math.sqrt((b2.x - b1.x)**2 + (b2.y - b1.y)**2)
        self.assertGreaterEqual(dist, 2 * Balle.RAYON - 0.01)  

        self.assertLess(b1.vx, 8.0)   
        self.assertGreater(b2.vx, -4.0)  


# ─────────────────────────────────────────────────────────────────────────────
#  TESTS CLASSE PLATEAU (4 tests)
# ─────────────────────────────────────────────────────────────────────────────

class TestPlateau(unittest.TestCase):

    def setUp(self):
        """Crée un plateau frais avant chaque test."""
        self.plateau = Plateau(largeur=800, hauteur=620, hauteur_barre_info=120, pseudo_j1="J1", pseudo_j2="J2")

    def test_initialisation(self):
        """
        Vérifie que le plateau contient exactement 1 balle blanche, 9 grises et 2 bleues.
        Les scores doivent être à zéro et le joueur actif doit être 'red'.
        """
        balles = self.plateau.balles

        nb_blanches = sum(1 for b in balles if b.couleur == 'white')
        nb_grises   = sum(1 for b in balles if b.couleur == 'grey')
        nb_bleues   = sum(1 for b in balles if b.couleur == 'blue')

        self.assertEqual(nb_blanches, 1)
        self.assertEqual(nb_grises,   9)
        self.assertEqual(nb_bleues,   2)
        self.assertEqual(len(balles), 12)

        self.assertEqual(self.plateau.scores['red'],  0)
        self.assertEqual(self.plateau.scores['blue'], 0)
        self.assertEqual(self.plateau.joueur_actif, 'red')

    def test_application_des_regles(self):
        """
        Vérifie que _appliquer_regles() modifie correctement la couleur des balles
        ou incrémente le score selon le propriétaire de la balle touchée.
        """
        p = self.plateau
        p.joueur_actif = 'red'

        # Cas 1 : balle grise → devient rouge
        balle_grise = Balle('grey', 200, 200)
        p._appliquer_regles(balle_grise)
        self.assertEqual(balle_grise.couleur, 'red')

        # Cas 2 : balle rouge (joueur actif) → éliminée, +1 point
        balle_rouge = Balle('red', 200, 200)
        p._appliquer_regles(balle_rouge)
        self.assertFalse(balle_rouge.est_active)
        self.assertEqual(p.scores['red'], 1)

        # Cas 3 : balle bleue (adversaire) → repasse grise
        balle_bleue = Balle('blue', 200, 200)
        p._appliquer_regles(balle_bleue)
        self.assertEqual(balle_bleue.couleur, 'grey')

    def test_changement_de_tour(self):
        """
        Vérifie que changer_tour() alterne le joueur actif entre 'red' et 'blue'
        et supprime de la liste les balles inactives.
        """
        p = self.plateau
        self.assertEqual(p.joueur_actif, 'red')

        balle_a_supprimer = p.balles[1]
        balle_a_supprimer.est_active = False
        nb_avant = len(p.balles)

        p.changer_tour()

        self.assertEqual(p.joueur_actif, 'blue')                
        self.assertEqual(len(p.balles), nb_avant - 1)           
        self.assertNotIn(balle_a_supprimer, p.balles)           

        p.changer_tour()
        self.assertEqual(p.joueur_actif, 'red')

    def test_victoire(self):
        """
        Vérifie que verifier_vainqueur() retourne l'identifiant du joueur gagnant ('red' ou 'blue')
        s'il atteint 5 points, sinon None.
        """
        p = self.plateau
        self.assertIsNone(p.verifier_vainqueur())

        # Victoire de rouge (Correction appliquée ici !)
        p.scores['red'] = 5
        self.assertEqual(p.verifier_vainqueur(), 'red')

        # Reset et victoire du bleu (Correction appliquée ici !)
        p.scores['red']  = 3
        p.scores['blue'] = 5
        self.assertEqual(p.verifier_vainqueur(), 'blue')

        p.scores['red']  = 4
        p.scores['blue'] = 4
        self.assertIsNone(p.verifier_vainqueur())

if __name__ == '__main__':
    unittest.main(verbosity=2)
