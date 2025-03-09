#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Générateur de tableau de bord pour visualiser les résultats de la simulation.
"""

import os
import json
import csv
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from pathlib import Path
import argparse
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dashboard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HotelSim.Dashboard")

class Dashboard:
    """Générateur de tableau de bord pour visualiser les données de simulation"""
    
    def __init__(self, data_path="./data", output_path="./dashboard"):
        self.data_path = Path(data_path)
        self.output_path = Path(output_path)
        
        # Création du répertoire de sortie s'il n'existe pas
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Style des graphiques
        plt.style.use('seaborn-v0_8-darkgrid')
        self.colors = {
            "standard": "#3498db",
            "confort": "#2ecc71",
            "suite": "#e74c3c",
            "revenue": "#f39c12",
            "occupancy": "#9b59b6"
        }
        
        logger.info(f"Dashboard initialisé (source: {data_path}, sortie: {output_path})")
    
    def load_csv_data(self, file_path):
        """Charge les données d'un fichier CSV"""
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append(row)
            return data
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier CSV {file_path}: {e}")
            return []
    
    def find_latest_files(self, prefix):
        """Trouve les fichiers les plus récents pour un préfixe donné"""
        files = list(self.data_path.glob(f"{prefix}_*.csv"))
        if not files:
            return None
        
        # Tri par date de modification (la plus récente en premier)
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        return latest_file
    
    def generate_occupancy_chart(self):
        """Génère un graphique d'occupation par jour"""
        file_path = self.find_latest_files("occupancy")
        if not file_path:
            logger.warning("Aucun fichier d'occupation trouvé")
            return None
        
        data = self.load_csv_data(file_path)
        if not data:
            return None
        
        # Préparation des données
        dates = []
        occupancy_rates = []
        standard_rates = []
        confort_rates = []
        suite_rates = []
        
        for row in data:
            try:
                date = datetime.datetime.fromisoformat(row['date']).date()
                dates.append(date)
                occupancy_rates.append(float(row['occupancy_rate']))
                
                # Taux d'occupation par type de chambre
                standard_rates.append(float(row.get('standard_occupancy_rate', 0)))
                confort_rates.append(float(row.get('confort_occupancy_rate', 0)))
                suite_rates.append(float(row.get('suite_occupancy_rate', 0)))
            except (ValueError, KeyError) as e:
                logger.warning(f"Erreur lors du traitement d'une ligne de données: {e}")
        
        # Création du graphique
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(dates, occupancy_rates, 'o-', color=self.colors["occupancy"], linewidth=2, label='Taux d\'occupation global')
        
        # Ajout des taux par type de chambre si disponibles
        if all(standard_rates):
            ax.plot(dates, standard_rates, '--', color=self.colors["standard"], alpha=0.7, label='Standard')
        
        if all(confort_rates):
            ax.plot(dates, confort_rates, '--', color=self.colors["confort"], alpha=0.7, label='Confort')
        
        if all(suite_rates):
            ax.plot(dates, suite_rates, '--', color=self.colors["suite"], alpha=0.7, label='Suite')
        
        # Mise en forme
        ax.set_title('Taux d\'occupation journalier', fontsize=16)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Taux d\'occupation', fontsize=12)
        ax.set_ylim(0, 1.05)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
        
        # Formatage des dates sur l'axe X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.xticks(rotation=45)
        
        # Zones de référence
        ax.axhspan(0.8, 1, alpha=0.2, color='green', label='Excellente occupation')
        ax.axhspan(0.5, 0.8, alpha=0.2, color='yellow', label='Bonne occupation')
        ax.axhspan(0, 0.5, alpha=0.2, color='red', label='Faible occupation')
        
        # Légende
        ax.legend(loc='upper left', fontsize=10)
        
        # Grille
        ax.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        output_file = self.output_path / 'occupancy_chart.png'
        plt.savefig(output_file, dpi=300)
        plt.close()
        
        logger.info(f"Graphique d'occupation généré: {output_file}")
        return output_file
    
    def generate_revenue_chart(self):
        """Génère un graphique de revenus par jour"""
        file_path = self.find_latest_files("occupancy")
        if not file_path:
            logger.warning("Aucun fichier d'occupation trouvé")
            return None
        
        data = self.load_csv_data(file_path)
        if not data:
            return None
        
        # Préparation des données
        dates = []
        revenues = []
        occupancy_rates = []
        
        for row in data:
            try:
                date = datetime.datetime.fromisoformat(row['date']).date()
                dates.append(date)
                revenues.append(float(row['revenue']))
                occupancy_rates.append(float(row['occupancy_rate']))
            except (ValueError, KeyError) as e:
                logger.warning(f"Erreur lors du traitement d'une ligne de données: {e}")
        
        # Création du graphique avec double axe Y
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # Graphique des revenus
        color = self.colors["revenue"]
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_ylabel('Revenu (€)', color=color, fontsize=12)
        ax1.bar(dates, revenues, color=color, alpha=0.7, label='Revenu journalier')
        ax1.tick_params(axis='y', labelcolor=color)
        
        # Deuxième axe pour le taux d'occupation
        ax2 = ax1.twinx()
        color = self.colors["occupancy"]
        ax2.set_ylabel('Taux d\'occupation', color=color, fontsize=12)
        ax2.plot(dates, occupancy_rates, 'o-', color=color, linewidth=2, label='Taux d\'occupation')
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.set_ylim(0, 1.05)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
        
        # Titre
        plt.title('Revenus et Taux d\'occupation', fontsize=16)
        
        # Formatage des dates
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.xticks(rotation=45)
        
        # Légendes combinées
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
        
        # Grille
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        output_file = self.output_path / 'revenue_chart.png'
        plt.savefig(output_file, dpi=300)
        plt.close()
        
        logger.info(f"Graphique de revenus généré: {output_file}")
        return output_file
    
    def generate_price_chart(self):
        """Génère un graphique des suggestions de prix"""
        file_path = self.find_latest_files("price_suggestions")
        if not file_path:
            logger.warning("Aucun fichier de suggestions de prix trouvé")
            return None
        
        data = self.load_csv_data(file_path)
        if not data:
            return None
        
        # Préparation des données
        room_types = []
        current_prices = []
        suggested_prices = []
        adjustments = []
        
        for row in data:
            try:
                room_type = row['room_type']
                room_types.append(room_type)
                current_prices.append(float(row['current_base_price']))
                suggested_prices.append(float(row['suggested_new_base']))
                adjustments.append(float(row['suggested_adjustment_pct']))
            except (ValueError, KeyError) as e:
                logger.warning(f"Erreur lors du traitement d'une ligne de données: {e}")
        
        # Création du graphique
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Positionnement des barres
        x = np.arange(len(room_types))
        width = 0.35
        
        # Barres
        rects1 = ax.bar(x - width/2, current_prices, width, label='Prix actuel', color='#3498db')
        rects2 = ax.bar(x + width/2, suggested_prices, width, label='Prix suggéré', color='#9b59b6')
        
        # Ajout des pourcentages d'ajustement
        for i, rect in enumerate(rects2):
            height = rect.get_height()
            adjustment = adjustments[i]
            color = 'green' if adjustment >= 0 else 'red'
            ax.annotate(f'{adjustment:+.1f}%',
                        xy=(rect.get_x() + rect.get_width()/2, height),
                        xytext=(0, 3),  # 3 points de décalage vertical
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=9, color=color, fontweight='bold')
        
        # Mise en forme
        ax.set_title('Suggestions d\'ajustement des prix de base', fontsize=16)
        ax.set_ylabel('Prix (€)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(room_types)
        ax.legend()
        
        # Formatage des prix sur l'axe Y
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}€'))
        
        plt.tight_layout()
        output_file = self.output_path / 'price_suggestions_chart.png'
        plt.savefig(output_file, dpi=300)
        plt.close()
        
        logger.info(f"Graphique de suggestions de prix généré: {output_file}")
        return output_file
    
    def generate_room_distribution_chart(self):
        """Génère un graphique de la distribution des types de chambres réservées"""
        file_path = self.find_latest_files("reservations")
        if not file_path:
            logger.warning("Aucun fichier de réservations trouvé")
            return None
        
        data = self.load_csv_data(file_path)
        if not data:
            return None
        
        # Comptage des réservations par type de chambre
        room_type_counts = {"standard": 0, "confort": 0, "suite": 0}
        
        for row in data:
            try:
                room_type = row['room_type']
                if room_type in room_type_counts:
                    room_type_counts[room_type] += 1
            except (KeyError, TypeError) as e:
                logger.warning(f"Erreur lors du traitement d'une ligne de données: {e}")
        
        # Filtrer les types qui ont des réservations
        labels = []
        counts = []
        colors = []
        
        for room_type, count in room_type_counts.items():
            if count > 0:
                labels.append(room_type.capitalize())
                counts.append(count)
                colors.append(self.colors.get(room_type, '#333333'))
        
        # Création du graphique en camembert
        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(
            counts, 
            labels=labels, 
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            wedgeprops={'width': 0.5, 'edgecolor': 'w'}
        )
        
        # Mise en forme des textes
        plt.setp(autotexts, size=10, weight="bold")
        plt.setp(texts, size=12)
        
        # Titre
        ax.set_title('Distribution des réservations par type de chambre', fontsize=16)
        
        # Légende avec le nombre exact
        legend_labels = [f"{label}: {count}" for label, count in zip(labels, counts)]
        ax.legend(wedges, legend_labels, title="Types de chambre", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.tight_layout()
        output_file = self.output_path / 'room_distribution_chart.png'
        plt.savefig(output_file, dpi=300)
        plt.close()
        
        logger.info(f"Graphique de distribution des chambres généré: {output_file}")
        return output_file
    
    def generate_html_dashboard(self):
        """Génère un tableau de bord HTML avec tous les graphiques"""
        # Génération des graphiques
        occupancy_chart = self.generate_occupancy_chart()
        revenue_chart = self.generate_revenue_chart()
        price_chart = self.generate_price_chart()
        distribution_chart = self.generate_room_distribution_chart()
        
        # Création du HTML
        html_content = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Tableau de Bord HotelSim</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .chart-container {{
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 30px;
                    padding: 20px;
                }}
                h2 {{
                    color: #2c3e50;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 0 auto;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    background-color: #2c3e50;
                    color: white;
                }}
                .timestamp {{
                    text-align: right;
                    font-size: 0.8em;
                    color: #7f8c8d;
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <header>
                <h1>Tableau de Bord HotelSim - Le Petit Refuge</h1>
            </header>
            
            <div class="container">
                <div class="chart-container">
                    <h2>Taux d'Occupation</h2>
                    <img src="occupancy_chart.png" alt="Taux d'occupation">
                    <p>Ce graphique montre l'évolution du taux d'occupation de l'hôtel au cours du temps, globalement et par type de chambre.</p>
                </div>
                
                <div class="chart-container">
                    <h2>Revenus et Occupation</h2>
                    <img src="revenue_chart.png" alt="Revenus et occupation">
                    <p>Ce graphique compare les revenus journaliers avec le taux d'occupation, montrant la corrélation entre ces deux indicateurs.</p>
                </div>
                
                <div class="chart-container">
                    <h2>Suggestions d'Ajustement des Prix</h2>
                    <img src="price_suggestions_chart.png" alt="Suggestions de prix">
                    <p>Ce graphique présente les suggestions d'ajustement des prix de base pour maximiser les revenus, basées sur l'analyse des données historiques.</p>
                </div>
                
                <div class="chart-container">
                    <h2>Distribution des Réservations</h2>
                    <img src="room_distribution_chart.png" alt="Distribution des chambres">
                    <p>Ce graphique montre la répartition des réservations par type de chambre, indiquant les préférences de la clientèle.</p>
                </div>
                
                <div class="timestamp">
                    Généré le: {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}
                </div>
            </div>
            
            <div class="footer">
                <p>HotelSim - Simulateur de Gestion Hôtelière</p>
            </div>
        </body>
        </html>
        """
        
        # Écriture du fichier HTML
        html_path = self.output_path / 'dashboard.html'
        try:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Tableau de bord HTML généré: {html_path}")
            return html_path
        except Exception as e:
            logger.error(f"Erreur lors de la génération du tableau de bord HTML: {e}")
            return None
    
    def generate_all(self):
        """Génère tous les graphiques et le tableau de bord"""
        self.generate_occupancy_chart()
        self.generate_revenue_chart()
        self.generate_price_chart()
        self.generate_room_distribution_chart()
        html_path = self.generate_html_dashboard()
        
        return html_path


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Générateur de tableau de bord pour HotelSim')
    parser.add_argument('--data', default='./data', help='Chemin vers le répertoire des données')
    parser.add_argument('--output', default='./dashboard', help='Chemin vers le répertoire de sortie')
    
    args = parser.parse_args()
    
    dashboard = Dashboard(args.data, args.output)
    html_path = dashboard.generate_all()
    
    if html_path:
        print(f"Tableau de bord généré avec succès dans: {html_path}")
    else:
        print("Erreur lors de la génération du tableau de bord")


if __name__ == "__main__":
    main() 