import unittest
from app import create_app, db
from app.models.utilisateur import Utilisateur
import logging
import os


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        # Configurer le logging pour les tests
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.INFO)
        self.handler = logging.StreamHandler()
        self.handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(self.handler)

        # Créer une application de test avec une base différente
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config[
            'SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:ton_mot_de_passe@localhost:5432/data_recettes_test'
        self.client = self.app.test_client()

        # Appliquer les migrations dans le contexte de test
        with self.app.app_context():
            os.system("flask db upgrade")  # Applique les migrations à recettes_db_test

    def tearDown(self):
        # Nettoyer uniquement la base de test
        with self.app.app_context():
            os.system("flask db downgrade")  # Revenir à l'état initial (optionnel)
            db.drop_all()  # Supprime les tables de recettes_db_test uniquement

        # Fermer proprement le handler de logging
        self.logger.removeHandler(self.handler)
        self.handler.close()

    def test_inscription_succes(self):
        response = self.client.post("/inscription", json={
            "email": "test@example.com",
            "mot_de_passe": "12345678",
            "nom": "Test User"
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn("Inscription réussie", response.get_json()["message"])

    def test_inscription_email_existant(self):
        self.client.post("/inscription", json={
            "email": "test@example.com",
            "mot_de_passe": "12345678",
            "nom": "Test User"
        })
        response = self.client.post("/inscription", json={
            "email": "test@example.com",
            "mot_de_passe": "12345678",
            "nom": "Test User 2"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Cet email est déjà utilisé", response.get_json()["message"])

    def test_inscription_email_invalide(self):
        response = self.client.post("/inscription", json={
            "email": "test.com",
            "mot_de_passe": "12345678",
            "nom": "Test User"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Format d'email invalide", response.get_json()["message"])

    def test_connexion_succes(self):
        self.client.post("/inscription", json={
            "email": "test@example.com",
            "mot_de_passe": "12345678",
            "nom": "Test User"
        })
        response = self.client.post("/connexion", json={
            "email": "test@example.com",
            "mot_de_passe": "12345678"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.get_json())
        self.token = response.get_json()["token"]

    def test_profil_succes(self):
        self.test_connexion_succes()  # Récupère le token
        response = self.client.get("/profil", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["utilisateur"]["email"], "test@example.com")

    def test_profil_token_manquant(self):
        response = self.client.get("/profil")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Token manquant", response.get_json()["message"])

    def test_profil_token_invalide(self):
        response = self.client.get("/profil", headers={
            "Authorization": "Bearer mauvais_token"
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn("Token invalide", response.get_json()["message"])

    def test_connexion_email_inexistant(self):
        response = self.client.post("/connexion", json={
            "email": "inconnu@example.com",
            "mot_de_passe": "12345678"
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn("Email non trouvé", response.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
