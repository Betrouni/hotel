/**
 * HotelSim - Intégration Google Sheets
 * 
 * Ce script simule l'intégration du simulateur HotelSim avec Google Sheets.
 * Il permet d'automatiser la mise à jour quotidienne des données, de générer
 * des visualisations et d'envoyer des notifications.
 */

// Configuration globale
const CONFIG = {
  hotelName: "Le Petit Refuge",
  roomTypes: {
    standard: { count: 5, capacity: 2, basePrice: 80 },
    confort: { count: 7, capacity: 3, basePrice: 120 },
    suite: { count: 3, capacity: 4, basePrice: 180 }
  },
  sheets: {
    reservations: "Réservations",
    occupancy: "Occupation",
    revenue: "Revenus",
    dashboard: "Tableau de bord",
    prices: "Prix Dynamiques"
  },
  thresholds: {
    lowOccupancy: 0.4,
    highOccupancy: 0.8
  },
  email: {
    alertRecipients: "manager@petitrefuge.com",
    reportRecipients: "direction@petitrefuge.com"
  }
};

/**
 * Point d'entrée principal - s'exécute lors de l'ouverture de la feuille
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  
  // Création du menu personnalisé
  ui.createMenu('HotelSim')
    .addItem('Exécuter Simulation', 'runSimulation')
    .addItem('Mettre à jour le tableau de bord', 'updateDashboard')
    .addItem('Générer rapport d\'occupation', 'generateOccupancyReport')
    .addItem('Calculer tarifs dynamiques', 'calculateDynamicPrices')
    .addSeparator()
    .addItem('Configurer notifications', 'setupNotifications')
    .addToUi();
}

/**
 * Exécute la simulation de réservations pour un jour
 */
function runSimulation() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert('Lancer la simulation', 
                           'Voulez-vous exécuter la simulation pour un jour supplémentaire ?', 
                           ui.ButtonSet.YES_NO);
  
  if (response !== ui.Button.YES) return;
  
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  // Récupérer la date de la dernière simulation
  let lastDate = getLastSimulationDate();
  const newDate = new Date(lastDate.getTime() + 24*60*60*1000); // Le jour suivant
  
  // Générer de nouvelles réservations
  const newReservations = generateDailyReservations(newDate);
  
  // Mettre à jour les feuilles de données
  updateReservationsSheet(newReservations);
  updateOccupancySheet(newDate);
  updateRevenueSheet(newDate);
  
  // Mettre à jour le tableau de bord
  updateDashboard();
  
  // Vérifier s'il faut envoyer des alertes
  checkOccupancyAlerts(newDate);
  
  ui.alert('Simulation terminée', 
           `Simulation effectuée pour le ${formatDate(newDate)}.\n${newReservations.length} nouvelles demandes traitées.`, 
           ui.ButtonSet.OK);
}

/**
 * Récupère la date de la dernière simulation
 */
function getLastSimulationDate() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.sheets.occupancy);
  
  // Si pas de données, on commence aujourd'hui
  if (sheet.getLastRow() <= 1) {
    return new Date();
  }
  
  // Sinon on prend la dernière date
  const lastDateCell = sheet.getRange(sheet.getLastRow(), 1);
  return lastDateCell.getValue();
}

/**
 * Génère des demandes de réservation aléatoires pour un jour
 */
function generateDailyReservations(date) {
  // Nombre de demandes en fonction de la saison
  const season = determineSeason(date);
  let requestCount;
  
  switch(season) {
    case 'high':
      requestCount = Math.floor(Math.random() * 10) + 15; // 15-25 demandes
      break;
    case 'medium':
      requestCount = Math.floor(Math.random() * 8) + 10;  // 10-18 demandes
      break;
    case 'low':
      requestCount = Math.floor(Math.random() * 7) + 5;   // 5-12 demandes
      break;
  }
  
  // Génération des demandes
  const requests = [];
  for (let i = 0; i < requestCount; i++) {
    requests.push(generateReservationRequest(date));
  }
  
  // Traitement des demandes
  const reservations = [];
  const occupancyData = getOccupancyData();
  
  for (const request of requests) {
    // Vérifier la disponibilité pour ces dates
    if (isRoomAvailable(request.roomType, request.checkInDate, request.checkOutDate, occupancyData)) {
      // Calcul du prix dynamique
      const pricePerNight = calculateDynamicPrice(request.roomType, request.checkInDate, occupancyData);
      
      // Vérifier si le client accepte le prix
      if (pricePerNight <= request.maxBudget) {
        // Créer la réservation
        const reservation = {
          id: 'RES' + Math.floor(Math.random() * 10000),
          ...request,
          status: 'confirmed',
          pricePerNight: pricePerNight,
          totalPrice: pricePerNight * calculateNights(request.checkInDate, request.checkOutDate),
          creationDate: date
        };
        
        reservations.push(reservation);
        
        // Mettre à jour les données d'occupation
        updateOccupancyData(occupancyData, reservation);
      }
    }
  }
  
  return reservations;
}

