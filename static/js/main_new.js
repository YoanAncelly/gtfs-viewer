/**
 * GTFS-RT Visualizer
 * Main JavaScript file for handling data fetching, processing and visualization
 */

// Global variables
let tripUpdatesData = [];
let vehiclePositionsData = [];
let alertsData = [];
let map = null;
let vehicleMap = null;
let vehicleMarkers = [];
let tripUpdatesTable = null;
let vehiclePositionsTable = null;
let configData = null;

// Initialize the application when the document is ready
$(document).ready(function() {
    // Initialize the maps
    initializeMaps();
    
    // Initialize DataTables
    initializeTables();
    
    // Load configuration
    loadConfig();
    
    // Load initial data
    loadAllData();
    
    // Set up navigation
    setupNavigation();
    
    // Set up filters
    setupFilters();
    
    // Set up auto-refresh every 30 seconds
    setInterval(loadAllData, 30000);
});

/**
 * Initialize Leaflet maps
 */
function initializeMaps() {
    // Dashboard map
    map = L.map('map').setView([48.8566, 2.3522], 12); // Default to Paris coordinates
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Vehicle positions map
    vehicleMap = L.map('vehicle-map').setView([48.8566, 2.3522], 12); // Default to Paris coordinates
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(vehicleMap);
}

/**
 * Initialize DataTables
 */
function initializeTables() {
    // Trip updates table
    tripUpdatesTable = $('#trip-updates-table').DataTable({
        columns: [
            { data: 'trip_id' },
            { data: 'route_id' },
            { data: 'stop_id' },
            { data: 'delay_minutes' },
            { data: 'arrival_time' },
            { data: 'departure_time' }
        ],
        order: [[3, 'desc']],
        pageLength: 10,
        lengthMenu: [10, 25, 50, 100],
        language: {
            search: 'Rechercher:',
            lengthMenu: 'Afficher _MENU_ entrées',
            info: 'Affichage de _START_ à _END_ sur _TOTAL_ entrées',
            infoEmpty: 'Aucune entrée à afficher',
            infoFiltered: '(filtré de _MAX_ entrées au total)',
            paginate: {
                first: 'Premier',
                last: 'Dernier',
                next: 'Suivant',
                previous: 'Précédent'
            }
        },
        responsive: true
    });
    
    // Vehicle positions table
    vehiclePositionsTable = $('#vehicle-positions-table').DataTable({
        columns: [
            { data: 'vehicle_id' },
            { data: 'trip_id' },
            { data: 'route_id' },
            { data: 'latitude' },
            { data: 'longitude' },
            { data: 'speed' },
            { data: 'bearing' },
            { data: 'current_status' },
            { data: 'timestamp' }
        ],
        order: [[1, 'asc']],
        pageLength: 10,
        lengthMenu: [10, 25, 50, 100],
        language: {
            search: 'Rechercher:',
            lengthMenu: 'Afficher _MENU_ entrées',
            info: 'Affichage de _START_ à _END_ sur _TOTAL_ entrées',
            infoEmpty: 'Aucune entrée à afficher',
            infoFiltered: '(filtré de _MAX_ entrées au total)',
            paginate: {
                first: 'Premier',
                last: 'Dernier',
                next: 'Suivant',
                previous: 'Précédent'
            }
        },
        responsive: true,
        createdRow: function(row, data, dataIndex) {
            // Add color based on status
            $(row).addClass(getMarkerClass(data.current_status));
        }
    });
}

/**
 * Set up navigation between sections
 */
function setupNavigation() {
    // Handle navigation clicks
    $('.nav-link[data-section]').click(function(e) {
        e.preventDefault();
        
        // Get the target section
        const targetSection = $(this).data('section');
        
        // Hide all sections and show the target section
        $('.section').removeClass('active');
        $('#' + targetSection).addClass('active');
        
        // Update active nav link
        $('.nav-link').removeClass('active');
        $(this).addClass('active');
        
        // Refresh maps if needed
        if (targetSection === 'dashboard' || targetSection === 'vehicle-positions') {
            setTimeout(function() {
                map.invalidateSize();
                vehicleMap.invalidateSize();
            }, 100);
        }
    });
    
    // Handle section links
    $('a[data-section]').click(function(e) {
        e.preventDefault();
        $('.nav-link[data-section="' + $(this).data('section') + '"]').click();
    });
}

