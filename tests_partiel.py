import math
import unittest
from objets_partiel import Balle, Plateau


class TestBalle(unittest.TestCase):

    def test_deplacement_basique(self):
        """
        Une balle avec une vitesse initiale doit se déplacer
        et ralentir à cause de la friction après un appel à maj_position().
        """
        balle = Balle('grey', 200, 200)
        balle.vx = 5.0
        balle.vy = 3.0

        balle.maj_position(largeur=800, hauteur=600)

        # maj_position ajoute d'abord vx/vy à la position, puis applique la friction.
        # Donc : nouvelle_position = ancienne + vitesse_initiale
        #        nouvelle_vitesse  = vitesse_initiale * FRICTION
        self.assertAlmostEqual(balle.x, 200 + 5.0, places=3)
        self.assertAlmostEqual(balle.y, 200 + 3.0, places=3)

        # La vitesse doit avoir diminué (friction appliquée après le déplacement)
        self.assertAlmostEqual(balle.vx, 5.0 * Balle.FRICTION, places=3)
        self.assertAlmostEqual(balle.vy, 3.0 * Balle.FRICTION, places=3)


    def test_detection_collision(self):
        """
        verifier_collision() doit retourner True si deux balles se touchent
        (distance < 2*RAYON) et False sinon.
        """
        b1 = Balle('grey', 100, 100)
        b2 = Balle('grey', 100, 100)  # même position → superposition totale

        # Les deux balles se chevauchent : collision détectée
        self.assertTrue(b1.verifier_collision(b2))

        # On éloigne b2 bien au-delà de 2*RAYON
        b2.x = 100 + 3 * Balle.RAYON
        self.assertFalse(b1.verifier_collision(b2))

        # Cas limite : balles exactement tangentes (distance == 2*RAYON)
        # La condition est strictement inférieure donc pas de collision
        b2.x = 100 + 2 * Balle.RAYON
        self.assertFalse(b1.verifier_collision(b2))


    def test_rebond_murs(self):
        """
        Une balle qui sort des limites du plateau doit être recalée
        contre le bord et voir sa composante de vitesse perpendiculaire inversée.
        """
        LARGEUR, HAUTEUR = 800, 600

        # — Rebond mur gauche —
        b = Balle('grey', 5, 300)   # x très proche du bord gauche
        b.vx = -10.0                # elle va vers la gauche
        b.vy = 0.0
        b.maj_position(LARGEUR, HAUTEUR)
        self.assertGreaterEqual(b.x, Balle.RAYON)   # recalée contre le bord
        self.assertGreater(b.vx, 0)                  # vitesse inversée (→ droite)

        # — Rebond mur droit —
        b = Balle('grey', LARGEUR - 5, 300)
        b.vx = 10.0
        b.vy = 0.0
        b.maj_position(LARGEUR, HAUTEUR)
        self.assertLessEqual(b.x, LARGEUR - Balle.RAYON)
        self.assertLess(b.vx, 0)                     # vitesse inversée (→ gauche)

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
        Après gerer_collision(), les deux balles ne doivent plus se chevaucher
        et leurs composantes de vitesse selon l'axe de collision doivent
        avoir été échangées (choc élastique entre masses égales).
        """
        # On place deux balles légèrement superposées sur l'axe horizontal
        b1 = Balle('grey', 100, 100)
        b2 = Balle('grey', 100 + 2 * Balle.RAYON - 5, 100)  # chevauchement de 5 px

        # Vitesses opposées sur l'axe x uniquement
        b1.vx, b1.vy = 8.0, 0.0
        b2.vx, b2.vy = -4.0, 0.0

        b1.gerer_collision(b2)

        # 1) Plus de superposition : distance >= 2 * RAYON
        dist = math.sqrt((b2.x - b1.x)**2 + (b2.y - b1.y)**2)
        self.assertGreaterEqual(dist, 2 * Balle.RAYON - 0.01)  # tolérance numérique

        # 2) Échange des vitesses sur l'axe de collision (horizontal ici)
        # b1 doit repartir vers la gauche, b2 vers la droite
        self.assertLess(b1.vx, 8.0)   # b1 a ralenti / changé de sens
        self.assertGreater(b2.vx, -4.0)  # b2 a accéléré / changé de sens

class TestPlateau(unittest.TestCase):
    
    
    

    def setUp(self):
        """Crée un plateau frais avant chaque test."""
        self.plateau = Plateau(largeur=800, hauteur=620, hauteur_barre_info=120)

    def test_application_des_regles(self):
        """
        _appliquer_regles() doit :
          - Changer une balle grise en couleur du joueur actif
          - Éliminer une balle de la couleur du joueur actif et incrémenter le score
          - Repasser une balle adverse en grise
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
        self.assertFalse(balle_rouge.est_active, "La balle rouge doit être désactivée")
        self.assertEqual(p.scores['red'], 1,      "Le score de red doit être 1")

        # Cas 3 : balle bleue (adversaire) → repasse grise
        balle_bleue = Balle('blue', 200, 200)
        p._appliquer_regles(balle_bleue)
        self.assertEqual(balle_bleue.couleur, 'grey')

    def test_changement_de_tour(self):
        
        
        """
        changer_tour() doit alterner le joueur actif entre 'red' et 'blue'
        et supprimer de la liste les balles inactives.
        """
        p = self.plateau
        self.assertEqual(p.joueur_actif, 'red')

        # On désactive manuellement une balle pour vérifier le nettoyage
        balle_a_supprimer = p.balles[1]
        balle_a_supprimer.est_active = False
        nb_avant = len(p.balles)

        p.changer_tour()

        self.assertEqual(p.joueur_actif, 'blue')                # tour basculé
        self.assertEqual(len(p.balles), nb_avant - 1)           # balle retirée
        self.assertNotIn(balle_a_supprimer, p.balles)           # elle n'est plus là

        # Second changement : retour à red
        p.changer_tour()
        self.assertEqual(p.joueur_actif, 'red')

# LANCEMENT DES TESTS
if __name__ == '__main__':
    unittest.main(verbosity=2)