/**
 * Génère une demande de réservation individuelle
 */
function generateReservationRequest(currentDate) {
  // Types de chambres disponibles
  const roomTypes = Object.keys(CONFIG.roomTypes);
  
  // Sélection aléatoire du type de chambre
  const roomType = roomTypes[Math.floor(Math.random() * roomTypes.length)];
  
  // Nombre de personnes en fonction du type de chambre
  const maxPersons = CONFIG.roomTypes[roomType].capacity;
  const persons = Math.floor(Math.random() * maxPersons) + 1;
  
  // Date d'arrivée (entre aujourd'hui et 60 jours dans le futur)
  const daysInFuture = Math.floor(Math.random() * 60) + 1;
  const checkInDate = new Date(currentDate.getTime() + daysInFuture * 24*60*60*1000);
  
  // Durée du séjour (entre 1 et 7 nuits)
  const stayDuration = Math.floor(Math.random() * 7) + 1;
  const checkOutDate = new Date(checkInDate.getTime() + stayDuration * 24*60*60*1000);
  
  // Budget maximum par nuit (basé sur le prix de base avec variation aléatoire)
  const basePrice = CONFIG.roomTypes[roomType].basePrice;
  const budgetVariation = 0.7 + Math.random() * 0.6; // Entre 70% et 130% du prix de base
  const maxBudget = Math.round(basePrice * budgetVariation);
  
  return {
    requestId: 'REQ' + Math.floor(Math.random() * 10000),
    checkInDate: checkInDate,
    checkOutDate: checkOutDate,
    persons: persons,
    roomType: roomType,
    maxBudget: maxBudget
  };
}

/**
 * Détermine la saison en fonction de la date
 */
function determineSeason(date) {
  const month = date.getMonth() + 1; // getMonth() renvoie 0-11
  const day = date.getDate();
  
  // Définition des saisons
  if ((month === 6 && day >= 15) || 
      (month === 7) || 
      (month === 8) || 
      (month === 9 && day <= 15) ||
      (month === 12 && day >= 15) ||
      (month === 1 && day <= 5)) {
    return 'high';  // Haute saison
  } else if ((month === 4) || 
             (month === 5) || 
             (month === 6 && day < 15) ||
             (month === 9 && day > 15) ||
             (month === 10)) {
    return 'medium';  // Moyenne saison
  } else {
    return 'low';  // Basse saison
  }
}

/**
 * Calcule le prix dynamique pour un type de chambre et une date
 */
function calculateDynamicPrice(roomType, date, occupancyData) {
  const basePrice = CONFIG.roomTypes[roomType].basePrice;
  
  // Facteur de saison
  const season = determineSeason(date);
  let seasonMultiplier;
  
  switch(season) {
    case 'high':
      seasonMultiplier = 1.3;  // +30% en haute saison
      break;
    case 'medium':
      seasonMultiplier = 1.0;  // Prix standard en moyenne saison
      break;
    case 'low':
      seasonMultiplier = 0.8;  // -20% en basse saison
      break;
    default:
      seasonMultiplier = 1.0;
  }
  
  // Facteur d'occupation
  let occupancyMultiplier = 1.0;
  const occupancyRate = getOccupancyRateForDate(date, occupancyData);
  
  if (occupancyRate >= 0.9) {
    occupancyMultiplier = 1.25;  // +25% si presque complet
  } else if (occupancyRate >= 0.8) {
    occupancyMultiplier = 1.1;   // +10%
  } else if (occupancyRate >= 0.5) {
    occupancyMultiplier = 1.0;   // Prix standard
  } else if (occupancyRate >= 0.3) {
    occupancyMultiplier = 0.9;   // -10%
  } else {
    occupancyMultiplier = 0.8;   // -20% si peu rempli
  }
  
  // Calcul final avec arrondissement
  const finalPrice = Math.round(basePrice * seasonMultiplier * occupancyMultiplier);
  
  return finalPrice;
}

