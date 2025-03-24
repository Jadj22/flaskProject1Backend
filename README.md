

# README - Itération 1 : Authentification

## Résumé de l’itération

Cette première itération a permis de mettre en place un **système d’authentification** pour une application de gestion de recettes.  
L’objectif principal était de permettre aux utilisateurs de :  
- S’inscrire,  
- Se connecter,  
- Se déconnecter,  
- Accéder à des routes protégées via un token JWT.  

Le développement a suivi une **approche agile légère**, avec des cycles courts : planification, codage, tests et validation.  
Période de réalisation : **du 1er au 8 mars 2025**.

---

## Fonctionnalités accomplies

1. **Inscription**  
   - **Route** : `POST /inscription`  
   - **Fonctionnalités** :  
     - Création d’un utilisateur avec un email, un mot de passe haché (via `werkzeug.security`, algorithme scrypt) et un nom.  
   - **Validations** :  
     - Unicité de l’email,  
     - Format d’email valide,  
     - Mot de passe d’au moins 8 caractères,  
     - Nom non vide.  
   - **Réponse** :  
     ```json
     {
       "message": "Inscription réussie",
       "utilisateur": {"id_utilisateur": 1, "email": "joel@example.com", "nom": "Joel Dupont"}
     }
     ```  
     Code HTTP : **201**.

2. **Connexion**  
   - **Route** : `POST /connexion`  
   - **Fonctionnalités** :  
     - Authentification avec email et mot de passe,  
     - Génération d’un token JWT via `flask-jwt-extended`.  
   - **Réponse** :  
     ```json
     {
       "token": "jwt_token",
       "utilisateur": {"id_utilisateur": 1, "email": "joel@example.com", "nom": "Joel Dupont"}
     }
     ```  
     Code HTTP : **200**.

3. **Déconnexion**  
   - **Route** : `POST /deconnexion`  
   - **Fonctionnalités** :  
     - Permet à un utilisateur authentifié de se déconnecter (protection via `@jwt_required()`),  
     - Le token doit être supprimé côté client (JWT stateless).  
   - **Réponse** :  
     ```json
     {"message": "Déconnexion réussie, veuillez supprimer le token localement"}
     ```  
     Code HTTP : **200**.

4. **Profil (route protégée)**  
   - **Route** : `GET /profil`  
   - **Fonctionnalités** :  
     - Retourne les informations de l’utilisateur connecté (protection via `@jwt_required()`).  
   - **Réponse** :  
     ```json
     {
       "utilisateur": {"id_utilisateur": 1, "email": "joel@example.com", "nom": "Joel Dupont"}
     }
     ```  
     Code HTTP : **200**.

5. **Modèle Utilisateur**  
   - **Table** : `utilisateurs` dans PostgreSQL  
   - **Colonnes** :  
     - `id_utilisateur` (clé primaire),  
     - `email` (unique),  
     - `nom`,  
     - `mot_de_passe` (haché).  
   - **Définition** : `app/models/utilisateur.py`.

6. **Infrastructure**  
   - Organisation modulaire avec Flask :  
     - `app/`  
     - `models/`  
     - `routes/`  
     - `utils/`  
   - Base de données PostgreSQL gérée via :  
     - `Flask-SQLAlchemy`  
     - `Flask-Migrate` (pour les migrations)  
   - Gestion des tokens JWT avec `Flask-JWT-Extended`.  
   - Logging configuré :  
     - Application : `app.log`  
     - Routes d’authentification : `auth.log`

---

## Structure du projet après l’itération 1

```
flaskProject1/
├── app/
│   ├── __init__.py         # Initialisation de l'application Flask
│   ├── config.py           # Configuration (DB, clés secrètes)
│   ├── models/
│   │   ├── __init__.py     # Fichier vide pour module
│   │   ├── utilisateur.py  # Modèle Utilisateur
│   ├── routes/
│   │   ├── __init__.py     # Fichier vide pour module
│   │   ├── auth.py         # Routes d'authentification
│   ├── utils/
│   │   ├── __init__.py     # Fichier vide pour module
│   │   └── auth_utils.py   # (Optionnel, non utilisé pour l'instant)
├── tests/
│   ├── __init__.py         # Fichier vide pour module
│   ├── test_auth.py        # Tests unitaires pour l'authentification
├── venv/                   # Environnement virtuel
├── migrations/             # Dossier des migrations Flask-Migrate
├── requirements.txt        # Dépendances Python
├── app.py                  # Point d'entrée de l'application
└── README.md               # Documentation (ce fichier)
```

---

## Difficultés rencontrées et solutions

### 1. Erreur de connexion à PostgreSQL
- **Problème** : Erreur `psycopg2.OperationalError` (impossible de se connecter à la base).  
- **Cause** : Mot de passe incorrect dans `SQLALCHEMY_DATABASE_URI` (`config.py`).  
- **Solution** :  
  - Mise à jour de `config.py` :  
    ```python
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:mon_mot_de_passe@localhost:5432/recettes_db"
    ```  
  - Création manuelle de la base :  
    ```sql
    CREATE DATABASE recettes_db;
    ```

### 2. Oubli des fichiers `__init__.py`
- **Problème** : Erreurs d’importation (dossiers non reconnus comme modules).  
- **Cause** : Absence des fichiers `__init__.py` dans `models/`, `routes/`, et `utils/`.  
- **Solution** : Ajout de fichiers `__init__.py` vides.

### 3. Erreur `StringDataRightTruncation` sur `mot_de_passe`
- **Problème** : Hash trop long pour `VARCHAR(128)` (`psycopg2.errors.StringDataRightTruncation`).  
- **Cause** : Hash `scrypt` de `werkzeug.security` dépassait 128 caractères.  
- **Solution** :  
  - Champ modifié dans `utilisateur.py` :  
    ```python
    mot_de_passe = db.Column(db.String(255), nullable=False)
    ```  
  - Mise à jour de la table :  
    ```sql
    ALTER TABLE utilisateurs ALTER COLUMN mot_de_passe TYPE VARCHAR(255);
    ```

