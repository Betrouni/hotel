#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'intégration avec l'API météo
"""

import requests
import datetime
import logging
import random
import json
from pathlib import Path

logger = logging.getLogger("HotelSim.WeatherAPI")

class WeatherAPI:
    """Interface avec une API météo externe ou simulation de données météo"""
    
    def __init__(self, config, use_real_api=False):
        self.config = config
        self.use_real_api = use_real_api
        self.api_key = config['weather'].get('api_key', '')
        self.location = config['weather'].get('location', 'Paris,FR')
        self.impact_factors = config['weather'].get('impact_factors', {
            "sunny": 1.2,
            "cloudy": 1.0,
            "rainy": 0.8,
            "snowy": 0.7
        })
        self.weather_cache = {}  # Cache des données météo pour éviter les appels API répétés
        
        # Option pour charger/sauvegarder des données météo simulées
        self.cache_file = Path('./data/weather_cache.json')
        
        logger.info(f"WeatherAPI initialisée pour {self.location}")
        
        # Charger le cache si disponible
        self._load_cache()
    
    def get_weather(self, date):
        """Obtient les données météo pour une date donnée"""
        # Convertir en chaîne de caractères pour utilisation comme clé
        date_str = date.isoformat()
        
        # Vérifier si les données sont déjà en cache
        if date_str in self.weather_cache:
            return self.weather_cache[date_str]
        
        # Si on utilise l'API réelle et que la date est dans le futur proche (prévisions)
        if self.use_real_api and (date - datetime.date.today()).days < 10:
            weather_data = self._get_real_weather(date)
        else:
            # Simuler des données météo pour des dates lointaines
            weather_data = self._simulate_weather(date)
        
        # Mettre en cache
        self.weather_cache[date_str] = weather_data
        
        # Sauvegarder le cache périodiquement
        if len(self.weather_cache) % 30 == 0:
            self._save_cache()
        
        return weather_data
    
    def get_demand_factor(self, date):
        """Détermine l'influence de la météo sur la demande"""
        weather_data = self.get_weather(date)
        condition = weather_data.get('condition', 'cloudy')
        
        # Impact standard si la condition n'est pas dans les facteurs
        return self.impact_factors.get(condition, 1.0)
    
    def _get_real_weather(self, date):
        """Obtient les données météo réelles depuis l'API"""
        if not self.api_key:
            logger.warning("Clé API manquante, utilisation de données simulées")
            return self._simulate_weather(date)
        
        try:
            # Exemple d'appel à l'API OpenWeatherMap
            # Remplacer par l'API de votre choix
            days = (date - datetime.date.today()).days
            
            if days < 0:
                # Données historiques
                url = f"https://api.openweathermap.org/data/2.5/onecall/timemachine"
                params = {
                    "lat": 48.8566,  # Paris (à remplacer par géolocalisation de self.location)
                    "lon": 2.3522,
                    "dt": int(datetime.datetime.combine(date, datetime.time()).timestamp()),
                    "appid": self.api_key,
                    "units": "metric"
                }
            else:
                # Prévisions
                url = f"https://api.openweathermap.org/data/2.5/onecall"
                params = {
                    "lat": 48.8566,  # Paris
                    "lon": 2.3522,
                    "exclude": "current,minutely,hourly,alerts",
                    "appid": self.api_key,
                    "units": "metric"
                }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Traitement des données API pour les formater
            if days < 0:
                weather_condition = data['current']['weather'][0]['main'].lower()
                temperature = data['current']['temp']
            else:
                daily_data = data['daily'][min(days, 7)]  # Max 7 jours de prévisions
                weather_condition = daily_data['weather'][0]['main'].lower()
                temperature = daily_data['temp']['day']
            
            # Mapper la condition dans l'un de nos types standards
            condition = self._map_weather_condition(weather_condition)
            
            weather_data = {
                "temperature": temperature,
                "condition": condition,
                "demand_impact": self.impact_factors.get(condition, 1.0)
            }
            
            logger.debug(f"Données météo réelles obtenues pour {date}: {condition}, {temperature}°C")
            return weather_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à l'API météo: {e}")
            return self._simulate_weather(date)
    
    def _simulate_weather(self, date):
        """Simule des données météo pour une date"""
        # Détermination de la saison
        month = date.month
        
        # Probabilités de conditions météo par saison
        if month in [12, 1, 2]:  # Hiver
            conditions = ["sunny", "cloudy", "rainy", "snowy"]
            probabilities = [0.2, 0.3, 0.3, 0.2]
            temp_range = (-5, 10)
        elif month in [3, 4, 5]:  # Printemps
            conditions = ["sunny", "cloudy", "rainy", "snowy"]
            probabilities = [0.4, 0.3, 0.25, 0.05]
            temp_range = (5, 20)
        elif month in [6, 7, 8]:  # Été
            conditions = ["sunny", "cloudy", "rainy", "snowy"]
            probabilities = [0.6, 0.25, 0.15, 0]
            temp_range = (15, 30)
        else:  # Automne
            conditions = ["sunny", "cloudy", "rainy", "snowy"]
            probabilities = [0.3, 0.4, 0.29, 0.01]
            temp_range = (5, 20)
        
        # Génération aléatoire pondérée par les probabilités
        condition = random.choices(conditions, weights=probabilities, k=1)[0]
        temperature = round(random.uniform(*temp_range), 1)
        
        weather_data = {
            "temperature": temperature,
            "condition": condition,
            "demand_impact": self.impact_factors.get(condition, 1.0)
        }
        
        logger.debug(f"Données météo simulées pour {date}: {condition}, {temperature}°C")
        return weather_data
    
    def _map_weather_condition(self, api_condition):
        """Convertit une condition météo de l'API en un format standard"""
        # Mapping pour OpenWeatherMap (à adapter selon l'API)
        condition_mapping = {
            "clear": "sunny",
            "clouds": "cloudy",
            "rain": "rainy",
            "drizzle": "rainy",
            "thunderstorm": "rainy",
            "snow": "snowy",
            "mist": "cloudy",
            "fog": "cloudy"
        }
        
        # Conversion en minuscules pour la correspondance
        api_condition = api_condition.lower()
        
        for key, value in condition_mapping.items():
            if key in api_condition:
                return value
        
        # Par défaut
        return "cloudy"
    
    def _save_cache(self):
        """Sauvegarde le cache des données météo"""
        try:
            # Création du répertoire si nécessaire
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.weather_cache, f, indent=2)
            
            logger.debug(f"Cache météo sauvegardé ({len(self.weather_cache)} entrées)")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du cache météo: {e}")
    
    def _load_cache(self):
        """Charge le cache des données météo"""
        if not self.cache_file.exists():
            logger.debug("Pas de cache météo existant")
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                self.weather_cache = json.load(f)
            
            logger.debug(f"Cache météo chargé ({len(self.weather_cache)} entrées)")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du cache météo: {e}")
            self.weather_cache = {} 