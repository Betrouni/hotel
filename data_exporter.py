#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'exportation des données pour analyse
"""

import os
import csv
import json
import logging
import datetime
from pathlib import Path

logger = logging.getLogger("HotelSim.DataExporter")

class DataExporter:
    """Exporte les données de simulation pour analyse externe"""
    
    def __init__(self, export_path="./data/", export_format="csv"):
        self.export_path = export_path
        self.export_format = export_format.lower()
        
        # Création du répertoire d'exportation s'il n'existe pas
        Path(export_path).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Exportateur de données initialisé (format: {export_format}, chemin: {export_path})")
    
    def export_reservations(self, reservations, filename=None):
        """Exporte la liste des réservations"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reservations_{timestamp}"
        
        # Préparation des données
        data = []
        for reservation in reservations:
            room_id = reservation.room.id if reservation.room else None
            room_type = reservation.room.type if reservation.room else None
            
            data.append({
                "reservation_id": reservation.reservation_id,
                "request_id": reservation.request_id,
                "check_in_date": reservation.check_in_date.isoformat(),
                "check_out_date": reservation.check_out_date.isoformat(),
                "guests": reservation.guests,
                "preferred_room_type": reservation.preferred_room_type,
                "room_id": room_id,
                "room_type": room_type,
                "price_per_night": reservation.price_per_night,
                "total_price": reservation.total_price,
                "status": reservation.status,
                "creation_date": reservation.creation_date.isoformat()
            })
        
        return self._export_data(data, filename)
    
    def export_occupancy(self, hotel, start_date, days=30, filename=None):
        """Exporte les données d'occupation pour une période"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"occupancy_{timestamp}"
        
        # Préparation des données
        data = []
        for day in range(days):
            current_date = start_date + datetime.timedelta(days=day)
            occupancy_rate = hotel.get_occupancy_rate(current_date)
            revenue = hotel.get_revenue_for_date(current_date)
            
            # Statistiques par type de chambre
            room_stats = hotel.get_room_type_stats()
            room_type_data = {}
            
            # Calcul de l'occupation par type de chambre
            occupied_by_type = {}
            for room in hotel.rooms:
                room_type = room.type
                is_occupied = False
                
                for reservation in room.reservations:
                    if reservation.check_in_date <= current_date < reservation.check_out_date:
                        is_occupied = True
                        break
                
                if room_type not in occupied_by_type:
                    occupied_by_type[room_type] = 0
                
                if is_occupied:
                    occupied_by_type[room_type] += 1
            
            # Calcul des taux d'occupation par type
            for room_type, stats in room_stats.items():
                occupied = occupied_by_type.get(room_type, 0)
                occupancy_rate_type = occupied / stats["count"] if stats["count"] > 0 else 0
                
                room_type_data[f"{room_type}_total"] = stats["count"]
                room_type_data[f"{room_type}_occupied"] = occupied
                room_type_data[f"{room_type}_occupancy_rate"] = occupancy_rate_type
            
            # Données pour le jour
            day_data = {
                "date": current_date.isoformat(),
                "occupancy_rate": occupancy_rate,
                "revenue": revenue,
                **room_type_data
            }
            
            data.append(day_data)
        
        return self._export_data(data, filename)
    
    def export_revenue_analysis(self, analysis, filename=None):
        """Exporte l'analyse des revenus"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"revenue_analysis_{timestamp}"
        
        # Préparation des données
        data = []
        
        # Données agrégées
        aggregated = {
            "date": "TOTAL",
            "total_revenue": analysis["total_revenue"],
            "average_daily_revenue": analysis["average_daily_revenue"],
            "average_occupancy": analysis["average_occupancy"]
        }
        data.append(aggregated)
        
        # Données journalières
        for date, revenue in analysis["daily_revenue"].items():
            occupancy = analysis["daily_occupancy"].get(date, 0)
            day_data = {
                "date": date.isoformat(),
                "revenue": revenue,
                "occupancy_rate": occupancy
            }
            data.append(day_data)
        
        return self._export_data(data, filename)
    
    def export_price_suggestions(self, suggestions, filename=None):
        """Exporte les suggestions d'ajustement de prix"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"price_suggestions_{timestamp}"
        
        # Préparation des données
        data = []
        
        for room_type, suggestion in suggestions.items():
            suggestion_data = {
                "room_type": room_type,
                "current_base_price": suggestion["current_base_price"],
                "suggested_adjustment_pct": suggestion["suggested_adjustment_pct"],
                "suggested_new_base": suggestion["suggested_new_base"],
                "reason": suggestion["reason"]
            }
            data.append(suggestion_data)
        
        return self._export_data(data, filename)
    
    def _export_data(self, data, filename):
        """Méthode interne pour exporter les données dans le format demandé"""
        full_path = os.path.join(self.export_path, f"{filename}.{self.export_format}")
        
        try:
            if self.export_format == "csv":
                return self._export_to_csv(data, full_path)
            elif self.export_format == "json":
                return self._export_to_json(data, full_path)
            else:
                logger.error(f"Format d'exportation non pris en charge: {self.export_format}")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation des données: {e}")
            return False
    
    def _export_to_csv(self, data, full_path):
        """Exporte les données au format CSV"""
        if not data:
            logger.warning("Aucune donnée à exporter")
            return False
        
        try:
            with open(full_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Récupération des champs à partir du premier élément
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Données exportées avec succès vers {full_path}")
            return full_path
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation CSV: {e}")
            return False
    
    def _export_to_json(self, data, full_path):
        """Exporte les données au format JSON"""
        if not data:
            logger.warning("Aucune donnée à exporter")
            return False
        
        try:
            with open(full_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2)
            
            logger.info(f"Données exportées avec succès vers {full_path}")
            return full_path
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation JSON: {e}")
            return False
    
    def prepare_weather_data(self, weather_data):
        """Prépare les données météo pour l'exportation"""
        formatted_data = []
        
        for date, data in weather_data.items():
            weather_entry = {
                "date": date.isoformat(),
                "temperature": data.get("temperature"),
                "weather_condition": data.get("condition"),
                "demand_impact": data.get("demand_impact", 1.0)
            }
            formatted_data.append(weather_entry)
        
        return formatted_data 