/**
 * Met à jour les réservations dans la feuille de calcul
 */
function updateReservationsSheet(newReservations) {
  if (newReservations.length === 0) return;
  
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.sheets.reservations) || ss.insertSheet(CONFIG.sheets.reservations);
  
  // Initialiser l'en-tête si nécessaire
  if (sheet.getLastRow() === 0) {
    sheet.appendRow([
      'ID Réservation', 
      'Date de création', 
      'ID Demande', 
      'Date arrivée', 
      'Date départ', 
      'Personnes', 
      'Type de chambre', 
      'Prix par nuit', 
      'Prix total', 
      'Budget max', 
      'Statut'
    ]);
    
    // Formater l'en-tête
    sheet.getRange(1, 1, 1, 11).setFontWeight('bold').setBackground('#eeeeee');
  }
  
  // Ajouter les nouvelles réservations
  for (const reservation of newReservations) {
    sheet.appendRow([
      reservation.id,
      formatDate(reservation.creationDate),
      reservation.requestId,
      formatDate(reservation.checkInDate),
      formatDate(reservation.checkOutDate),
      reservation.persons,
      reservation.roomType,
      reservation.pricePerNight,
      reservation.totalPrice,
      reservation.maxBudget,
      reservation.status
    ]);
  }
  
  // Formatage conditionnel pour le statut
  const lastRow = sheet.getLastRow();
  const statusRange = sheet.getRange(2, 11, lastRow - 1, 1);
  
  const confirmedRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo('confirmed')
    .setBackground('#d9ead3')
    .setRanges([statusRange])
    .build();
  
  const cancelledRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo('cancelled')
    .setBackground('#f4cccc')
    .setRanges([statusRange])
    .build();
  
  sheet.setConditionalFormatRules([confirmedRule, cancelledRule]);
}

/**
 * Met à jour la feuille d'occupation
 */
function updateOccupancySheet(date) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.sheets.occupancy) || ss.insertSheet(CONFIG.sheets.occupancy);
  
  // Initialiser l'en-tête si nécessaire
  if (sheet.getLastRow() === 0) {
    sheet.appendRow([
      'Date', 
      'Taux occupation', 
      'Occupation Standard', 
      'Occupation Confort', 
      'Occupation Suite', 
      'Revenus du jour'
    ]);
    
    // Formater l'en-tête
    sheet.getRange(1, 1, 1, 6).setFontWeight('bold').setBackground('#eeeeee');
  }
  
  // Calculer les données d'occupation
  const occupancyData = calculateDailyOccupancy(date);
  
  // Ajouter la ligne pour le jour
  sheet.appendRow([
    formatDate(date),
    occupancyData.occupancyRate,
    occupancyData.standardOccupancy,
    occupancyData.confortOccupancy,
    occupancyData.suiteOccupancy,
    occupancyData.dailyRevenue
  ]);
  
  // Formater les taux en pourcentages
  const lastRow = sheet.getLastRow();
  sheet.getRange(lastRow, 2, 1, 4).setNumberFormat('0.00%');
  
  // Formater le revenu
  sheet.getRange(lastRow, 6).setNumberFormat('0.00€');
  
  // Formatage conditionnel pour le taux d'occupation
  const occupancyRange = sheet.getRange(2, 2, lastRow - 1, 1);
  
  const highRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThanOrEqualTo(0.8)
    .setBackground('#d9ead3')
    .setRanges([occupancyRange])
    .build();
  
  const mediumRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberBetween(0.4, 0.8)
    .setBackground('#fff2cc')
    .setRanges([occupancyRange])
    .build();
  
  const lowRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberLessThan(0.4)
    .setBackground('#f4cccc')
    .setRanges([occupancyRange])
    .build();
  
  sheet.setConditionalFormatRules([highRule, mediumRule, lowRule]);
}

/**
 * Calcule l'occupation pour une journée
 */
