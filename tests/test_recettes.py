import unittest
from app import create_app, db
from app.models.utilisateur import Utilisateur
from app.models.recette import Recette
from app.models.ingredient import Ingredient
from app.models.recette_ingredient import RecetteIngredient


class TestRecettes(unittest.TestCase):
    def setUp(self):
        """
        Configure l'environnement de test avant chaque test.
        Crée une base de données de test, un utilisateur unique et un token JWT.
        """
        # Initialisation de l'application en mode test
        self.app = create_app()
        self.app.config["SQLALCHEMY_DATABASE_URI"] = (
            "postgresql://postgres:1234@localhost:5432/recettes_db_test"
        )
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Création des tables et ajout d'un utilisateur de test avec identifiants uniques
        with self.app.app_context():
            db.create_all()  # Recréer les tables pour les tests
            utilisateur = Utilisateur(
                email="utilisateur_test_recettes@example.com",  # Email unique pour les tests
                mot_de_passe="TestPass2025",                   # Mot de passe différent
                nom="Utilisateur Recettes"                     # Nom distinct
            )
            db.session.add(utilisateur)
            db.session.commit()

            # Connexion pour obtenir un token JWT
            response = self.client.post("/connexion", json={
                "email": "utilisateur_test_recettes@example.com",
                "mot_de_passe": "TestPass2025"
            })
            self.token = response.get_json()["token"]

    def tearDown(self):
        """
        Nettoie l'environnement après chaque test.
        Supprime les tables et la session.
        """
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_creer_recette(self):
        """
        Teste la création d'une recette avec un titre et un ingrédient.
        Vérifie le code 201 et les données renvoyées.
        """
        response = self.client.post("/recettes", json={
            "titre": "Pâtes au pesto",
            "ingredients": [{"nom": "Pâtes", "quantite": "200g"}]
        }, headers={"Authorization": f"Bearer {self.token}"})

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["message"], "Recette créée avec succès")
        self.assertEqual(data["recette"]["titre"], "Pâtes au pesto")

    def test_lister_recettes(self):
        """
        Teste la récupération de la liste des recettes.
        Vérifie le code 200 et la présence d'au moins une recette.
        """
        # Créer une recette pour le test
        self.client.post("/recettes", json={
            "titre": "Pâtes au pesto",
            "ingredients": [{"nom": "Pâtes", "quantite": "200g"}]
        }, headers={"Authorization": f"Bearer {self.token}"})

        # Lister les recettes
        response = self.client.get("/recettes", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(len(data) > 0)

    def test_modifier_recette(self):
        """
        Teste la modification d'une recette existante.
        Vérifie le code 200 et la mise à jour des données.
        """
        # Créer une recette initiale
        response_creation = self.client.post("/recettes", json={
            "titre": "Pâtes au pesto",
            "ingredients": [{"nom": "Pâtes", "quantite": "200g"}]
        }, headers={"Authorization": f"Bearer {self.token}"})
        recette_id = response_creation.get_json()["recette"]["id_recette"]

        # Modifier la recette
        response = self.client.put(f"/recettes/{recette_id}", json={
            "titre": "Pâtes au pesto revisitées",
            "description": "Une version améliorée",
            "ingredients": [{"nom": "Pesto", "quantite": "50g"}]
        }, headers={"Authorization": f"Bearer {self.token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["message"], "Recette mise à jour avec succès")
        self.assertEqual(data["recette"]["titre"], "Pâtes au pesto revisitées")
        self.assertEqual(data["recette"]["description"], "Une version améliorée")

    def test_supprimer_recette(self):
        """
        Teste la suppression d'une recette existante.
        Vérifie le code 200 et l'absence de la recette après suppression.
        """
        # Créer une recette initiale
        response_creation = self.client.post("/recettes", json={
            "titre": "Pâtes au pesto",
            "ingredients": [{"nom": "Pâtes", "quantite": "200g"}]
        }, headers={"Authorization": f"Bearer {self.token}"})
        recette_id = response_creation.get_json()["recette"]["id_recette"]

        # Supprimer la recette
        response = self.client.delete(f"/recettes/{recette_id}",
                                      headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["message"], "Recette supprimée avec succès")

        # Vérifier que la recette n'existe plus
        response_get = self.client.get(f"/recettes/{recette_id}",
                                       headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response_get.status_code, 404)


if __name__ == "__main__":
    unittest.main()