### 4. Gestion manuelle de la base de données
- **Problème** : Modifications manuelles des tables sans suivi.  
- **Cause** : Utilisation de `db.create_all()` sans migrations.  
- **Solution** :  
  - Intégration de `Flask-Migrate` :  
    - Ajout dans `requirements.txt` : `Flask-Migrate==4.0.7`  
    - Initialisation dans `app/__init__.py` :  
      ```python
      from flask_migrate import Migrate
      migrate = Migrate()
      migrate.init_app(app, db)
      ```  
    - Commandes :  
      ```bash
      flask db init
      flask db migrate -m "Initial migration with Utilisateur model"
      flask db upgrade
      ```  
  - Suppression de `db.create_all()`.

### 5. Gestion des erreurs JWT
- **Problème** : Erreurs de tokens (absent, invalide, expiré) non gérées.  
- **Cause** : Absence de gestionnaires personnalisés pour `flask-jwt-extended`.  
- **Solution** :  
  - Gestionnaires ajoutés dans `app/__init__.py` :  
    ```python
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        logger.warning("Requête non autorisée : token manquant")
        return jsonify({"message": "Token manquant, veuillez vous connecter"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        logger.warning(f"Token invalide : {str(error)}")
        return jsonify({"message": "Token invalide"}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        logger.warning(f"Token expiré pour utilisateur : {jwt_payload['sub']}")
        return jsonify({"message": "Token expiré, veuillez vous reconnecter"}), 401
    ```

### 6. Erreur dans les tests unitaires : `werkzeug.__version__`
- **Problème** : `AttributeError: module 'werkzeug' has no attribute '__version__'`.  
- **Cause** : Incompatibilité Flask 2.3.2 / Werkzeug 3.x.  
- **Solution** :  
  - Version fixée dans `requirements.txt` :  
    ```
    Werkzeug==2.3.7
    ```  
  - Réinstallation :  
    ```bash
    pip install -r requirements.txt
    ```

### 7. ResourceWarning pour les fichiers de logs
- **Problème** : `ResourceWarning: unclosed file` dans les tests.  
- **Cause** : Gestionnaires de logs non fermés.  
- **Solution** :  
  - Logging conditionnel dans `auth.py` et `__init__.py` :  
    ```python
    if not app.config.get('TESTING'):
        # Configurer le logging
    ```  
  - Fermeture dans `test_auth.py` (`tearDown`).

### 8. Erreur `UndefinedTable` dans l’application principale
- **Problème** : `relation « utilisateurs » n'existe pas`.  
- **Cause** : Table non créée (migrations non appliquées).  
- **Solution** :  
  - Recréation de `recettes_db` :  
    ```sql
    CREATE DATABASE recettes_db;
    ```  
  - Application des migrations :  
    ```bash
    flask db migrate -m "Initial migration with Utilisateur model"
    flask db upgrade
    ```

### 9. Conflit entre base principale et base de test
- **Problème** : Tests utilisaient `recettes_db` au lieu de `recettes_db_test`.  
- **Cause** : Même `SQLALCHEMY_DATABASE_URI`.  
- **Solution** :  
  - Bases séparées :  
    - `recettes_db` (app)  
    - `recettes_db_test` (tests)  
  - Recréation :  
    ```bash
    psql -U postgres -c "DROP DATABASE IF EXISTS recettes_db;"
    psql -U postgres -c "CREATE DATABASE recettes_db;"
    psql -U postgres -c "DROP DATABASE IF EXISTS recettes_db_test;"
    psql -U postgres -c "CREATE DATABASE recettes_db_test;"
    ```  
  - Migrations :  
    ```bash
    flask db upgrade
    ```

### 10. Erreur de token sur `/deconnexion` : Token manquant
- **Problème** : `401 UNAUTHORIZED` ("Token manquant").  
- **Cause** : En-tête `Authorization` absent.  
- **Solution** :  
  - Ajout dans Postman : `Authorization: Bearer <token>`.

### 11. Erreur de token sur `/deconnexion` : Subject must be a string
- **Problème** : `Token invalide : Subject must be a string`.  
- **Cause** : `identity` était un entier (`utilisateur.id_utilisateur`).  
- **Solution** :  
  - Conversion en chaîne dans `/connexion` :  
    ```python
    token = create_access_token(identity=str(utilisateur.id_utilisateur))
    ```  
  - Régénération et retest.

---

## Tests effectués

### Tests manuels (via Postman)
1. **Inscription**  
   - Requête : `POST http://localhost:5000/inscription`  
   - Corps : `{"email": "jojo@gmail.com", "mot_de_passe": "12345678", "nom": "Jojo"}`  
   - Résultat :  
     ```json
     {"message": "Inscription réussie", "utilisateur": {"id_utilisateur": 1, "email": "jojo@gmail.com", "nom": "Jojo"}}
     ```  
     Code : **201**.

2. **Connexion**  
   - Requête : `POST http://localhost:5000/connexion`  
   - Corps : `{"email": "jojo@gmail.com", "mot_de_passe": "12345678"}`  
   - Résultat :  
     ```json
     {"token": "jwt_token", "utilisateur": {"id_utilisateur": 1, "email": "jojo@gmail.com", "nom": "Jojo"}}
     ```  
     Code : **200**.

3. **Déconnexion**  
   - Requête : `POST http://localhost:5000/deconnexion`  
   - Headers : `Authorization: Bearer <jwt_token>`  
   - Résultat :  
     ```json
     {"message": "Déconnexion réussie, veuillez supprimer le token localement"}
     ```  
     Code : **200**.

