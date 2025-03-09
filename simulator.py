#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de simulation de l'activité hôtelière
"""

import logging
import datetime
import random
from time import sleep
from reservation import Reservation, ReservationGenerator

logger = logging.getLogger("HotelSim.Simulator")

class Simulator:
    """Simulateur de gestion hôtelière"""
    
    def __init__(self, hotel, revenue_manager, data_exporter, 
                 simulation_days=90, requests_per_day=15, weather_api=None):
        self.hotel = hotel
        self.revenue_manager = revenue_manager
        self.data_exporter = data_exporter
        self.simulation_days = simulation_days
        self.requests_per_day = requests_per_day
        self.weather_api = weather_api
        self.all_reservations = []
        self.start_date = datetime.date.today()
        
        logger.info(f"Simulateur initialisé pour {simulation_days} jours avec {requests_per_day} demandes/jour")
    
    def run(self, config=None):
        """Exécute la simulation complète"""
        logger.info("Démarrage de la simulation")
        
        # Si une configuration est fournie, l'utiliser
        if config:
            self.simulation_days = config.get('simulation', {}).get('days', self.simulation_days)
            self.requests_per_day = config.get('simulation', {}).get('requests_per_day', self.requests_per_day)
            if 'start_date' in config.get('simulation', {}):
                self.start_date = datetime.datetime.strptime(
                    config['simulation']['start_date'], "%Y-%m-%d"
                ).date()
        
        # Création du générateur de réservation
        reservation_generator = ReservationGenerator(config, self.weather_api)
        
        # Exécution de la simulation jour par jour
        for day in range(self.simulation_days):
            current_date = self.start_date + datetime.timedelta(days=day)
            logger.info(f"Simulation du jour {day+1}/{self.simulation_days} ({current_date})")
            
            # Génération des demandes du jour
            daily_requests = reservation_generator.generate_batch(current_date, self.requests_per_day)
            
            # Traitement des demandes
            self.process_daily_requests(daily_requests, current_date)
            
            # Export périodique des données (tous les 30 jours)
            if (day + 1) % 30 == 0 or day == self.simulation_days - 1:
                self.export_simulation_data(current_date)
                
                # Analyse et suggestions de prix
                suggestions = self.revenue_manager.suggest_price_adjustments(
                    self.hotel, 
                    current_date - datetime.timedelta(days=30),
                    days=30
                )
                
                # Export des suggestions
                self.data_exporter.export_price_suggestions(suggestions, f"price_suggestions_{current_date.isoformat()}")
                
                logger.info(f"Données exportées pour le jour {day+1}")
        
        logger.info("Simulation terminée")
        return {
            "total_reservations": len(self.all_reservations),
            "total_revenue": sum(r.total_price for r in self.all_reservations),
            "average_occupancy": self.calculate_average_occupancy(),
            "reservations": self.all_reservations
        }
    
    def process_daily_requests(self, requests, current_date):
        """Traite les demandes de réservation du jour"""
        accepted = 0
        rejected = 0
        
        for request in requests:
            # Détermination du prix optimal
            price_per_night, _ = self.revenue_manager.optimize_price_for_request(
                request, self.hotel, current_date
            )
            
            if price_per_night is None:
                logger.debug(f"Demande {request.request_id} rejetée: pas de chambre disponible ou tarif trop élevé")
                rejected += 1
                continue
            
            # Vérification si le client accepte le prix
            if not request.can_afford(price_per_night):
                logger.debug(f"Demande {request.request_id} rejetée: prix trop élevé ({price_per_night}€)")
                rejected += 1
                continue
            
            # Création de la réservation
            reservation = Reservation(request, price_per_night=price_per_night)
            
            # Attribution d'une chambre
            booked_room = self.hotel.book_room(reservation)
            
            if booked_room:
                self.all_reservations.append(reservation)
                accepted += 1
                logger.debug(f"Réservation {reservation.reservation_id} confirmée: {booked_room}")
            else:
                rejected += 1
                logger.debug(f"Réservation {reservation.reservation_id} rejetée: pas de chambre disponible")
        
        total = accepted + rejected
        acceptance_rate = accepted / total if total > 0 else 0
        logger.info(f"Jour {current_date}: {accepted}/{total} réservations acceptées ({acceptance_rate:.1%})")
    
    def calculate_average_occupancy(self):
        """Calcule le taux d'occupation moyen sur toute la période de simulation"""
        occupancy_sum = 0
        
        for day in range(self.simulation_days):
            current_date = self.start_date + datetime.timedelta(days=day)
            occupancy_sum += self.hotel.get_occupancy_rate(current_date)
        
        return occupancy_sum / self.simulation_days if self.simulation_days > 0 else 0
    
    def export_simulation_data(self, current_date):
        """Exporte les données de simulation"""
        # Export des réservations
        self.data_exporter.export_reservations(
            self.all_reservations, 
            f"reservations_{current_date.isoformat()}"
        )
        
        # Export des données d'occupation
        look_back = min(30, (current_date - self.start_date).days + 1)
        start_export = current_date - datetime.timedelta(days=look_back-1)
        
        self.data_exporter.export_occupancy(
            self.hotel,
            start_export,
            days=look_back,
            filename=f"occupancy_{current_date.isoformat()}"
        )
        
        # Export de l'analyse des revenus
        analysis = self.revenue_manager.analyze_revenue(
            self.hotel,
            start_export,
            days=look_back
        )
        
        self.data_exporter.export_revenue_analysis(
            analysis,
            f"revenue_analysis_{current_date.isoformat()}"
        )
        
        logger.info(f"Données de simulation exportées pour la période jusqu'au {current_date}")
    
    def get_simulation_summary(self):
        """Retourne un résumé de la simulation"""
        total_revenue = sum(r.total_price for r in self.all_reservations)
        avg_occupancy = self.calculate_average_occupancy()
        
        summary = {
            "simulation_period": {
                "start_date": self.start_date.isoformat(),
                "end_date": (self.start_date + datetime.timedelta(days=self.simulation_days-1)).isoformat(),
                "total_days": self.simulation_days
            },
            "performance": {
                "total_reservations": len(self.all_reservations),
                "total_revenue": total_revenue,
                "average_daily_revenue": total_revenue / self.simulation_days if self.simulation_days > 0 else 0,
                "average_occupancy_rate": avg_occupancy
            },
            "hotel_details": {
                "name": self.hotel.name,
                "total_rooms": len(self.hotel.rooms),
                "room_types": self.hotel.get_room_type_stats()
            }
        }
        
        logger.info(f"Résumé de simulation généré: {len(self.all_reservations)} réservations, "
                   f"{total_revenue:.2f}€ de revenus, {avg_occupancy:.1%} d'occupation moyenne")
        
        return summary 