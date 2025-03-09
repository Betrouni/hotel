#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour lancer une simulation hôtelière et générer un tableau de bord
"""

import os
import sys
import json
import logging
import argparse
import datetime
from pathlib import Path

from hotel import Hotel
from reservation import ReservationGenerator
from revenue_manager import RevenueManager
from data_exporter import DataExporter
from simulator import Simulator
from dashboard import Dashboard

try:
    from weather_api import WeatherAPI
    WEATHER_API_AVAILABLE = True
except ImportError:
    WEATHER_API_AVAILABLE = False

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simulation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HotelSim.Runner")

def load_config(config_path):
    """Charge la configuration depuis un fichier JSON"""
    try:
        with open(config_path, 'r', encoding='utf-8') as config_file:
            config = json.load(config_file)
            logger.info(f"Configuration chargée depuis {config_path}")
            return config
    except FileNotFoundError:
        logger.error(f"Fichier de configuration {config_path} non trouvé")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Erreur de format JSON dans le fichier {config_path}")
        sys.exit(1)

def setup_directories(config):
    """Configure les répertoires nécessaires"""
    data_path = Path(config['data']['export_path'])
    dashboard_path = Path('./dashboard')
    
    # Création des répertoires s'ils n'existent pas
    data_path.mkdir(parents=True, exist_ok=True)
    dashboard_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Répertoires configurés: données={data_path}, dashboard={dashboard_path}")
    return data_path, dashboard_path

def run_simulation(config, use_weather_api=False):
    """Exécute la simulation complète"""
    logger.info("Initialisation de la simulation...")
    
    # Initialisation de l'hôtel
    hotel = Hotel(
        name=config['hotel']['name'],
        room_types=config['hotel']['room_types']
    )
    
    # Initialisation du gestionnaire de revenus
    revenue_manager = RevenueManager(
        base_rates=config['pricing']['base_rates'],
        occupancy_thresholds=config['pricing']['occupancy_thresholds'],
        price_multipliers=config['pricing']['price_multipliers'],
        seasons=config['pricing']['seasons']
    )
    
    # Initialisation de l'exportateur de données
    data_exporter = DataExporter(
        export_path=config['data']['export_path'],
        export_format=config['data']['format']
    )
    
    # Initialisation de l'API météo si disponible
    weather_api = None
    if WEATHER_API_AVAILABLE and use_weather_api:
        weather_api = WeatherAPI(config, use_real_api=False)  # Simulation de météo
        logger.info("API météo initialisée (simulation)")
    
    # Création du simulateur
    simulator = Simulator(
        hotel=hotel,
        revenue_manager=revenue_manager,
        data_exporter=data_exporter,
        simulation_days=config['simulation']['days'],
        requests_per_day=config['simulation']['requests_per_day'],
        weather_api=weather_api
    )
    
    # Lancement de la simulation
    logger.info("Lancement de la simulation...")
    start_time = datetime.datetime.now()
    
    result = simulator.run(config)
    
    end_time = datetime.datetime.now()
    duration = end_time - start_time
    
    # Affichage des résultats
    logger.info(f"Simulation terminée en {duration.total_seconds():.2f} secondes")
    logger.info(f"Réservations totales: {result['total_reservations']}")
    logger.info(f"Revenu total: {result['total_revenue']:.2f}€")
    logger.info(f"Taux d'occupation moyen: {result['average_occupancy']:.1%}")
    
    return result

def generate_dashboard(data_path, dashboard_path):
    """Génère le tableau de bord à partir des données de simulation"""
    logger.info("Génération du tableau de bord...")
    
    dashboard = Dashboard(data_path, dashboard_path)
    dashboard_path = dashboard.generate_all()
    
    if dashboard_path:
        logger.info(f"Tableau de bord généré avec succès: {dashboard_path}")
        return dashboard_path
    else:
        logger.error("Erreur lors de la génération du tableau de bord")
        return None

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Lancement d\'une simulation hôtelière')
    parser.add_argument('--config', default='config.json', help='Chemin vers le fichier de configuration')
    parser.add_argument('--weather', action='store_true', help='Utiliser la simulation météo')
    parser.add_argument('--dashboard', action='store_true', help='Générer le tableau de bord après la simulation')
    
    args = parser.parse_args()
    
    logger.info(f"Démarrage du programme avec config={args.config}, weather={args.weather}, dashboard={args.dashboard}")
    
    # Chargement de la configuration
    config = load_config(args.config)
    
    # Configuration des répertoires
    data_path, dashboard_path = setup_directories(config)
    
    # Exécution de la simulation
    result = run_simulation(config, use_weather_api=args.weather)
    
    # Génération du tableau de bord si demandé
    if args.dashboard:
        dashboard_file = generate_dashboard(data_path, dashboard_path)
        if dashboard_file:
            print(f"\nTableau de bord disponible à l'adresse: {dashboard_file}")
    
    # Affichage du résumé de la simulation
    print("\n" + "="*50)
    print(f"RÉSUMÉ DE LA SIMULATION - {config['hotel']['name']}")
    print("="*50)
    print(f"Période: {config['simulation']['days']} jours")
    print(f"Réservations: {result['total_reservations']}")
    print(f"Revenu total: {result['total_revenue']:.2f}€")
    print(f"Revenu moyen par jour: {result['total_revenue']/config['simulation']['days']:.2f}€/jour")
    print(f"Taux d'occupation moyen: {result['average_occupancy']:.1%}")
    print("="*50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 