4. **Profil (token valide)**  
   - Requête : `GET http://localhost:5000/profil`  
   - Headers : `Authorization: Bearer <jwt_token>`  
   - Résultat :  
     ```json
     {"utilisateur": {"id_utilisateur": 1, "email": "jojo@gmail.com", "nom": "Jojo"}}
     ```  
     Code : **200**.

5. **Profil (sans token)**  
   - Requête : `GET http://localhost:5000/profil`  
   - Résultat :  
     ```json
     {"message": "Token manquant, veuillez vous connecter"}
     ```  
     Code : **401**.

6. **Profil (token invalide)**  
   - Requête : `GET http://localhost:5000/profil`  
   - Headers : `Authorization: Bearer mauvais_token`  
   - Résultat :  
     ```json
     {"message": "Token invalide"}
     ```  
     Code : **401**.

### Tests automatisés (unitaires)
- **Fichier** : `tests/test_auth.py`  
- **Couverture** :  
  - Inscription réussie  
  - Inscription avec email existant (échec)  
  - Inscription avec email invalide (échec)  
  - Connexion réussie  
  - Connexion avec email inexistant (échec)  
  - Connexion avec mot de passe incorrect (échec)  
  - Déconnexion réussie  
  - Accès au profil avec token valide  
  - Accès au profil sans token (échec)  
  - Accès au profil avec token invalide (échec)  
- **Commande** : `python -m unittest tests/test_auth.py`  
- **Résultat** : Tous les tests passent après corrections.

---

## Leçons apprises

1. **Configuration de la base de données** : Vérifier les identifiants et créer la base avant lancement.  
2. **Modularité** : Les fichiers `__init__.py` sont essentiels pour les modules Python.  
3. **Hachage des mots de passe** : Prévoir une taille suffisante pour les champs (ex. 255 pour scrypt).  
4. **Migrations** : Utiliser `Flask-Migrate` pour un suivi reproductible.  
5. **Sécurité JWT** :  
   - Gérer les erreurs de token explicitement.  
   - Utiliser une chaîne pour `identity` dans `create_access_token()`.  
   - Régénérer les tokens après modification.  
6. **Compatibilité des dépendances** : Vérifier les versions (ex. Flask/Werkzeug).  
7. **Logging** : Configurer conditionnellement pour éviter les conflits dans les tests.  
8. **Séparation des bases** : Bases distinctes pour app et tests.  
9. **En-têtes HTTP** : Vérifier l’en-tête `Authorization` pour les routes protégées.  
10. **Débogage** : Ajouter un logging détaillé pour un diagnostic rapide.

---

## Prochaines étapes

- **Itération 2 : Gestion des recettes**  
  - **Modèles** : `Recette`, `Ingredient`, `RecetteIngredient` (relation many-to-many).  
  - **Routes** :  
    - `POST /recettes` : Créer une recette.  
    - `GET /recettes` : Lister les recettes.  
  - **Migrations** : Continuer avec `Flask-Migrate`.  
  - **Tests** : Ajouter des tests unitaires.

---

## Date de fin de l’itération
- **~~**


---

# README - Itération 2 : Gestion des recettes

## Résumé de l’itération

Cette deuxième itération a permis de mettre en place la **gestion des recettes** dans l’application.  
L’objectif principal était d’implémenter les fonctionnalités suivantes pour les utilisateurs authentifiés :  
- Créer une recette,  
- Lister les recettes,  
- Modifier une recette existante,  
- Supprimer une recette.  

Le développement a suivi une **approche agile légère**, avec des cycles courts (planification, codage, tests, validation), et a été réalisé après l’itération 1, en supposant une période du **9 au 15 mars 2025** (ajustez selon vos dates réelles).

---

## Fonctionnalités accomplies

1. **Création d’une recette**  
   - **Route** : `POST /recettes`  
   - **Fonctionnalités** :  
     - Ajout d’une recette avec un titre, une description (optionnelle) et une liste d’ingrédients.  
     - Protection via `@jwt_required()` pour limiter l’accès aux utilisateurs authentifiés.  
   - **Validations** :  
     - Titre requis et non vide,  
     - Nom des ingrédients requis.  
   - **Réponse** :  
     ```json
     {
       "message": "Recette créée avec succès",
       "recette": {
         "id_recette": 1,
         "titre": "Pâtes au pesto",
         "description": null,
         "ingredients": [{"nom": "Pâtes", "quantite": "200g"}]
       }
     }
     ```  
     Code HTTP : **201**.

2. **Liste des recettes**  
   - **Route** : `GET /recettes`  
   - **Fonctionnalités** :  
     - Retourne la liste des recettes créées par l’utilisateur connecté.  
     - Protection via `@jwt_required()`.  
   - **Réponse** :  
     ```json
     [
       {
         "id_recette": 1,
         "titre": "Pâtes au pesto",
         "description": null,
         "ingredients": [{"nom": "Pâtes", "quantite": "200g"}]
       }
     ]
     ```  
     Code HTTP : **200**.

3. **Modification d’une recette**  
   - **Route** : `PUT /recettes/<int:id>`  
   - **Fonctionnalités** :  
     - Mise à jour du titre, de la description (optionnelle) et des ingrédients d’une recette existante.  
     - Vérification que l’utilisateur est le propriétaire via `get_jwt_identity()`.  
   - **Validations** :  
     - Titre requis,  
     - Autorisation vérifiée.  
   - **Réponse** :  
     ```json
     {
       "message": "Recette mise à jour avec succès",
       "recette": {
         "id_recette": 1,
         "titre": "Pâtes au pesto revisitées",
         "description": "Une version améliorée",
         "ingredients": [{"nom": "Pesto", "quantite": "50g"}]
       }
     }
     ```  
     Code HTTP : **200**.

