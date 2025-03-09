#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de gestion de l'hôtel et des chambres
"""

import logging
import datetime
from collections import defaultdict

logger = logging.getLogger("HotelSim.Hotel")

class Room:
    """Représente une chambre d'hôtel"""
    
    def __init__(self, room_id, room_type, capacity):
        self.id = room_id
        self.type = room_type
        self.capacity = capacity
        self.reservations = []  # Liste des réservations pour cette chambre
    
    def is_available(self, check_in_date, check_out_date):
        """Vérifie si la chambre est disponible pour la période donnée"""
        for reservation in self.reservations:
            # Si les périodes se chevauchent, la chambre n'est pas disponible
            if not (check_out_date <= reservation.check_in_date or 
                    check_in_date >= reservation.check_out_date):
                return False
        return True
    
    def add_reservation(self, reservation):
        """Ajoute une réservation à cette chambre"""
        if not self.is_available(reservation.check_in_date, reservation.check_out_date):
            raise ValueError("La chambre n'est pas disponible pour cette période")
        
        if reservation.guests > self.capacity:
            raise ValueError(f"Trop de personnes pour cette chambre (max: {self.capacity})")
        
        self.reservations.append(reservation)
        self.reservations.sort(key=lambda r: r.check_in_date)  # Maintenir l'ordre chronologique
        logger.debug(f"Réservation ajoutée à la chambre {self.id} pour {reservation.check_in_date} - {reservation.check_out_date}")
        
        return True
    
    def __str__(self):
        return f"Chambre {self.id} ({self.type}) - Capacité: {self.capacity} personnes"


class Hotel:
    """Représente l'hôtel avec l'ensemble de ses chambres"""
    
    def __init__(self, name, room_types):
        self.name = name
        self.rooms = []
        self.room_types = room_types
        
        # Création des chambres
        room_id = 1
        for room_type, details in room_types.items():
            for _ in range(details["count"]):
                self.rooms.append(Room(room_id, room_type, details["capacity"]))
                room_id += 1
        
        logger.info(f"Hôtel '{name}' initialisé avec {len(self.rooms)} chambres")
    
    def get_available_rooms(self, check_in_date, check_out_date, guests=1, room_type=None):
        """Trouve toutes les chambres disponibles pour la période et les critères donnés"""
        available_rooms = []
        
        for room in self.rooms:
            if room.is_available(check_in_date, check_out_date) and room.capacity >= guests:
                if room_type is None or room.type == room_type:
                    available_rooms.append(room)
        
        return available_rooms
    
    def book_room(self, reservation):
        """Réserve une chambre disponible pour la demande"""
        available_rooms = self.get_available_rooms(
            reservation.check_in_date,
            reservation.check_out_date,
            reservation.guests,
            reservation.preferred_room_type
        )
        
        if not available_rooms:
            logger.info(f"Aucune chambre disponible pour la réservation du {reservation.check_in_date} au {reservation.check_out_date}")
            return None
        
        # Choix de la chambre la plus adaptée (économie de chambres)
        best_room = min(available_rooms, key=lambda r: r.capacity)
        
        try:
            best_room.add_reservation(reservation)
            reservation.room = best_room
            logger.info(f"Réservation confirmée: Chambre {best_room.id} du {reservation.check_in_date} au {reservation.check_out_date}")
            return best_room
        except Exception as e:
            logger.error(f"Erreur lors de la réservation: {e}")
            return None
    
    def get_occupancy_rate(self, date):
        """Calcule le taux d'occupation pour une date donnée"""
        occupied_rooms = 0
        
        for room in self.rooms:
            for reservation in room.reservations:
                if reservation.check_in_date <= date < reservation.check_out_date:
                    occupied_rooms += 1
                    break
        
        return occupied_rooms / len(self.rooms) if self.rooms else 0
    
    def get_occupancy_forecast(self, start_date, days=30):
        """Calcule les prévisions d'occupation sur plusieurs jours"""
        forecast = {}
        
        for day in range(days):
            current_date = start_date + datetime.timedelta(days=day)
            forecast[current_date] = self.get_occupancy_rate(current_date)
        
        return forecast
    
    def get_revenue_for_date(self, date):
        """Calcule le revenu pour une date donnée"""
        revenue = 0
        
        for room in self.rooms:
            for reservation in room.reservations:
                if reservation.check_in_date <= date < reservation.check_out_date:
                    # On divise le prix total par le nombre de nuits pour obtenir le prix par nuit
                    nights = (reservation.check_out_date - reservation.check_in_date).days
                    revenue += reservation.total_price / nights
                    break
        
        return revenue
    
    def get_room_type_stats(self):
        """Retourne les statistiques par type de chambre"""
        stats = defaultdict(lambda: {"count": 0, "booked": 0})
        
        for room_type, details in self.room_types.items():
            stats[room_type]["count"] = details["count"]
            stats[room_type]["capacity"] = details["capacity"]
        
        return dict(stats)
    
    def __str__(self):
        room_counts = ", ".join([f"{count} {room_type}" for room_type, details in self.room_types.items() 
                                 for count in [details["count"]]])
        return f"Hôtel {self.name} - {len(self.rooms)} chambres ({room_counts})"