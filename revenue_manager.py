#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de gestion des revenus et tarification dynamique
"""

import datetime
import logging
import math

logger = logging.getLogger("HotelSim.RevenueManager")

class RevenueManager:
    """Gestionnaire de revenus et de tarification dynamique"""
    
    def __init__(self, base_rates, occupancy_thresholds, price_multipliers, seasons):
        self.base_rates = base_rates  # Prix de base par type de chambre
        self.occupancy_thresholds = occupancy_thresholds  # Seuils d'occupation pour ajustement des prix
        self.price_multipliers = price_multipliers  # Multiplicateurs de prix correspondant aux seuils
        self.seasons = seasons  # Définition des saisons
        
        # Multiplicateurs de prix par saison
        self.season_multipliers = {
            "high": 1.3,    # Haute saison: +30%
            "medium": 1.0,  # Saison moyenne: prix de base
            "low": 0.8      # Basse saison: -20%
        }
        
        # Multiplicateur d'anticipation (prix plus élevés pour les réservations tardives)
        self.advance_booking_discounts = {
            60: 0.85,  # 60+ jours à l'avance: -15%
            30: 0.9,   # 30-59 jours à l'avance: -10%
            14: 0.95,  # 14-29 jours à l'avance: -5%
            7: 1.0,    # 7-13 jours à l'avance: prix normal
            3: 1.05,   # 3-6 jours à l'avance: +5%
            0: 1.1     # 0-2 jours à l'avance: +10%
        }
        
        # Minimum et maximum de modification de prix
        self.min_price_multiplier = 0.7  # -30% max
        self.max_price_multiplier = 1.5  # +50% max
        
        logger.info("Gestionnaire de revenus initialisé")
    
    def get_current_season(self, date):
        """Détermine la saison en fonction de la date"""
        date_str = date.strftime("%m-%d")
        
        for season_name, periods in self.seasons.items():
            for period in periods:
                start = period["start"]
                end = period["end"]
                
                # Gestion du cas où la période chevauche l'année
                if start > end:
                    if date_str >= start or date_str <= end:
                        return season_name
                else:
                    if start <= date_str <= end:
                        return season_name
        
        # Par défaut, saison moyenne
        return "medium"
    
    def get_advance_booking_multiplier(self, booking_date, check_in_date):
        """Calcule le multiplicateur de prix en fonction de l'anticipation de réservation"""
        days_in_advance = (check_in_date - booking_date).days
        
        for days, multiplier in sorted(self.advance_booking_discounts.items()):
            if days_in_advance >= days:
                return multiplier
        
        # Par défaut, si avant tous les seuils
        return self.advance_booking_discounts[max(self.advance_booking_discounts.keys())]
    
    def calculate_price(self, room_type, date, occupancy_rate, booking_date=None):
        """Calcule le prix dynamique pour un type de chambre et une date"""
        # Prix de base pour ce type de chambre
        base_price = self.base_rates[room_type]
        
        # Détermination de la saison
        season = self.get_current_season(date)
        season_multiplier = self.season_multipliers[season]
        
        # Multiplicateur basé sur le taux d'occupation
        occupancy_multiplier = 1.0
        for i, threshold in enumerate(self.occupancy_thresholds):
            if occupancy_rate >= threshold:
                occupancy_multiplier = self.price_multipliers[i]
        
        # Multiplicateur d'anticipation
        advance_multiplier = 1.0
        if booking_date:
            advance_multiplier = self.get_advance_booking_multiplier(booking_date, date)
        
        # Calcul du prix final
        total_multiplier = season_multiplier * occupancy_multiplier * advance_multiplier
        
        # Application des limites min/max
        total_multiplier = max(self.min_price_multiplier, min(self.max_price_multiplier, total_multiplier))
        
        # Arrondi du prix à l'unité près
        price = math.ceil(base_price * total_multiplier)
        
        logger.debug(f"Prix calculé pour {room_type} le {date}: {price}€ (taux d'occupation: {occupancy_rate:.1%})")
        return price
    
    def calculate_prices_for_stay(self, room_type, check_in_date, check_out_date, hotel, booking_date=None):
        """Calcule les prix pour toute la durée du séjour"""
        daily_prices = []
        total_nights = (check_out_date - check_in_date).days
        
        for night in range(total_nights):
            current_date = check_in_date + datetime.timedelta(days=night)
            occupancy_rate = hotel.get_occupancy_rate(current_date)
            price = self.calculate_price(room_type, current_date, occupancy_rate, booking_date)
            daily_prices.append(price)
        
        return daily_prices
    
    def get_average_price(self, daily_prices):
        """Calcule le prix moyen par nuit à partir des prix journaliers"""
        if not daily_prices:
            return 0
        return sum(daily_prices) / len(daily_prices)
    
    def optimize_price_for_request(self, request, hotel, current_date):
        """Détermine le prix optimal pour une demande de réservation"""
        if request.preferred_room_type:
            # Si le client a une préférence de type de chambre
            room_type = request.preferred_room_type
            daily_prices = self.calculate_prices_for_stay(
                room_type, 
                request.check_in_date, 
                request.check_out_date, 
                hotel, 
                current_date
            )
            avg_price = self.get_average_price(daily_prices)
            
            # Vérification si le client peut se permettre ce prix
            if request.can_afford(avg_price):
                return avg_price, daily_prices
            
            # Si non abordable, essayer de trouver un autre type de chambre
            for rt in self.base_rates.keys():
                if rt == room_type:
                    continue
                
                # Vérifier si un autre type de chambre peut convenir
                daily_prices = self.calculate_prices_for_stay(
                    rt, 
                    request.check_in_date, 
                    request.check_out_date, 
                    hotel, 
                    current_date
                )
                avg_price = self.get_average_price(daily_prices)
                
                if request.can_afford(avg_price):
                    # Vérifier la disponibilité
                    available_rooms = hotel.get_available_rooms(
                        request.check_in_date,
                        request.check_out_date,
                        request.guests,
                        rt
                    )
                    
                    if available_rooms:
                        return avg_price, daily_prices
        else:
            # Si le client n'a pas de préférence, trouver la meilleure option
            for room_type in sorted(self.base_rates.keys(), key=lambda rt: self.base_rates[rt]):
                daily_prices = self.calculate_prices_for_stay(
                    room_type, 
                    request.check_in_date, 
                    request.check_out_date, 
                    hotel, 
                    current_date
                )
                avg_price = self.get_average_price(daily_prices)
                
                # Vérifier si abordable
                if request.can_afford(avg_price):
                    # Vérifier disponibilité
                    available_rooms = hotel.get_available_rooms(
                        request.check_in_date,
                        request.check_out_date,
                        request.guests,
                        room_type
                    )
                    
                    if available_rooms:
                        return avg_price, daily_prices
        
        # Si aucune option n'est disponible ou abordable
        return None, []
    
    def analyze_revenue(self, hotel, start_date, days=30):
        """Analyse les revenus sur une période donnée"""
        revenue_data = {}
        occupancy_data = {}
        
        for day in range(days):
            current_date = start_date + datetime.timedelta(days=day)
            revenue = hotel.get_revenue_for_date(current_date)
            occupancy = hotel.get_occupancy_rate(current_date)
            
            revenue_data[current_date] = revenue
            occupancy_data[current_date] = occupancy
        
        total_revenue = sum(revenue_data.values())
        avg_occupancy = sum(occupancy_data.values()) / len(occupancy_data) if occupancy_data else 0
        
        analysis = {
            "total_revenue": total_revenue,
            "average_daily_revenue": total_revenue / days if days > 0 else 0,
            "average_occupancy": avg_occupancy,
            "daily_revenue": revenue_data,
            "daily_occupancy": occupancy_data
        }
        
        logger.info(f"Analyse des revenus sur {days} jours: {total_revenue:.2f}€ (occupancy: {avg_occupancy:.1%})")
        return analysis
    
    def suggest_price_adjustments(self, hotel, start_date, days=30):
        """Suggère des ajustements de prix basés sur l'analyse des revenus"""
        analysis = self.analyze_revenue(hotel, start_date, days)
        
        suggestions = {}
        room_types = list(self.base_rates.keys())
        
        for room_type in room_types:
            current_base = self.base_rates[room_type]
            
            if analysis["average_occupancy"] < 0.5:
                # Faible occupation: suggérer une réduction de prix
                suggested_adjustment = -0.1  # -10%
                reason = "Faible taux d'occupation"
            elif analysis["average_occupancy"] > 0.85:
                # Forte occupation: suggérer une augmentation de prix
                suggested_adjustment = 0.15  # +15%
                reason = "Fort taux d'occupation"
            else:
                # Occupation moyenne: ajustement mineur
                if analysis["average_occupancy"] < 0.65:
                    suggested_adjustment = -0.05  # -5%
                    reason = "Taux d'occupation modéré"
                elif analysis["average_occupancy"] > 0.75:
                    suggested_adjustment = 0.05  # +5%
                    reason = "Bon taux d'occupation"
                else:
                    suggested_adjustment = 0  # Pas de changement
                    reason = "Taux d'occupation optimal"
            
            suggestions[room_type] = {
                "current_base_price": current_base,
                "suggested_adjustment_pct": suggested_adjustment * 100,
                "suggested_new_base": round(current_base * (1 + suggested_adjustment)),
                "reason": reason
            }
        
        logger.info(f"Ajustements de prix suggérés: {suggestions}")
        return suggestions 