4. **Suppression d’une recette**  
   - **Route** : `DELETE /recettes/<int:id>`  
   - **Fonctionnalités** :  
     - Suppression d’une recette existante.  
     - Vérification de l’autorisation via `get_jwt_identity()`.  
   - **Réponse** :  
     ```json
     {"message": "Recette supprimée avec succès"}
     ```  
     Code HTTP : **200**.

5. **Modèles**  
   - **Recette** : Table `recettes` avec colonnes :  
     - `id_recette` (clé primaire),  
     - `titre`,  
     - `description` (nullable),  
     - `id_utilisateur` (clé étrangère vers `utilisateurs`).  
   - **Ingredient** : Table `ingredients` avec colonnes :  
     - `id_ingredient` (clé primaire),  
     - `nom` (unique).  
   - **RecetteIngredient** : Table de liaison `recette_ingredient` (many-to-many) avec :  
     - `id_recette`,  
     - `id_ingredient`,  
     - `quantite`.  
   - Définis dans `app/models/` : `recette.py`, `ingredient.py`, `recette_ingredient.py`.

6. **Infrastructure**  
   - Ajout des routes dans `app/routes/recettes.py` avec un Blueprint `recettes_bp`.  
   - Gestion des migrations avec `Flask-Migrate` pour les nouveaux modèles.  
   - Tests unitaires dans `tests/test_recettes.py`.

---

## Structure du projet après l’itération 2

```
flaskProject1/
├── app/
│   ├── __init__.py         # Initialisation de l'application Flask
│   ├── config.py           # Configuration (DB, clés secrètes)
│   ├── models/
│   │   ├── utilisateur.py  # Modèle Utilisateur
│   │   ├── recette.py      # Modèle Recette
│   │   ├── ingredient.py   # Modèle Ingredient
│   │   ├── recette_ingredient.py  # Modèle RecetteIngredient
│   ├── routes/
│   │   ├── auth.py         # Routes d'authentification
│   │   ├── recettes.py     # Routes pour la gestion des recettes
│   ├── utils/
│   │   ├── __init__.py     # Fichier vide pour module
│   │   └── auth_utils.py   # (Optionnel)
├── tests/
│   ├── test_auth.py        # Tests unitaires pour l'authentification
│   ├── test_recettes.py    # Tests unitaires pour les recettes
├── venv/                   # Environnement virtuel
├── migrations/             # Dossier des migrations Flask-Migrate
├── requirements.txt        # Dépendances Python
├── app.py                  # Point d'entrée de l'application
└── README.md               # Documentation (ce fichier)
```

---

## Difficultés rencontrées et solutions

### 1. Gestion des relations many-to-many
- **Problème** : Difficulté à gérer la mise à jour des ingrédients lors de la modification d’une recette.  
- **Cause** : Les anciennes relations `RecetteIngredient` n’étaient pas supprimées avant d’ajouter les nouvelles.  
- **Solution** :  
  - Suppression explicite des anciennes relations avant mise à jour :  
    ```python
    RecetteIngredient.query.filter_by(id_recette=id).delete()
    ```

### 2. Erreur 404 non gérée correctement
- **Problème** : Une requête `GET` ou `PUT` sur une recette inexistante ne renvoyait pas toujours un `404`.  
- **Cause** : Utilisation de `Recette.query.get()` sans gestion explicite.  
- **Solution** :  
  - Passage à `Recette.query.get_or_404(id)` pour lever une erreur 404 automatiquement.

### 3. Validation des ingrédients
- **Problème** : Crash si un ingrédient avait un nom vide ou manquant.  
- **Cause** : Absence de vérification avant insertion.  
- **Solution** :  
  - Ajout d’une validation dans `PUT` et `POST` :  
    ```python
    if not ingredient_nom:
        return jsonify({"message": "Le nom de l'ingrédient est requis"}), 400
    ```

### 4. Conflit de base de données dans les tests
- **Problème** : Les tests pouvaient interférer avec la base principale.  
- **Cause** : Mauvaise séparation entre `recettes_db` et `recettes_db_test`.  
- **Solution** :  
  - Configuration explicite dans `test_recettes.py` :  
    ```python
    self.app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:1234@localhost:5432/recettes_db_test"
    ```

---

## Tests effectués

### Tests manuels (via Postman)
1. **Création** :  
   - Requête : `POST /recettes`  
   - Headers : `Authorization: Bearer <token>`  
   - Corps : `{"titre": "Pâtes au pesto", "ingredients": [{"nom": "Pâtes", "quantite": "200g"}]}`  
   - Résultat : Code **201**, message "Recette créée avec succès".

2. **Liste** :  
   - Requête : `GET /recettes`  
   - Headers : `Authorization: Bearer <token>`  
   - Résultat : Code **200**, liste contenant au moins une recette.

3. **Modification** :  
   - Requête : `PUT /recettes/1`  
   - Headers : `Authorization: Bearer <token>`  
   - Corps : `{"titre": "Pâtes revisitées", "description": "Nouveau", "ingredients": [{"nom": "Pesto", "quantite": "50g"}]}`  
   - Résultat : Code **200**, message "Recette mise à jour avec succès".

4. **Suppression** :  
   - Requête : `DELETE /recettes/1`  
   - Headers : `Authorization: Bearer <token>`  
   - Résultat : Code **200**, message "Recette supprimée avec succès".

### Tests automatisés (unitaires)
- **Fichier** : `tests/test_recettes.py`  
- **Couverture** :  
  - Création réussie (`POST /recettes`)  
  - Listing des recettes (`GET /recettes`)  
  - Modification réussie (`PUT /recettes/<id>`)  
  - Suppression réussie (`DELETE /recettes/<id>`)  
- **Commande** : `python -m unittest tests/test_recettes.py`  
- **Résultat** : Tous les tests passent.

---

## Leçons apprises

