# GTFS-RT Viewer

Une application web pour visualiser, analyser et explorer les données GTFS-RT (General Transit Feed Specification - Real Time) à partir de fichiers .pb ou d'URLs en direct.

## Fonctionnalités

- Lecture et analyse de fichiers GTFS-RT (.pb)
- Support pour les trois types de flux GTFS-RT :
  - Mises à jour des trajets (Trip Updates)
  - Positions des véhicules (Vehicle Positions)
  - Alertes (Alerts)
- Visualisation interactive avec tableau de bord
- Affichage des positions des véhicules sur une carte
- Analyse statistique des retards
- Export des données au format CSV
- Configuration de sources multiples (fichiers locaux ou URLs)
- Interface utilisateur responsive et moderne

## Prérequis

Pour exécuter cette application, vous aurez besoin de Python 3.6+ et des bibliothèques suivantes :

```bash
gtfs-realtime-bindings>=1.0.0
protobuf>=3.20.0
pandas>=1.3.0
matplotlib>=3.5.0
flask>=2.0.0
flask-cors>=3.0.10
requests>=2.28.0
```

Vous pouvez installer ces dépendances en utilisant le fichier `requirements.txt` :

```bash
pip install -r requirements.txt
```

## Installation

1. Clonez ce dépôt :

   ```bash
   git clone https://github.com/your-username/gtfs-viewer.git
   cd gtfs-viewer
   ```

2. Installez les dépendances :

   ```bash
   pip install -r requirements.txt
   ```

3. Lancez l'application :

   ```bash
   python main.py
   ```

4. Ouvrez votre navigateur à l'adresse `http://localhost:5000`

## Structure du Projet

Le projet suit une structure organisée par fonctionnalité :

```markdown
gtfs-viewer/
├── app/                      # Code de l'application
│   ├── api/                  # Points d'entrée API
│   ├── core/                 # Fonctionnalités principales
│   ├── utils/                # Utilitaires
│   └── web/                  # Interface web
├── config/                   # Configuration
├── data/                     # Données
│   ├── gtfs/                 # Données GTFS statiques
│   └── gtfs_rt/              # Fichiers GTFS-RT
├── docs/                     # Documentation
├── output/                   # Fichiers générés
│   ├── charts/               # Graphiques
│   └── csv/                  # Exports CSV
├── static/                   # Ressources statiques
├── templates/                # Templates HTML
└── tests/                    # Tests
```

Consultez le fichier `docs/DEVBOOK.md` pour plus de détails sur la structure et l'organisation du projet.

## Développement

Pour contribuer au projet, veuillez consulter le fichier `docs/DEVBOOK.md` qui contient les lignes directrices de développement et le journal des activités.

## Tests

Exécutez les tests avec pytest :

```bash
python -m pytest tests/
```

## Licence

[À définir selon vos besoins]