/**
 * Set up filters for vehicle positions
 */
function setupFilters() {
    // Route filter change
    $('#route-filter').change(function() {
        const routeFilter = $(this).val();
        const statusFilter = $('#status-filter').val();
        
        // Update vehicle markers
        updateVehicleMarkers(vehiclePositionsData, routeFilter, statusFilter);
        
        // Filter the table
        vehiclePositionsTable.column(2).search(routeFilter === 'all' ? '' : routeFilter).draw();
    });
    
    // Status filter change
    $('#status-filter').change(function() {
        const routeFilter = $('#route-filter').val();
        const statusFilter = $(this).val();
        
        // Update vehicle markers
        updateVehicleMarkers(vehiclePositionsData, routeFilter, statusFilter);
        
        // Filter the table
        vehiclePositionsTable.column(7).search(statusFilter === 'all' ? '' : statusFilter).draw();
    });
}

/**
 * Load configuration data from the server
 */
function loadConfig() {
    $.ajax({
        url: '/api/config',
        method: 'GET',
        dataType: 'json',
        success: function(response) {
            configData = response;
            updateConfigInfo();
        },
        error: function(xhr, status, error) {
            console.error('Error loading configuration:', error);
        }
    });
}

/**
 * Update configuration info in the UI
 */
function updateConfigInfo() {
    if (!configData) return;
    
    const currentSource = configData.sources[configData.current_source];
    
    // Add source info to the dashboard
    const sourceInfo = $('<div class="alert alert-info mt-3">' +
        '<strong>Source actuelle:</strong> ' + currentSource.name +
        ' <button id="refresh-data" class="btn btn-sm btn-outline-primary ms-2"><i class="fas fa-sync-alt"></i> Rafraîchir</button>' +
        ' <a href="/config" class="btn btn-sm btn-outline-secondary ms-2"><i class="fas fa-cog"></i> Configuration</a>' +
        '</div>');
    
    // Check if the source info already exists
    if ($('#source-info').length === 0) {
        // Add it after the last-update paragraph
        $('#dashboard .row:first-child .col-12').append(sourceInfo.attr('id', 'source-info'));
    } else {
        // Update the existing source info
        $('#source-info').replaceWith(sourceInfo.attr('id', 'source-info'));
    }
    
    // Re-attach click handler
    $('#refresh-data').click(function() {
        refreshData();
    });
}

/**
 * Refresh data from the current source
 */
function refreshData() {
    // Show loading indicator
    const refreshBtn = $('#refresh-data');
    const originalHtml = refreshBtn.html();
    refreshBtn.html('<i class="fas fa-spinner fa-spin"></i> Rafraîchissement...').prop('disabled', true);
    
    $.ajax({
        url: '/api/refresh-data',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({}),
        dataType: 'json',
        success: function(response) {
            if (response.success) {
                // Reload all data
                loadAllData();
                
                // Show success message
                showNotification('success', 'Données rafraîchies avec succès');
            } else {
                showNotification('danger', 'Erreur lors du rafraîchissement des données: ' + (response.error || 'Erreur inconnue'));
            }
            refreshBtn.html(originalHtml).prop('disabled', false);
        },
        error: function(xhr, status, error) {
            showNotification('danger', 'Erreur lors du rafraîchissement des données: ' + error);
            refreshBtn.html(originalHtml).prop('disabled', false);
        }
    });
}

/**
 * Load all data from the API
 */
function loadAllData() {
    $.ajax({
        url: '/api/all-data',
        method: 'GET',
        dataType: 'json',
        success: function(response) {
            // Store the data
            if (response.trip_updates && response.trip_updates.data) {
                tripUpdatesData = response.trip_updates.data;
            }
            
            if (response.vehicle_positions && response.vehicle_positions.data) {
                vehiclePositionsData = response.vehicle_positions.data;
            }
            
            if (response.alerts && response.alerts.data) {
                alertsData = response.alerts.data;
            }
            
            // Update timestamps
            updateTimestamps(response);
            
            // Update UI components
            updateTripUpdatesUI(response.trip_updates);
            updateVehiclePositionsUI(response.vehicle_positions);
            updateAlertsUI(response.alerts);
            
            // Update vehicle markers
            const routeFilter = $('#route-filter').val() || 'all';
            const statusFilter = $('#status-filter').val() || 'all';
            updateVehicleMarkers(vehiclePositionsData, routeFilter, statusFilter);
            
            // Update route filter options
            updateRouteFilterOptions(vehiclePositionsData);
        },
        error: function(xhr, status, error) {
            console.error('Error loading data:', error);
            showNotification('danger', 'Erreur lors du chargement des données: ' + error);
        }
    });
}