1. **Gestion des relations** : Les relations many-to-many nécessitent une suppression explicite avant mise à jour.  
2. **Sécurité** : Vérifier l’identité de l’utilisateur (`get_jwt_identity()`) pour chaque action sensible.  
3. **Validation** : Toujours valider les données entrantes pour éviter des erreurs serveur.  
4. **Tests** : Séparer clairement les bases de données entre environnement de test et production.  
5. **Modularité** : Utiliser des Blueprints (`recettes_bp`) pour organiser les routes par fonctionnalité.

---

## Prochaines étapes

- **Itération 3 : Fonctionnalités avancées**  
  - Ajout de catégories pour les recettes (ex. "Végétarien", "Dessert").  
  - Recherche/filtrage des recettes par titre ou ingrédient.  
  - Routes :  
    - `GET /recettes/recherche`  
    - `POST /recettes/<id>/categorie`  
  - Tests unitaires pour les nouvelles fonctionnalités.

---

## Date de fin de l’itération
- **~~**

---



# README - Itération 3

## Objectifs de l’Itération 3
L’**Itération 3**  se concentre sur la gestion des inventaires et la génération de listes de courses, conformément au cahier des charges. Les objectifs spécifiques sont :

- Permettre aux utilisateurs de gérer leurs inventaires (création, lecture, mise à jour, suppression) et de suivre les ingrédients disponibles.
- Générer une liste de courses en comparant les ingrédients nécessaires pour une recette avec ceux disponibles dans un inventaire, incluant le calcul du coût total.
- Améliorer la robustesse avec la gestion des unités de mesure et une validation des quantités.

### Fonctionnalités principales implémentées
1. **Gestion des inventaires** :
   - Création d’un inventaire (`POST /inventaires`).
   - Liste des inventaires d’un utilisateur (`GET /inventaires`).
   - Mise à jour d’un inventaire (`PUT /inventaires/<id>`).
   - Suppression d’un inventaire (`DELETE /inventaires/<id>`).
   - Ajout d’ingrédients à un inventaire avec validation (`POST /inventaires/<id>/ingredients`).
2. **Génération de la liste de courses** :
   - Comparaison des ingrédients d’une recette avec ceux disponibles dans un inventaire, avec gestion des unités (`GET /inventaires/<id>/courses`).
   - Possibilité de spécifier une recette via un paramètre `id_recette`.
   - Calcul du coût total des ingrédients manquants.

---

## Modèles ajoutés

### Modèle `Inventaire`
- **Fichier** : `app/models/inventaire.py`
- **Description** : Représente un inventaire appartenant à un utilisateur, avec un nom et une liste d’ingrédients disponibles.
- **Champs** :
  - `id_inventaire` (Integer, clé primaire)
  - `nom` (String, obligatoire)
  - `id_utilisateur` (Integer, clé étrangère vers `utilisateurs.id_utilisateur`)
  - `ingredients` (Relation avec `InventaireIngredient`)

### Modèle `InventaireIngredient`
- **Fichier** : `app/models/inventaire_ingredient.py`
- **Description** : Table de jointure pour lier un inventaire à un ingrédient, avec la quantité disponible et le prix unitaire.
- **Champs** :
  - `id_inventaire_ingredient` (Integer, clé primaire)
  - `id_inventaire` (Integer, clé étrangère vers `inventaires.id_inventaire`)
  - `id_ingredient` (Integer, clé étrangère vers `ingredients.id_ingredient`)
  - `quantite_disponible` (String, obligatoire, ex. "150g", "2 unités")
  - `prix_unitaire` (Float, optionnel, ex. 2.50)

---

## Routes implémentées

### Blueprint `inventaires`
- **Fichier** : `app/routes/inventaires.py`
- Toutes les routes sont protégées par `jwt_required()` pour garantir l’authentification.

#### 1. `POST /inventaires`
- **Description** : Crée un nouvel inventaire pour l’utilisateur connecté.
- **Entrée** : `{"nom": "Cuisine principale"}`
- **Sortie** :
  - Succès : `201 Created`
    ```json
    {
      "message": "Inventaire créé avec succès",
      "inventaire": {
        "id_inventaire": 1,
        "nom": "Cuisine principale",
        "id_utilisateur": 1,
        "ingredients": []
      }
    }
    ```
  - Erreur : `400 Bad Request` si le nom est manquant.

#### 2. `GET /inventaires`
- **Description** : Liste tous les inventaires de l’utilisateur connecté.
- **Sortie** :
  - Succès : `200 OK`
    ```json
    {
      "inventaires": [
        {
          "id_inventaire": 1,
          "nom": "Cuisine principale",
          "id_utilisateur": 1,
          "ingredients": []
        }
      ]
    }
    ```

#### 3. `PUT /inventaires/<id>`
- **Description** : Met à jour le nom d’un inventaire existant.
- **Entrée** : `{"nom": "Cuisine mise à jour"}`
- **Sortie** :
  - Succès : `200 OK`
    ```json
    {
      "message": "Inventaire mis à jour avec succès",
      "inventaire": {
        "id_inventaire": 1,
        "nom": "Cuisine mise à jour",
        "id_utilisateur": 1,
        "ingredients": []
      }
    }
    ```
  - Erreur : `403 Forbidden` si non autorisé, `404 Not Found` si l’inventaire n’existe pas.

#### 4. `DELETE /inventaires/<id>`
- **Description** : Supprime un inventaire existant.
- **Sortie** :
  - Succès : `200 OK`
    ```json
    {
      "message": "Inventaire supprimé avec succès"
    }
    ```
  - Erreur : `403 Forbidden` si non autorisé, `404 Not Found` si l’inventaire n’existe pas.

#### 5. `POST /inventaires/<id>/ingredients`
- **Description** : Ajoute un ingrédient à un inventaire avec validation du format de `quantite_disponible`.
- **Entrée** :
  ```json
  {
    "id_ingredient": 4,
    "quantite_disponible": "150g",
    "prix_unitaire": 2.50
  }
  ```