function calculateDailyOccupancy(date) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const reservationsSheet = ss.getSheetByName(CONFIG.sheets.reservations);
  
  if (!reservationsSheet) {
    return {
      occupancyRate: 0,
      standardOccupancy: 0,
      confortOccupancy: 0,
      suiteOccupancy: 0,
      dailyRevenue: 0
    };
  }
  
  // Récupérer toutes les réservations
  const data = reservationsSheet.getDataRange().getValues();
  const headers = data[0];
  
  // Trouver les indices des colonnes nécessaires
  const checkInIndex = headers.indexOf('Date arrivée');
  const checkOutIndex = headers.indexOf('Date départ');
  const roomTypeIndex = headers.indexOf('Type de chambre');
  const pricePerNightIndex = headers.indexOf('Prix par nuit');
  const statusIndex = headers.indexOf('Statut');
  
  // Compter les chambres occupées pour cette date
  let standardOccupied = 0;
  let confortOccupied = 0;
  let suiteOccupied = 0;
  let dailyRevenue = 0;
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const status = row[statusIndex];
    
    if (status !== 'confirmed') continue;
    
    const checkIn = new Date(row[checkInIndex]);
    const checkOut = new Date(row[checkOutIndex]);
    
    // Vérifier si la date se situe pendant le séjour
    if (date >= checkIn && date < checkOut) {
      const roomType = row[roomTypeIndex];
      const pricePerNight = row[pricePerNightIndex];
      
      // Compter l'occupation par type
      if (roomType === 'standard') {
        standardOccupied++;
      } else if (roomType === 'confort') {
        confortOccupied++;
      } else if (roomType === 'suite') {
        suiteOccupied++;
      }
      
      // Ajouter le revenu
      dailyRevenue += pricePerNight;
    }
  }
  
  // Calculer les taux d'occupation
  const standardRate = standardOccupied / CONFIG.roomTypes.standard.count;
  const confortRate = confortOccupied / CONFIG.roomTypes.confort.count;
  const suiteRate = suiteOccupied / CONFIG.roomTypes.suite.count;
  
  // Occupation globale
  const totalRooms = CONFIG.roomTypes.standard.count + CONFIG.roomTypes.confort.count + CONFIG.roomTypes.suite.count;
  const totalOccupied = standardOccupied + confortOccupied + suiteOccupied;
  const occupancyRate = totalOccupied / totalRooms;
  
  return {
    occupancyRate: occupancyRate,
    standardOccupancy: standardRate,
    confortOccupancy: confortRate,
    suiteOccupancy: suiteRate,
    dailyRevenue: dailyRevenue
  };
}

/**
 * Met à jour le tableau de bord
 */
function updateDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dashboardSheet = ss.getSheetByName(CONFIG.sheets.dashboard) || ss.insertSheet(CONFIG.sheets.dashboard);
  
  // Effacer le contenu existant
  dashboardSheet.clear();
  
  // Configurer la présentation
  dashboardSheet.setColumnWidth(1, 250);
  dashboardSheet.setColumnWidth(2, 150);
  dashboardSheet.setColumnWidth(3, 400);
  
  // Titre
  dashboardSheet.getRange('A1:C1').merge();
  dashboardSheet.getRange('A1').setValue(`TABLEAU DE BORD - ${CONFIG.hotelName}`);
  dashboardSheet.getRange('A1').setFontSize(18).setFontWeight('bold').setHorizontalAlignment('center');
  
  // Date de mise à jour
  dashboardSheet.getRange('A2:C2').merge();
  dashboardSheet.getRange('A2').setValue(`Dernière mise à jour: ${formatDate(new Date())}`);
  dashboardSheet.getRange('A2').setFontStyle('italic').setHorizontalAlignment('center');
  
  // Indicateurs clés
  dashboardSheet.getRange('A4').setValue('PERFORMANCES RÉCENTES (30 JOURS)');
  dashboardSheet.getRange('A4').setFontWeight('bold').setBackground('#eeeeee');
  
  // Récupérer les données d'occupation des 30 derniers jours
  const occupancySheet = ss.getSheetByName(CONFIG.sheets.occupancy);
  if (occupancySheet && occupancySheet.getLastRow() > 1) {
    const range = occupancySheet.getRange(Math.max(2, occupancySheet.getLastRow() - 30), 1, Math.min(30, occupancySheet.getLastRow() - 1), 6);
    const occupancyData = range.getValues();
    
    // Calculer les moyennes
    let totalOccupancy = 0;
    let totalRevenue = 0;
    
    for (const row of occupancyData) {
      totalOccupancy += row[1];
      totalRevenue += row[5];
    }
    
    const avgOccupancy = totalOccupancy / occupancyData.length;
    const avgRevenue = totalRevenue / occupancyData.length;
    const totalRevenueSum = totalRevenue;
    
    // Afficher les KPIs
    dashboardSheet.getRange('A5').setValue('Taux d\'occupation moyen:');
    dashboardSheet.getRange('B5').setValue(avgOccupancy);
    dashboardSheet.getRange('B5').setNumberFormat('0.00%');
    
    // Colorisation conditionnelle
    if (avgOccupancy >= 0.8) {
      dashboardSheet.getRange('B5').setBackground('#d9ead3'); // Vert
    } else if (avgOccupancy >= 0.4) {
      dashboardSheet.getRange('B5').setBackground('#fff2cc'); // Jaune
    } else {
      dashboardSheet.getRange('B5').setBackground('#f4cccc'); // Rouge
    }
    
    dashboardSheet.getRange('A6').setValue('Revenu journalier moyen:');
    dashboardSheet.getRange('B6').setValue(avgRevenue);
    dashboardSheet.getRange('B6').setNumberFormat('0.00€');
    
    dashboardSheet.getRange('A7').setValue('Revenu total sur la période:');
    dashboardSheet.getRange('B7').setValue(totalRevenueSum);
    dashboardSheet.getRange('B7').setNumberFormat('0.00€');
    
    // Ajouter des insights
    dashboardSheet.getRange('A9').setValue('INSIGHTS & RECOMMANDATIONS');
    dashboardSheet.getRange('A9').setFontWeight('bold').setBackground('#eeeeee');
    
    let insight;
    if (avgOccupancy >= 0.8) {
      insight = 'Le taux d\'occupation est excellent. Envisagez d\'augmenter les prix de base pour maximiser les revenus.';
    } else if (avgOccupancy >= 0.6) {
      insight = 'Bon taux d\'occupation. Les prix actuels semblent bien positionnés.';
    } else if (avgOccupancy >= 0.4) {
      insight = 'Taux d\'occupation modéré. Surveillez la tendance et envisagez des promotions ciblées.';
    } else {
      insight = 'Taux d\'occupation faible. Recommandation: réduire les prix ou lancer des offres promotionnelles.';
    }
    
    dashboardSheet.getRange('A10').setValue(insight);
    
    // Créer un graphique d'occupation
    if (occupancyData.length > 0) {
      createOccupancyChart(dashboardSheet, occupancySheet);
    }
  } else {
    dashboardSheet.getRange('A5').setValue('Données insuffisantes pour l\'analyse.');
  }
}

/**
 * Crée un graphique pour le tableau de bord
 */
function createOccupancyChart(dashboardSheet, occupancySheet) {
  // Nombre de lignes à utiliser
  const numRows = Math.min(30, occupancySheet.getLastRow() - 1);
  const startRow = Math.max(2, occupancySheet.getLastRow() - numRows);
  
  // Créer un graphique en courbes
  const chartBuilder = dashboardSheet.newChart();
  chartBuilder
    .setChartType(Charts.ChartType.LINE)
    .addRange(occupancySheet.getRange(startRow, 1, numRows, 1))  // Dates
    .addRange(occupancySheet.getRange(startRow, 2, numRows, 1))  // Taux occupation
    .setPosition(12, 1, 0, 0)
    .setOption('title', 'Évolution du Taux d\'Occupation')
    .setOption('hAxis', {title: 'Date'})
    .setOption('vAxis', {title: 'Taux d\'occupation', format: 'percent'})
    .setOption('width', 600)
    .setOption('height', 350);
  
  // Ajouter le graphique
  dashboardSheet.insertChart(chartBuilder.build());
  
  // Ajouter un graphique de revenus
  const revenueChartBuilder = dashboardSheet.newChart();
  revenueChartBuilder
    .setChartType(Charts.ChartType.COLUMN)
    .addRange(occupancySheet.getRange(startRow, 1, numRows, 1))  // Dates
    .addRange(occupancySheet.getRange(startRow, 6, numRows, 1))  // Revenus
    .setPosition(12, 1, 0, 380)
    .setOption('title', 'Revenus Journaliers')
    .setOption('hAxis', {title: 'Date'})
    .setOption('vAxis', {title: 'Revenus (€)'})
    .setOption('width', 600)
    .setOption('height', 350);
  
  dashboardSheet.insertChart(revenueChartBuilder.build());
}

