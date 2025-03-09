# HotelSim - Simulateur de Gestion Hôtelière

HotelSim est un simulateur de gestion des réservations d'un petit hôtel avec tarification dynamique. Ce projet vise à optimiser le taux d'occupation et les revenus en ajustant automatiquement les prix en fonction de la demande.

## Fonctionnalités

### 🏨 Simulation de l'hôtel "Le Petit Refuge"
- 15 chambres de différents types (Standard, Confort, Suite)
- Gestion des réservations
- Calcul du taux d'occupation et des revenus

### 💰 Tarification dynamique (Yield Management)
- Ajustement automatique des prix en fonction de l'occupation
- Gestion des saisons touristiques (haute, moyenne, basse)
- Réductions pour les réservations anticipées
- Optimisation du revenu par chambre

### 📊 Analyse et exportation de données
- Exportation des données de réservations, occupation et revenus
- Formats CSV et JSON
- Analyses de performance
- Suggestions d'ajustement de prix

### 🌤️ Intégration météo (optionnelle)
- Influence de la météo sur la demande
- Ajustement de prix en fonction des conditions climatiques

## Structure du Projet

```
hotel/
├── main.py               # Point d'entrée du simulateur
├── config.json           # Configuration du simulateur
├── hotel.py              # Classes pour l'hôtel et les chambres
├── reservation.py        # Gestion des réservations et demandes
├── revenue_manager.py    # Tarification dynamique 
├── data_exporter.py      # Export des données
├── simulator.py          # Orchestration de la simulation
├── data/                 # Dossier pour les données exportées
└── README.md             # Documentation du projet
```

## Installation

1. Clonez ce dépôt
```bash
git clone https://github.com/votre-utilisateur/hotel-sim.git
cd hotel-sim
```

2. Installez les dépendances
```bash
pip install -r requirements.txt
```

## Utilisation

### Lancer une simulation

Pour lancer une simulation avec les paramètres par défaut :

```bash
python main.py
```

### Configuration

Vous pouvez modifier le fichier `config.json` pour ajuster :

- Les caractéristiques de l'hôtel (nombre et types de chambres)
- Les prix de base
- Les seuils d'occupation pour ajustement des prix
- Les périodes de saison haute/basse
- La durée de simulation
- Les formats d'exportation de données

### Analyser les résultats

Les résultats sont exportés dans le dossier `data/` avec des fichiers contenant :
- Les réservations
- Les taux d'occupation
- Les revenus générés
- Les suggestions d'ajustement de prix

## Extensions possibles

1. **Interface utilisateur web** : Création d'un tableau de bord dynamique pour visualiser les résultats en temps réel
2. **API météo** : Intégration d'une API météo réelle pour influencer la demande de manière réaliste
3. **Profils clients** : Ajout de profils de clients avec des comportements distincts
4. **Concurrence** : Simulation d'hôtels concurrents avec leurs propres stratégies de prix
5. **Événements spéciaux** : Gestion d'événements locaux influençant la demande

## Intégration à Google Sheets

Pour intégrer les données à Google Sheets et créer un dashboard:

1. Exportez les données au format CSV
2. Importez-les dans Google Sheets
3. Créez des graphiques et tableaux de bord
4. (Optionnel) Utilisez Google Apps Script pour automatiser l'importation

## Recommandations pour le Yield Management

Le système suggère des ajustements de prix basés sur plusieurs facteurs:

- Si l'occupation dépasse 80%, une augmentation de prix est recommandée
- Si l'occupation est inférieure à 50%, une réduction est suggérée
- Les prix sont également ajustés en fonction de la saison touristique

---