- **Sortie** :
  - Succès : `201 Created`
    ```json
    {
      "message": "Ingrédient ajouté avec succès",
      "ingredient": {
        "id_inventaire_ingredient": 1,
        "id_inventaire": 1,
        "id_ingredient": 4,
        "nom_ingredient": "Pâtes",
        "quantite_disponible": "150g",
        "prix_unitaire": 2.50
      }
    }
    ```
  - Erreur : `400 Bad Request` si le format de `quantite_disponible` est invalide (ex. "150x"), `404 Not Found` si l’ingrédient ou l’inventaire n’existe pas, `403 Forbidden` si non autorisé.

#### 6. `GET /inventaires/<id>/courses`
- **Description** : Génère une liste de courses en comparant les ingrédients d’une recette avec ceux disponibles dans l’inventaire, avec gestion des unités et paramètre `id_recette`.
- **Paramètres** : `?id_recette=5` (optionnel, spécifie une recette).
- **Sortie** :
  - Succès : `200 OK`
    ```json
    {
      "liste_courses": [
        {
          "nom": "Pâtes",
          "quantite_manquante": "50g",
          "prix_unitaire": 2.50,
          "cout": 125.0
        }
      ],
      "total_cout": 125.0
    }
    ```
  - Erreur : `404 Not Found` si l’inventaire ou la recette n’est pas trouvée, `403 Forbidden` si non autorisé.

---

## Instructions pour tester

### Prérequis
1. **Démarrer l’application** :
   ```bash
   py app.py
   ```
   - L’application sera accessible sur `http://localhost:5000`.

2. **Obtenir un token JWT** :
   - Utilise `POST /connexion` pour obtenir un token :
     - **URL** : `http://localhost:5000/connexion`
     - **Corps** :
       ```json
       {
         "email": "jojo@gmail.com",
         "mot_de_passe": "12345678"
       }
       ```
     - **Réponse** : Un token JWT (ex. `"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."`).

3. **Créer des données de test** :
   - Crée une recette avec `POST /recettes` pour avoir des ingrédients dans la table `ingredients` (ex. "Pâtes" 200g, "Pesto" 50g).

### Tests avec Postman
1. **Créer un inventaire** :
   - **Méthode** : `POST`
   - **URL** : `http://localhost:5000/inventaires`
   - **Headers** : `Authorization: Bearer <ton_token>`
   - **Corps** :
     ```json
     {
       "nom": "Cuisine principale"
     }
     ```

2. **Lister les inventaires** :
   - **Méthode** : `GET`
   - **URL** : `http://localhost:5000/inventaires`
   - **Headers** : `Authorization: Bearer <ton_token>`

3. **Ajouter un ingrédient à l’inventaire** :
   - **Méthode** : `POST`
   - **URL** : `http://localhost:5000/inventaires/1/ingredients`
   - **Headers** : `Authorization: Bearer <ton_token>`
   - **Corps** :
     ```json
     {
       "id_ingredient": 4,
       "quantite_disponible": "150g",
       "prix_unitaire": 2.50
     }
     ```
   - Test invalide :
     ```json
     {
       "id_ingredient": 4,
       "quantite_disponible": "150x",
       "prix_unitaire": 2.50
     }
     ```

4. **Mettre à jour un inventaire** :
   - **Méthode** : `PUT`
   - **URL** : `http://localhost:5000/inventaires/1`
   - **Headers** : `Authorization: Bearer <ton_token>`
   - **Corps** :
     ```json
     {
       "nom": "Cuisine mise à jour"
     }
     ```

5. **Supprimer un inventaire** :
   - **Méthode** : `DELETE`
   - **URL** : `http://localhost:5000/inventaires/1`
   - **Headers** : `Authorization: Bearer <ton_token>`

6. **Générer une liste de courses** :
   - **Méthode** : `GET`
   - **URL** : `http://localhost:5000/inventaires/1/courses`
   - **Headers** : `Authorization: Bearer <ton_token>`
   - Avec paramètre :
     - **URL** : `http://localhost:5000/inventaires/1/courses?id_recette=5`

---

## Prochaines étapes

### Fonctionnalités à affiner
1. **Amélioration de la gestion des unités** :
   - Ajouter une validation plus stricte des conversions (ex. "1kg" vs "1000g").
   - Gérer les cas où les unités ne sont pas compatibles (ex. "g" vs "unités").
2. **Optimisation de la liste de courses** :
   - Permettre de sélectionner plusieurs recettes pour une liste de courses combinée.
   - Ajouter une option pour arrondir les quantités (ex. au kilo le plus proche).
3. **Tests unitaires** :
   - Implémenter des tests pour valider les routes (`POST`, `GET`, `PUT`, `DELETE`, etc.).
4. **Documentation supplémentaire** :
   - Ajouter des exemples de requêtes dans les commentaires des routes.

### Étapes futures (Itération 4)
- Ajouter des fonctionnalités de partage pour les inventaires ou les recettes.
- Implémenter un système de commentaires sur les recettes.
- Intégrer une interface utilisateur (frontend).

---

## Remarques
- La gestion des unités dans `GET /inventaires/<id>/courses` est fonctionnelle mais simplifiée. Une amélioration pour gérer des conversions plus complexes est recommandée.
- La validation des quantités utilise une expression régulière basique (`^\d+\s*(g|kg|cl|ml|unité?s)?$`). Elle peut être étendue pour inclure des plages ou des formats plus spécifiques.
- Les migrations doivent être appliquées avant tout test (`flask db migrate` et `flask db upgrade`).

---


### Confirmation de la portée actuelle
- **Statut de partage** : Utilisation de `publique` (True/False) au lieu d’un Enum `partage` avec "amis".
- **Fonctionnalités** : 
  - Rendre une recette publique ou privée.
  - Enregistrer une recette publique.
  - Lister les recettes enregistrées.
  - Générer une liste de courses à partir des recettes enregistrées.
  - Supprimer un enregistrement localement sans affecter la recette originale.


