# GTFS-RT Reader

Ce script Python permet de lire et d'interpréter des fichiers au format GTFS-RT (General Transit Feed Specification - Real Time) avec l'extension .pb.

## Prérequis

Pour exécuter ce script, vous aurez besoin de Python 3.6+ et des bibliothèques suivantes :

```
gtfs-realtime-bindings>=1.0.0
protobuf>=3.20.0
pandas>=1.3.0
matplotlib>=3.5.0
```

Vous pouvez installer ces dépendances en utilisant le fichier `requirements.txt` :

```bash
pip install -r requirements.txt
```

## Utilisation

Le script est configuré pour lire trois types de fichiers GTFS-RT :
- `TripUpdate.pb` : Mises à jour des trajets (retards, annulations, etc.)
- `VehiclePosition.pb` : Positions des véhicules en temps réel
- `Alert.pb` : Alertes et notifications

Pour exécuter le script :

```bash
python gtfs_rt_reader.py
```

## Fonctionnalités

Le script effectue les opérations suivantes :

1. Lecture des fichiers GTFS-RT (.pb)
2. Affichage des informations de base sur chaque flux
3. Analyse des mises à jour de trajets (retards moyens, distribution des retards)
4. Analyse des positions des véhicules (vitesse moyenne, positions géographiques)
5. Analyse des alertes (cause, effet, entités concernées)
6. Génération de graphiques (distribution des retards, positions des véhicules)
7. Export des données au format CSV

## Résultats

Le script génère les fichiers suivants :
- `trip_updates.csv` : Données sur les mises à jour des trajets
- `vehicle_positions.csv` : Données sur les positions des véhicules
- `delay_distribution.png` : Graphique de la distribution des retards
- `vehicle_positions.png` : Carte des positions des véhicules

## Structure du code

- `read_gtfs_rt_file()` : Lit un fichier GTFS-RT et renvoie le message d'alimentation analysé
- `convert_to_dict()` : Convertit un message GTFS-RT en dictionnaire Python
- `print_feed_info()` : Affiche les informations de base sur le flux
- `analyze_trip_updates()` : Analyse les mises à jour des trajets
- `analyze_vehicle_positions()` : Analyse les positions des véhicules
- `analyze_alerts()` : Analyse les alertes
- `main()` : Fonction principale qui orchestre l'exécution du script
