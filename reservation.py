#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de gestion des réservations
"""

import datetime
import uuid
import logging
import random

logger = logging.getLogger("HotelSim.Reservation")

class ReservationRequest:
    """Représente une demande de réservation par un client"""
    
    def __init__(self, check_in_date, check_out_date, guests, max_budget, preferred_room_type=None):
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.guests = guests
        self.max_budget = max_budget  # Budget maximal par nuit
        self.preferred_room_type = preferred_room_type
        self.request_id = str(uuid.uuid4())[:8]  # Identifiant unique pour la demande
        
        # Validation des dates
        if check_in_date >= check_out_date:
            raise ValueError("La date d'arrivée doit être antérieure à la date de départ")
        
        # Validation du nombre de personnes
        if guests < 1:
            raise ValueError("Le nombre de personnes doit être au moins 1")
    
    def get_stay_duration(self):
        """Retourne la durée du séjour en nombre de nuits"""
        return (self.check_out_date - self.check_in_date).days
    
    def can_afford(self, price_per_night):
        """Vérifie si le client peut se permettre le prix proposé"""
        return price_per_night <= self.max_budget
    
    def __str__(self):
        room_pref = f" ({self.preferred_room_type})" if self.preferred_room_type else ""
        return (f"Demande {self.request_id}: {self.guests} pers. du {self.check_in_date} au {self.check_out_date}"
                f" - Budget max: {self.max_budget}€/nuit{room_pref}")


class Reservation:
    """Représente une réservation confirmée"""
    
    def __init__(self, request, room=None, price_per_night=0):
        self.request_id = request.request_id
        self.reservation_id = str(uuid.uuid4())[:8]
        self.check_in_date = request.check_in_date
        self.check_out_date = request.check_out_date
        self.guests = request.guests
        self.preferred_room_type = request.preferred_room_type
        self.room = room  # Sera défini lors de l'attribution d'une chambre
        self.price_per_night = price_per_night
        self.total_price = price_per_night * request.get_stay_duration()
        self.creation_date = datetime.datetime.now()
        self.status = "confirmed"  # 'confirmed', 'cancelled', 'completed'
        
        logger.info(f"Création de la réservation {self.reservation_id} pour {self.guests} personne(s) "
                   f"du {self.check_in_date} au {self.check_out_date} à {self.price_per_night}€/nuit")
    
    def cancel(self):
        """Annule la réservation"""
        self.status = "cancelled"
        logger.info(f"Annulation de la réservation {self.reservation_id}")
        return True
    
    def complete(self):
        """Marque la réservation comme terminée"""
        if datetime.date.today() >= self.check_out_date:
            self.status = "completed"
            logger.info(f"Réservation {self.reservation_id} terminée")
            return True
        return False
    
    def get_stay_duration(self):
        """Retourne la durée du séjour en nombre de nuits"""
        return (self.check_out_date - self.check_in_date).days
    
    def __str__(self):
        room_info = f", Chambre {self.room.id}" if self.room else ""
        return (f"Réservation {self.reservation_id}: {self.guests} pers. du {self.check_in_date} au {self.check_out_date}"
                f"{room_info} - {self.price_per_night}€/nuit ({self.total_price}€ total) - {self.status}")


class ReservationGenerator:
    """Générateur de demandes de réservation aléatoires"""
    
    def __init__(self, config, weather_api=None):
        self.config = config
        self.weather_api = weather_api
        self.room_types = list(config['hotel']['room_types'].keys())
        random.seed(config['simulation']['random_seed'])
        
        # Facteurs d'influence pour la génération de demandes
        self.season_influence = {
            "high": {"demand_multiplier": 1.5, "budget_multiplier": 1.2},
            "medium": {"demand_multiplier": 1.0, "budget_multiplier": 1.0},
            "low": {"demand_multiplier": 0.7, "budget_multiplier": 0.8}
        }
        
        # Préférences de durée de séjour
        self.stay_duration_weights = {
            1: 10,  # 1 nuit: 10% des cas
            2: 30,  # 2 nuits: 30% des cas
            3: 25,  # 3 nuits: 25% des cas
            4: 15,  # 4 nuits: 15% des cas
            5: 10,  # 5 nuits: 10% des cas
            6: 5,   # 6 nuits: 5% des cas
            7: 5    # 7 nuits: 5% des cas
        }
        
        logger.info("Générateur de réservations initialisé")
    
    def get_current_season(self, date):
        """Détermine la saison en fonction de la date"""
        date_str = date.strftime("%m-%d")
        
        for season_name, periods in self.config['pricing']['seasons'].items():
            for period in periods:
                start = period["start"]
                end = period["end"]
                
                # Gestion du cas où la période chevauche l'année (par ex. 12-15 au 01-05)
                if start > end:
                    if date_str >= start or date_str <= end:
                        return season_name
                else:
                    if start <= date_str <= end:
                        return season_name
        
        # Par défaut, saison moyenne
        return "medium"
    
    def get_random_stay_duration(self):
        """Retourne une durée de séjour aléatoire selon les poids définis"""
        durations = list(self.stay_duration_weights.keys())
        weights = list(self.stay_duration_weights.values())
        return random.choices(durations, weights=weights, k=1)[0]
    
    def generate_request(self, date):
        """Génère une demande de réservation aléatoire pour la date donnée"""
        # Détermination de la saison et de ses influences
        season = self.get_current_season(date)
        influence = self.season_influence[season]
        
        # Influence météo si disponible
        weather_factor = 1.0
        if self.weather_api:
            # Hypothétique fonction pour obtenir la météo et son influence
            weather_factor = self.weather_api.get_demand_factor(date)
        
        # Calcul du facteur global d'influence
        demand_factor = influence["demand_multiplier"] * weather_factor
        budget_factor = influence["budget_multiplier"] * weather_factor
        
        # Détermination des détails de la demande
        check_in_date = date + datetime.timedelta(days=random.randint(1, 30))
        stay_duration = self.get_random_stay_duration()
        check_out_date = check_in_date + datetime.timedelta(days=stay_duration)
        
        # Nombre de personnes
        persons_weights = [5, 40, 30, 20, 5]  # Pour 1, 2, 3, 4, 5 personnes
        guests = random.choices(range(1, 6), weights=persons_weights, k=1)[0]
        
        # Type de chambre préféré
        if random.random() < 0.7:  # 70% des clients ont une préférence
            # Attribution intelligente du type préféré en fonction du nombre de personnes
            if guests == 1:
                preferred_room_type = random.choices(self.room_types, weights=[70, 25, 5], k=1)[0]
            elif guests == 2:
                preferred_room_type = random.choices(self.room_types, weights=[60, 30, 10], k=1)[0]
            elif guests == 3:
                preferred_room_type = random.choices(self.room_types, weights=[10, 70, 20], k=1)[0]
            else:  # 4 ou 5 personnes
                preferred_room_type = random.choices(self.room_types, weights=[0, 30, 70], k=1)[0]
        else:
            preferred_room_type = None
        
        # Budget maximum par nuit
        # Base sur le prix du type de chambre préféré ou moyen
        if preferred_room_type:
            base_price = self.config['pricing']['base_rates'][preferred_room_type]
        else:
            base_prices = list(self.config['pricing']['base_rates'].values())
            base_price = sum(base_prices) / len(base_prices)
        
        # Ajout d'une variation aléatoire au budget
        budget_variation = random.uniform(0.8, 1.5)
        max_budget = base_price * budget_variation * budget_factor
        
        # Création de la demande
        try:
            request = ReservationRequest(
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                guests=guests,
                max_budget=max_budget,
                preferred_room_type=preferred_room_type
            )
            logger.debug(f"Demande générée: {request}")
            return request
        except ValueError as e:
            logger.error(f"Erreur lors de la génération de la demande: {e}")
            return None
    
    def generate_batch(self, date, count):
        """Génère un lot de demandes de réservation pour la date donnée"""
        requests = []
        
        for _ in range(count):
            request = self.generate_request(date)
            if request:
                requests.append(request)
        
        logger.info(f"Généré {len(requests)} demandes de réservation pour le {date}")
        return requests 