---


# README - Itération 4

## Objectifs de l’Itération 4
L’**Itération 4** enrichit l’application avec des fonctionnalités de partage et de gestion collaborative des recettes, en restant simple avec un système de partage binaire (public/privé). Les objectifs sont :

- Permettre aux utilisateurs de rendre leurs recettes publiques ou privées via un champ booléen `publique`.
- Donner la possibilité aux autres utilisateurs d’enregistrer une recette publique dans leur compte.
- Permettre la génération de listes de courses à partir des recettes enregistrées.
- Autoriser les utilisateurs à supprimer une recette enregistrée de leur compte sans affecter la recette originale.

### Fonctionnalités principales implémentées
1. **Gestion du partage des recettes** :
   - Les utilisateurs peuvent marquer leurs recettes comme publiques ou privées avec `publique` (True/False).
2. **Enregistrement des recettes publiques** :
   - Les utilisateurs connectés peuvent enregistrer une recette publique via une table de jointure (`RecetteUtilisateur`).
3. **Gestion des recettes enregistrées** :
   - Liste des recettes enregistrées par un utilisateur.
   - Suppression d’un enregistrement local sans impact sur la recette originale.
4. **Génération de listes de courses** :
   - Les recettes enregistrées peuvent être utilisées pour générer une liste de courses avec un inventaire.

---

## Modèles ajoutés ou modifiés

### Modèle `Recette` (mis à jour)
- **Fichier** : `app/models/recette.py`
- **Description** : Représente une recette avec un statut de partage booléen.
- **Champs mis à jour** :
  - `publique` (Boolean, défaut : `False`) : Indique si la recette est publique.
  - `utilisateurs` (Relation) : Lien vers `RecetteUtilisateur` pour suivre les enregistrements.
- **Code** :
  ```python
  from app import db

  class Recette(db.Model):
      __tablename__ = "recettes"
      id_recette = db.Column(db.Integer, primary_key=True)
      titre = db.Column(db.String(100), nullable=False)
      description = db.Column(db.Text)
      id_utilisateur = db.Column(db.Integer, db.ForeignKey("utilisateurs.id_utilisateur"), nullable=False)
      publique = db.Column(db.Boolean, default=False)
      ingredients = db.relationship("RecetteIngredient", backref="recette")
      utilisateurs = db.relationship("RecetteUtilisateur", back_populates="recette")

      def to_dict(self):
          return {
              "id_recette": self.id_recette,
              "titre": self.titre,
              "description": self.description,
              "id_utilisateur": self.id_utilisateur,
              "publique": self.publique,
              "ingredients": [i.to_dict() for i in self.ingredients]
          }
  ```

### Modèle `Utilisateur` (mis à jour)
- **Fichier** : `app/models/utilisateur.py`
- **Description** : Représente un utilisateur avec ses recettes enregistrées.
- **Champs ajoutés** :
  - `recettes_enregistrees` (Relation) : Lien vers `RecetteUtilisateur`.
- **Code** :
  ```python
  from app import db
  from werkzeug.security import generate_password_hash, check_password_hash

  class Utilisateur(db.Model):
      __tablename__ = "utilisateurs"
      id_utilisateur = db.Column(db.Integer, primary_key=True)
      email = db.Column(db.String(120), unique=True, nullable=False)
      mot_de_passe_hash = db.Column(db.String(128), nullable=False)
      recettes = db.relationship("Recette", backref="utilisateur")
      recettes_enregistrees = db.relationship("RecetteUtilisateur", back_populates="utilisateur")

      def set_password(self, mot_de_passe):
          self.mot_de_passe_hash = generate_password_hash(mot_de_passe)

      def check_password(self, mot_de_passe):
          return check_password_hash(self.mot_de_passe_hash, mot_de_passe)

      def to_dict(self):
          return {"id_utilisateur": self.id_utilisateur, "email": self.email}
  ```

### Modèle `RecetteUtilisateur` (nouveau)
- **Fichier** : `app/models/recette_utilisateur.py`
- **Description** : Table de jointure pour associer une recette enregistrée à un utilisateur.
- **Champs** :
  - `id` (Integer, clé primaire)
  - `id_recette` (Integer, clé étrangère vers `recettes.id_recette`)
  - `id_utilisateur` (Integer, clé étrangère vers `utilisateurs.id_utilisateur`)
  - `date_enregistrement` (DateTime, défaut : maintenant)
- **Code** :
  ```python
  from app import db

  class RecetteUtilisateur(db.Model):
      __tablename__ = "recette_utilisateur"
      id = db.Column(db.Integer, primary_key=True)
      id_recette = db.Column(db.Integer, db.ForeignKey("recettes.id_recette"), nullable=False)
      id_utilisateur = db.Column(db.Integer, db.ForeignKey("utilisateurs.id_utilisateur"), nullable=False)
      date_enregistrement = db.Column(db.DateTime, default=db.func.now())
      recette = db.relationship("Recette", back_populates="utilisateurs")
      utilisateur = db.relationship("Utilisateur", back_populates="recettes_enregistrees")
  ```

---

## Routes implémentées

### Blueprint `recettes` (mis à jour)
- **Fichier** : `app/routes/recettes.py`
- Toutes les routes sauf `GET /recettes/public` nécessitent un token JWT.

#### 1. `POST /recettes`
- **Description** : Crée une nouvelle recette avec un statut publique/privé.
- **Entrée** : `{"titre": "Pâtes", "publique": true, "ingredients": [{"nom": "Pâtes", "quantite": "200g"}]}`
- **Sortie** : `201 Created` avec les détails de la recette.