/**
 * Update timestamps in the UI
 * @param {Object} data - Data object containing timestamps
 */
function updateTimestamps(data) {
    // Format the current time
    const now = new Date();
    const formattedTime = now.toLocaleString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    // Update the last update timestamp
    $('#last-update').text(formattedTime);
    $('.last-update').text(formattedTime);
    
    // Update feed timestamps if available
    if (data.trip_updates && data.trip_updates.header && data.trip_updates.header.timestamp_formatted) {
        $('#trip-update-timestamp').text(data.trip_updates.header.timestamp_formatted);
    }
    
    if (data.vehicle_positions && data.vehicle_positions.header && data.vehicle_positions.header.timestamp_formatted) {
        $('#vehicle-position-timestamp').text(data.vehicle_positions.header.timestamp_formatted);
    }
    
    if (data.alerts && data.alerts.header && data.alerts.header.timestamp_formatted) {
        $('#alert-timestamp').text(data.alerts.header.timestamp_formatted);
    }
}

/**
 * Update the trip updates UI
 * @param {Object} tripUpdates - Trip updates data
 */
function updateTripUpdatesUI(tripUpdates) {
    if (!tripUpdates || !tripUpdates.data) return;
    
    // Update dashboard stats
    $('#trip-count').text(tripUpdates.data.length);
    
    if (tripUpdates.stats) {
        $('#avg-delay').text(tripUpdates.stats.avg_delay_minutes + ' min');
        $('#max-delay').text(tripUpdates.stats.max_delay_minutes + ' min');
        
        // Update trip updates section stats
        $('#trip-update-count').text(tripUpdates.stats.count);
        $('#trip-avg-delay').text(tripUpdates.stats.avg_delay_minutes + ' min');
        $('#trip-max-delay').text(tripUpdates.stats.max_delay_minutes + ' min');
        $('#trip-min-delay').text(tripUpdates.stats.min_delay_minutes + ' min');
    }
    
    // Update delay chart
    if (tripUpdates.chart) {
        $('#delay-chart').attr('src', '/static/' + tripUpdates.chart + '?t=' + new Date().getTime());
        $('#trip-delay-chart').attr('src', '/static/' + tripUpdates.chart + '?t=' + new Date().getTime());
    }
    
    // Update trip updates table
    tripUpdatesTable.clear();
    tripUpdatesTable.rows.add(tripUpdates.data);
    tripUpdatesTable.draw();
}

/**
 * Update the vehicle positions UI
 * @param {Object} vehiclePositions - Vehicle positions data
 */
function updateVehiclePositionsUI(vehiclePositions) {
    if (!vehiclePositions || !vehiclePositions.data) return;
    
    // Update dashboard stats
    $('#vehicle-count').text(vehiclePositions.data.length);
    
    if (vehiclePositions.stats) {
        $('#avg-speed').text(vehiclePositions.stats.avg_speed ? vehiclePositions.stats.avg_speed + ' m/s' : 'N/A');
        $('#max-speed').text(vehiclePositions.stats.max_speed ? vehiclePositions.stats.max_speed + ' m/s' : 'N/A');
        
        // Update vehicle positions section stats
        $('#vehicle-position-count').text(vehiclePositions.stats.count);
        $('#vehicle-avg-speed').text(vehiclePositions.stats.avg_speed ? vehiclePositions.stats.avg_speed + ' m/s' : 'N/A');
        $('#vehicle-max-speed').text(vehiclePositions.stats.max_speed ? vehiclePositions.stats.max_speed + ' m/s' : 'N/A');
        $('#vehicle-min-speed').text(vehiclePositions.stats.min_speed ? vehiclePositions.stats.min_speed + ' m/s' : 'N/A');
    }
    
    // Update vehicle positions table
    vehiclePositionsTable.clear();
    vehiclePositionsTable.rows.add(vehiclePositions.data);
    vehiclePositionsTable.draw();
}

/**
 * Update the alerts UI
 * @param {Object} alerts - Alerts data
 */