/**
 * Vérifie s'il faut envoyer des alertes d'occupation
 */
function checkOccupancyAlerts(date) {
  // Vérifier l'occupation pour les 7 prochains jours
  const nextWeek = new Date(date.getTime() + 7 * 24*60*60*1000);
  let lowOccupancyDays = 0;
  let averageOccupancy = 0;
  
  for (let i = 0; i < 7; i++) {
    const checkDate = new Date(date.getTime() + i * 24*60*60*1000);
    const occupancyData = calculateDailyOccupancy(checkDate);
    
    if (occupancyData.occupancyRate < CONFIG.thresholds.lowOccupancy) {
      lowOccupancyDays++;
    }
    
    averageOccupancy += occupancyData.occupancyRate;
  }
  
  averageOccupancy /= 7;
  
  // Envoyer une alerte si plus de la moitié des jours ont une faible occupation
  if (lowOccupancyDays >= 4 || averageOccupancy < CONFIG.thresholds.lowOccupancy) {
    sendLowOccupancyAlert(date, nextWeek, averageOccupancy, lowOccupancyDays);
  }
}

/**
 * Envoie une alerte de faible occupation
 */
function sendLowOccupancyAlert(fromDate, toDate, averageOccupancy, lowDays) {
  const recipientEmail = CONFIG.email.alertRecipients;
  if (!recipientEmail) return;
  
  const subject = `ALERTE: Faible occupation prévue du ${formatDate(fromDate)} au ${formatDate(toDate)}`;
  
  const body = `
    Bonjour,
    
    Une faible occupation est prévue pour la semaine prochaine:
    
    - Taux d'occupation moyen: ${(averageOccupancy * 100).toFixed(1)}%
    - Jours avec occupation inférieure à ${CONFIG.thresholds.lowOccupancy * 100}%: ${lowDays}/7
    
    Recommandations:
    1. Envisager des réductions de prix pour stimuler la demande
    2. Lancer une campagne promotionnelle
    3. Proposer des offres spéciales aux clients réguliers
    
    Pour plus de détails, consultez le tableau de bord.
    
    Cordialement,
    Système HotelSim
  `;
  
  try {
    MailApp.sendEmail(recipientEmail, subject, body);
    Logger.log("Alerte d'occupation envoyée à " + recipientEmail);
  } catch (e) {
    Logger.log("Erreur lors de l'envoi de l'email: " + e.toString());
  }
}

/**
 * Met à jour la feuille de revenus (pour analyse avancée)
 */
function updateRevenueSheet(date) {
  // Implémenter selon les besoins
}

/**
 * Fonction utilitaire pour formater les dates
 */
function formatDate(date) {
  return Utilities.formatDate(date, Session.getScriptTimeZone(), "dd/MM/yyyy");
}

/**
 * Calcule le nombre de nuits entre deux dates
 */
function calculateNights(checkIn, checkOut) {
  const oneDay = 24 * 60 * 60 * 1000; // Milliseconds in a day
  return Math.round(Math.abs((checkOut - checkIn) / oneDay));
}

/**
 * Récupère les données d'occupation 
 */
function getOccupancyData() {
  // Simulé pour l'exemple
  return [];
}

/**
 * Vérifie si une chambre est disponible
 */
function isRoomAvailable(roomType, checkIn, checkOut, occupancyData) {
  // Dans cette version simplifiée, on suppose une disponibilité de 80%
  return Math.random() > 0.2;
}

/**
 * Calcule le taux d'occupation pour une date donnée
 */
function getOccupancyRateForDate(date, occupancyData) {
  // Simulé pour l'exemple
  const seasonFactor = determineSeason(date) === 'high' ? 0.3 : 0;
  return Math.random() * 0.5 + seasonFactor;
}

/**
 * Met à jour les données d'occupation
 */
function updateOccupancyData(occupancyData, reservation) {
  // Simulé pour l'exemple
}

/**
 * Fonction déclenchée quotidiennement par un déclencheur
 */
function dailyUpdate() {
  runSimulation();
} 