#### 2. `GET /recettes`
- **Description** : Liste les recettes de l’utilisateur (personnelles + enregistrées) ou publiques (avec `?public=true`).
- **Paramètres** : `?public=true` (optionnel).
- **Sortie** : `200 OK` avec une liste paginée.

#### 3. `PUT /recettes/<id>`
- **Description** : Modifie une recette, y compris son statut publique.
- **Entrée** : `{"titre": "Pâtes au pesto", "publique": true}`
- **Sortie** : `200 OK` avec la recette mise à jour.

#### 4. `DELETE /recettes/<id>`
- **Description** : Supprime une recette (propriétaire uniquement).
- **Sortie** : `200 OK` avec confirmation.

#### 5. `PUT /recettes/<id>/partager`
- **Description** : Met à jour le statut publique/privé d’une recette.
- **Entrée** : `{"publique": true}`
- **Sortie** : `200 OK` avec la recette mise à jour.

#### 6. `GET /recettes/public`
- **Description** : Liste toutes les recettes publiques (accessible sans authentification).
- **Sortie** :
  ```json
  {
    "recettes": [
      {"id_recette": 1, "titre": "Pâtes", "publique": true, ...}
    ]
  }
  ```

#### 7. `POST /recettes/<id>/enregistrer`
- **Description** : Enregistre une recette publique dans le compte de l’utilisateur.
- **Sortie** : `201 Created` avec confirmation.

#### 8. `DELETE /recettes/<id>/enregistrer`
- **Description** : Supprime une recette enregistrée du compte de l’utilisateur.
- **Sortie** : `200 OK` avec confirmation.

#### 9. `GET /recettes/enregistrées`
- **Description** : Liste les recettes enregistrées par l’utilisateur.
- **Sortie** :
  ```json
  {
    "recettes": [
      {"id_recette": 1, "titre": "Pâtes", ...}
    ]
  }
  ```

### Blueprint `inventaires` (mis à jour)
- **Fichier** : `app/routes/inventaires.py`
#### 1. `GET /inventaires/<id>/courses`
- **Description** : Génère une liste de courses à partir d’une recette (personnelle ou enregistrée).
- **Paramètres** : `?id_recette=<id>` (optionnel).
- **Sortie** : `200 OK` avec liste de courses et coût total.

---

## Instructions pour tester

### Prérequis
1. **Démarrer l’application** :
   ```bash
   py app.py
   ```
   - Accessible sur `http://localhost:5000`.

2. **Obtenir un token JWT** :
   - `POST /connexion` avec `{"email": "jojo@gmail.com", "mot_de_passe": "12345678"}`.

3. **Créer des données** :
   - Ajoute au moins deux utilisateurs et une recette via les routes existantes.

### Tests avec Postman
1. **Créer une recette publique** :
   - **Méthode** : `POST`
   - **URL** : `http://localhost:5000/recettes`
   - **Headers** : `Authorization: Bearer <token1>`
   - **Corps** : `{"titre": "Pâtes au pesto", "publique": true, "ingredients": [{"nom": "Pâtes", "quantite": "200g"}]}`
   - Attendu : `201 Created`

2. **Lister les recettes publiques** :
   - **Méthode** : `GET`
   - **URL** : `http://localhost:5000/recettes/public`
   - Attendu : Liste avec "Pâtes au pesto".

3. **Enregistrer une recette (autre utilisateur)** :
   - Connexion avec un autre compte (`POST /connexion` → `<token2>`).
   - **Méthode** : `POST`
   - **URL** : `http://localhost:5000/recettes/1/enregistrer`
   - **Headers** : `Authorization: Bearer <token2>`
   - Attendu : `201 Created`

4. **Lister les recettes enregistrées** :
   - **Méthode** : `GET`
   - **URL** : `http://localhost:5000/recettes/enregistrées`
   - **Headers** : `Authorization: Bearer <token2>`
   - Attendu : "Pâtes au pesto" dans la liste.

5. **Générer une liste de courses** :
   - **Méthode** : `GET`
   - **URL** : `http://localhost:5000/inventaires/1/courses?id_recette=1`
   - **Headers** : `Authorization: Bearer <token2>`
   - Attendu : Liste des ingrédients manquants.

6. **Supprimer une recette enregistrée** :
   - **Méthode** : `DELETE`
   - **URL** : `http://localhost:5000/recettes/1/enregistrer`
   - **Headers** : `Authorization: Bearer <token2>`
   - Attendu : `200 OK`, recette absente de `GET /recettes/enregistrées`.

7. **Vérifier l’original** :
   - **Méthode** : `GET`
   - **URL** : `http://localhost:5000/recettes/1`
   - **Headers** : `Authorization: Bearer <token1>`
   - Attendu : Recette toujours présente pour le créateur.

---

## Prochaines étapes

### Fonctionnalités à envisager
1. **Partage avancé** :
   - Ajouter un Enum `partage` ("privé", "public", "amis") avec une table `Amis` pour un contrôle plus fin.
2. **Personnalisation des recettes enregistrées** :
   - Permettre aux utilisateurs de modifier leur copie d’une recette enregistrée (nécessite une duplication).
3. **Tests unitaires** :
   - Implémenter des tests avec `pytest` pour valider les routes.

### Étapes futures (Itération 5)
- Intégrer une interface utilisateur (frontend).
- Ajouter des commentaires ou évaluations sur les recettes.
- Implémenter des statistiques (ex. recettes les plus enregistrées).

---

## Remarques
- Le système utilise `publique` (booléen) pour le partage, limitant les options à "public" ou "privé". Une extension vers "amis" est possible mais non implémentée ici.
- Les migrations doivent être appliquées après chaque modification des modèles (`flask db migrate` et `flask db upgrade`).
- La suppression dans `RecetteUtilisateur` n’affecte que l’enregistrement local, préservant l’intégrité de la recette originale.

---
