#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HotelSim - Simulateur de Gestion Hôtelière
Un outil de simulation pour l'optimisation des réservations et du pricing dynamique
"""

import datetime
import json
import random
import logging
from hotel import Hotel
from reservation import Reservation, ReservationRequest
from revenue_manager import RevenueManager
from data_exporter import DataExporter
from simulator import Simulator

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hotel_sim.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HotelSim")

def main():
    """Point d'entrée principal du simulateur"""
    logger.info("Démarrage du simulateur HotelSim")
    
    # Chargement de la configuration
    try:
        with open('config.json', 'r', encoding='utf-8') as config_file:
            config = json.load(config_file)
            logger.info("Configuration chargée avec succès")
    except FileNotFoundError:
        logger.error("Fichier de configuration non trouvé. Utilisation des valeurs par défaut.")
        config = create_default_config()
        save_config(config)
    
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
    
    # Création du simulateur
    simulator = Simulator(
        hotel=hotel,
        revenue_manager=revenue_manager,
        data_exporter=data_exporter,
        simulation_days=config['simulation']['days'],
        requests_per_day=config['simulation']['requests_per_day']
    )
    
    # Lancement de la simulation
    simulator.run()
    
    logger.info("Simulation terminée avec succès")

def create_default_config():
    """Crée une configuration par défaut"""
    today = datetime.date.today()
    
    config = {
        "hotel": {
            "name": "Le Petit Refuge",
            "room_types": {
                "standard": {"count": 5, "capacity": 2},
                "confort": {"count": 7, "capacity": 3},
                "suite": {"count": 3, "capacity": 4}
            }
        },
        "pricing": {
            "base_rates": {
                "standard": 80,
                "confort": 120,
                "suite": 180
            },
            "occupancy_thresholds": [0.3, 0.5, 0.8, 0.9],
            "price_multipliers": [0.8, 0.9, 1.1, 1.25],
            "seasons": {
                "high": [
                    {"start": "06-15", "end": "09-15"},
                    {"start": "12-15", "end": "01-05"}
                ],
                "medium": [
                    {"start": "04-01", "end": "06-14"},
                    {"start": "09-16", "end": "10-31"}
                ],
                "low": [
                    {"start": "01-06", "end": "03-31"},
                    {"start": "11-01", "end": "12-14"}
                ]
            }
        },
        "simulation": {
            "start_date": today.strftime("%Y-%m-%d"),
            "days": 90,
            "requests_per_day": 15,
            "random_seed": 42
        },
        "data": {
            "export_path": "./data/",
            "format": "csv"
        }
    }
    
    return config

def save_config(config):
    """Sauvegarde la configuration dans un fichier JSON"""
    try:
        with open('config.json', 'w', encoding='utf-8') as config_file:
            json.dump(config, config_file, indent=4)
        logger.info("Configuration par défaut créée et sauvegardée")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")

if __name__ == "__main__":
    main() 