function updateAlertsUI(alerts) {
    if (!alerts) return;
    
    // Update dashboard stats
    $('#alert-count').text(alerts.count || 0);
    
    // Update alert preview
    let alertPreviewHtml = '';
    
    if (alerts.data && alerts.data.length > 0) {
        // Show the first alert in the preview
        const firstAlert = alerts.data[0];
        alertPreviewHtml = `
            <div class="alert-preview-item">
                <h6>${firstAlert.header_text || 'Alerte sans titre'}</h6>
                <p class="mb-0">${firstAlert.description_text || 'Pas de description'}</p>
            </div>
        `;
        
        if (alerts.data.length > 1) {
            alertPreviewHtml += `<p class="text-muted mt-2">${alerts.data.length - 1} autre(s) alerte(s)...</p>`;
        }
    } else {
        alertPreviewHtml = '<p>Aucune alerte active</p>';
    }
    
    $('#alert-preview').html(alertPreviewHtml);
    
    // Update alerts container
    const alertsContainer = $('#alerts-container');
    alertsContainer.empty();
    
    if (alerts.data && alerts.data.length > 0) {
        alerts.data.forEach(function(alert) {
            // Determine alert class based on effect
            let alertClass = 'warning';
            if (alert.effect === 'NO_SERVICE' || alert.effect === 'SIGNIFICANT_DELAYS') {
                alertClass = 'danger';
            } else if (alert.effect === 'DETOUR' || alert.effect === 'STOP_MOVED') {
                alertClass = 'warning';
            } else if (alert.effect === 'ADDITIONAL_SERVICE' || alert.effect === 'MODIFIED_SERVICE') {
                alertClass = 'info';
            }
            
            // Create affected entities list
            let entitiesList = '';
            if (alert.affected_entities && alert.affected_entities.length > 0) {
                entitiesList = '<ul class="list-group list-group-flush mt-2">';
                alert.affected_entities.forEach(function(entity) {
                    let entityInfo = [];
                    if (entity.agency_id) entityInfo.push('Agence: ' + entity.agency_id);
                    if (entity.route_id) entityInfo.push('Route: ' + entity.route_id);
                    if (entity.trip_id) entityInfo.push('Trajet: ' + entity.trip_id);
                    if (entity.stop_id) entityInfo.push('Arrêt: ' + entity.stop_id);
                    
                    entitiesList += '<li class="list-group-item">' + entityInfo.join(', ') + '</li>';
                });
                entitiesList += '</ul>';
            }
            
            // Create alert card
            const alertCard = $(`
                <div class="col-md-6 mb-4">
                    <div class="card border-${alertClass}">
                        <div class="card-header bg-${alertClass} text-white">
                            <h5 class="card-title mb-0">${alert.header_text || 'Alerte sans titre'}</h5>
                        </div>
                        <div class="card-body">
                            <p><strong>Cause:</strong> ${alert.cause}</p>
                            <p><strong>Effet:</strong> ${alert.effect}</p>
                            <p>${alert.description_text || 'Pas de description'}</p>
                            ${entitiesList}
                        </div>
                    </div>
                </div>
            `);
            
            alertsContainer.append(alertCard);
        });
    } else {
        alertsContainer.html('<div class="col-12"><div class="alert alert-info">Aucune alerte active</div></div>');
    }
}

/**
 * Update vehicle markers on the maps
 * @param {Array} vehicles - Vehicle positions data
 * @param {string} routeFilter - Route filter value
 * @param {string} statusFilter - Status filter value
 */
function updateVehicleMarkers(vehicles, routeFilter, statusFilter) {
    if (!vehicles) return;
    
    // Clear existing markers
    vehicleMarkers.forEach(function(marker) {
        map.removeLayer(marker);
        vehicleMap.removeLayer(marker);
    });
    vehicleMarkers = [];
    
    // Add new markers
    vehicles.forEach(function(vehicle) {
        // Skip if no position data
        if (!vehicle.latitude || !vehicle.longitude) return;
        
        // Apply filters
        if (routeFilter !== 'all' && vehicle.route_id !== routeFilter) return;
        if (statusFilter !== 'all' && vehicle.current_status !== statusFilter) return;
        
        // Create marker
        const markerClass = getMarkerClass(vehicle.current_status);
        const markerHtml = `
            <div class="vehicle-marker ${markerClass}">
                <i class="fas fa-bus"></i>
            </div>
        `;
        
        const markerIcon = L.divIcon({
            html: markerHtml,
            className: 'vehicle-marker-container',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
        
        // Create popup content
        const popupContent = `
            <div class="vehicle-popup">
                <h6>Véhicule ${vehicle.vehicle_id}</h6>
                <p><strong>Trajet:</strong> ${vehicle.trip_id}</p>
                <p><strong>Route:</strong> ${vehicle.route_id}</p>
                <p><strong>Position:</strong> ${vehicle.latitude.toFixed(5)}, ${vehicle.longitude.toFixed(5)}</p>
                <p><strong>Vitesse:</strong> ${vehicle.speed ? vehicle.speed.toFixed(2) + ' m/s' : 'N/A'}</p>
                <p><strong>Direction:</strong> ${vehicle.bearing ? vehicle.bearing.toFixed(2) + '°' : 'N/A'}</p>
                <p><strong>Statut:</strong> ${getStatusText(vehicle.current_status)}</p>
                <p><strong>Horodatage:</strong> ${vehicle.timestamp || 'N/A'}</p>
            </div>
        `;
        
        // Create marker and add to maps
        const marker = L.marker([vehicle.latitude, vehicle.longitude], { icon: markerIcon })
            .bindPopup(popupContent);
        
        // Add to both maps
        marker.addTo(map);
        const markerCopy = L.marker([vehicle.latitude, vehicle.longitude], { icon: markerIcon })
            .bindPopup(popupContent)
            .addTo(vehicleMap);
        
        // Store markers
        vehicleMarkers.push(marker);
        vehicleMarkers.push(markerCopy);
    });
    
    // Fit bounds if there are markers
    if (vehicleMarkers.length > 0) {
        const group = L.featureGroup(vehicleMarkers);
        map.fitBounds(group.getBounds(), { padding: [50, 50] });
        vehicleMap.fitBounds(group.getBounds(), { padding: [50, 50] });
    }
}

/**
 * Get marker class based on vehicle status
 * @param {string} status - Vehicle status
 * @returns {string} CSS class for the marker
 */
function getMarkerClass(status) {
    if (status === 'STOPPED_AT') return 'marker-stopped';
    if (status === 'IN_TRANSIT_TO') return 'marker-transit';
    if (status === 'INCOMING_AT') return 'marker-incoming';
    return 'marker-unknown';
}

/**
 * Get human-readable status text
 * @param {string} status - Vehicle status
 * @returns {string} Human-readable status
 */
function getStatusText(status) {
    if (status === 'STOPPED_AT') return 'Arrêté';
    if (status === 'IN_TRANSIT_TO') return 'En transit';
    if (status === 'INCOMING_AT') return 'En approche';
    return 'Inconnu';
}

/**
 * Update route filter options based on available routes
 * @param {Array} vehicles - Vehicle positions data
 */
function updateRouteFilterOptions(vehicles) {
    if (!vehicles) return;
    
    // Get unique route IDs
    const routeIds = [];
    vehicles.forEach(function(vehicle) {
        if (vehicle.route_id && !routeIds.includes(vehicle.route_id)) {
            routeIds.push(vehicle.route_id);
        }
    });
    
    // Sort route IDs
    routeIds.sort();
    
    // Get current selection
    const currentSelection = $('#route-filter').val();
    
    // Update route filter options
    const routeFilter = $('#route-filter');
    routeFilter.empty();
    
    // Add 'All' option
    routeFilter.append('<option value="all">Toutes les routes</option>');
    
    // Add route options
    routeIds.forEach(function(routeId) {
        routeFilter.append(`<option value="${routeId}">${routeId}</option>`);
    });
    
    // Restore selection if possible
    if (currentSelection && (currentSelection === 'all' || routeIds.includes(currentSelection))) {
        routeFilter.val(currentSelection);
    }
}

/**
 * Show a notification message
 * @param {string} type - Notification type (success, danger, warning, info)
 * @param {string} message - Notification message
 */
function showNotification(type, message) {
    const notificationHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    // Check if there's already a notification container
    let notificationContainer = $('.notification-container');
    if (notificationContainer.length === 0) {
        notificationContainer = $('<div class="notification-container position-fixed top-0 end-0 p-3" style="z-index: 1050;"></div>');
        $('body').append(notificationContainer);
    }

    // Add the notification to the container
    const notification = $(notificationHtml);
    notificationContainer.append(notification);

    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        notification.alert('close');
    }, 5000);
}
