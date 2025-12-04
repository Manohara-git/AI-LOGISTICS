/**
 * AI Logistics System - Frontend JavaScript
 * Handles map visualization, API communication, and user interactions
 */

// Configuration
const API_BASE_URL = 'http://localhost:5000/api';
const DEFAULT_CENTER = [17.385044, 78.486671]; // Hyderabad
const DEFAULT_ZOOM = 12;

// State
let map = null;
let markers = {};
let routePolyline = null;
let selectedStops = [];
let locations = [];
let trafficOverlay = false;

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
  initializeMap();
  loadLocations();
  setupEventListeners();
  loadDeliveries();
  updateStats();
});

/**
 * Initialize Leaflet map
 */
function initializeMap() {
  map = L.map('map').setView(DEFAULT_CENTER, DEFAULT_ZOOM);

  // Add tile layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map);

  console.log('✓ Map initialized');
}

/**
 * Load available locations from API
 */
async function loadLocations() {
  try {
    const response = await fetch(`${API_BASE_URL}/locations`);
    const data = await response.json();
    locations = data.locations;

    // Populate dropdowns
    populateLocationDropdowns();

    // Add markers to map
    addLocationMarkers();

    console.log(`✓ Loaded ${locations.length} locations`);
  } catch (error) {
    console.error('Error loading locations:', error);
    showToast('Failed to load locations', 'error');
  }
}

/**
 * Populate location dropdowns
 */
function populateLocationDropdowns() {
  const startSelect = document.getElementById('startLocation');
  const addStopSelect = document.getElementById('addStopSelect');

  locations.forEach(loc => {
    // Add to start location (except Warehouse which is default)
    if (loc.name !== 'Warehouse') {
      const option = document.createElement('option');
      option.value = loc.name;
      option.textContent = loc.name;
      startSelect.appendChild(option);
    }

    // Add to stops dropdown (except Warehouse)
    if (loc.name !== 'Warehouse') {
      const option = document.createElement('option');
      option.value = loc.name;
      option.textContent = loc.name;
      addStopSelect.appendChild(option);
    }
  });
}

/**
 * Add location markers to map
 */
function addLocationMarkers() {
  locations.forEach(loc => {
    const icon = loc.type === 'warehouse'
      ? L.divIcon({
        html: '🏭',
        className: 'emoji-marker',
        iconSize: [30, 30]
      })
      : L.divIcon({
        html: '📍',
        className: 'emoji-marker',
        iconSize: [25, 25]
      });

    const marker = L.marker([loc.lat, loc.lng], { icon })
      .bindPopup(`
        <div style="text-align: center;">
          <strong>${loc.name}</strong><br>
          <small>${loc.area_type}</small>
        </div>
      `)
      .addTo(map);

    markers[loc.name] = marker;
  });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Add stop
  document.getElementById('addStopSelect').addEventListener('change', (e) => {
    const stop = e.target.value;
    if (stop && !selectedStops.includes(stop)) {
      selectedStops.push(stop);
      updateStopsList();
      highlightMarker(stop, true);
    }
    e.target.value = '';
  });

  // Optimize route
  document.getElementById('optimizeBtn').addEventListener('click', optimizeRoute);

  // Clear all
  document.getElementById('clearBtn').addEventListener('click', clearAll);

  // Center map
  document.getElementById('centerMapBtn').addEventListener('click', () => {
    map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
  });

  // Toggle traffic
  document.getElementById('toggleTrafficBtn').addEventListener('click', toggleTraffic);
}

/**
 * Update stops list UI
 */
function updateStopsList() {
  const stopsList = document.getElementById('stopsList');

  if (selectedStops.length === 0) {
    stopsList.innerHTML = '';
    return;
  }

  stopsList.innerHTML = selectedStops.map((stop, index) => `
    <div class="stop-item">
      <span class="stop-name">${index + 1}. ${stop}</span>
      <button class="remove-stop" onclick="removeStop('${stop}')">✕</button>
    </div>
  `).join('');
}

/**
 * Remove a stop
 */
function removeStop(stop) {
  selectedStops = selectedStops.filter(s => s !== stop);
  updateStopsList();
  highlightMarker(stop, false);
}

/**
 * Highlight/unhighlight marker
 */
function highlightMarker(locationName, highlight) {
  const marker = markers[locationName];
  if (marker) {
    if (highlight) {
      marker.setIcon(L.divIcon({
        html: '🎯',
        className: 'emoji-marker',
        iconSize: [30, 30]
      }));
    } else {
      marker.setIcon(L.divIcon({
        html: '📍',
        className: 'emoji-marker',
        iconSize: [25, 25]
      }));
    }
  }
}

/**
 * Optimize route
 */
async function optimizeRoute() {
  if (selectedStops.length === 0) {
    showToast('Please add at least one delivery stop', 'warning');
    return;
  }

  const start = document.getElementById('startLocation').value;
  const algorithm = document.getElementById('algorithm').value;
  const hour = parseInt(document.getElementById('hour').value);
  const day = parseInt(document.getElementById('day').value);
  const weather = document.getElementById('weather').value;

  // Show loading
  document.getElementById('loadingOverlay').style.display = 'flex';

  try {
    const response = await fetch(`${API_BASE_URL}/optimize-route`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start,
        stops: selectedStops,
        algorithm,
        hour,
        day,
        weather
      })
    });

    const data = await response.json();

    if (data.success) {
      displayRouteResults(data);
      drawRouteOnMap(data.route_coords);
      showToast('Route optimized successfully!', 'success');

      // Create delivery
      await createDelivery(start, selectedStops, data);
    } else {
      showToast(data.error || 'Optimization failed', 'error');
    }
  } catch (error) {
    console.error('Error optimizing route:', error);
    showToast('Failed to optimize route', 'error');
  } finally {
    document.getElementById('loadingOverlay').style.display = 'none';
  }
}

/**
 * Display route results
 */
function displayRouteResults(data) {
  const resultsSection = document.getElementById('resultsSection');
  const resultsContent = document.getElementById('routeResults');

  const algorithmNames = {
    'genetic': 'Genetic Algorithm',
    'nearest_neighbor': 'Nearest Neighbor',
    'dijkstra': 'Dijkstra',
    'a_star': 'A*'
  };

  resultsContent.innerHTML = `
    <div class="result-row">
      <span class="result-label">Algorithm:</span>
      <span class="result-value">${algorithmNames[data.algorithm]}</span>
    </div>
    <div class="result-row">
      <span class="result-label">Total Distance:</span>
      <span class="result-value">${data.distance} km</span>
    </div>
    <div class="result-row">
      <span class="result-label">Estimated Time:</span>
      <span class="result-value">${data.estimated_time_minutes} min</span>
    </div>
    <div class="result-row">
      <span class="result-label">Number of Stops:</span>
      <span class="result-value">${selectedStops.length}</span>
    </div>
    <div class="route-path">
      <strong>Route:</strong><br>
      ${data.route.join(' → ')}
    </div>
  `;

  resultsSection.style.display = 'block';
}

/**
 * Draw route on map
 */
function drawRouteOnMap(coords) {
  // Remove existing route
  if (routePolyline) {
    map.removeLayer(routePolyline);
  }

  // Draw new route
  routePolyline = L.polyline(coords, {
    color: '#6366f1',
    weight: 4,
    opacity: 0.8,
    smoothFactor: 1
  }).addTo(map);

  // Fit map to route
  map.fitBounds(routePolyline.getBounds(), { padding: [50, 50] });

  // Add numbered markers
  coords.forEach((coord, index) => {
    if (index > 0 && index < coords.length - 1) {
      L.marker(coord, {
        icon: L.divIcon({
          html: `<div style="background: #6366f1; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px;">${index}</div>`,
          className: 'numbered-marker',
          iconSize: [24, 24]
        })
      }).addTo(map);
    }
  });
}

/**
 * Clear all selections
 */
function clearAll() {
  selectedStops = [];
  updateStopsList();

  // Reset markers
  locations.forEach(loc => {
    if (loc.name !== 'Warehouse') {
      highlightMarker(loc.name, false);
    }
  });

  // Remove route
  if (routePolyline) {
    map.removeLayer(routePolyline);
    routePolyline = null;
  }

  // Hide results
  document.getElementById('resultsSection').style.display = 'none';

  // Reset map view
  map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);

  showToast('Cleared all selections', 'success');
}

/**
 * Toggle traffic overlay
 */
function toggleTraffic() {
  trafficOverlay = !trafficOverlay;
  const btn = document.getElementById('toggleTrafficBtn');

  if (trafficOverlay) {
    btn.style.background = 'rgba(99, 102, 241, 0.9)';
    showToast('Traffic overlay enabled', 'success');
    // In a real app, this would show traffic data
  } else {
    btn.style.background = 'rgba(30, 41, 59, 0.9)';
    showToast('Traffic overlay disabled', 'success');
  }
}

/**
 * Create delivery
 */
async function createDelivery(start, stops, routeData) {
  try {
    const response = await fetch(`${API_BASE_URL}/deliveries`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start,
        stops,
        distance: routeData.distance,
        estimated_time: routeData.estimated_time_minutes,
        algorithm: routeData.algorithm
      })
    });

    if (response.ok) {
      loadDeliveries();
      updateStats();
    }
  } catch (error) {
    console.error('Error creating delivery:', error);
  }
}

/**
 * Load deliveries
 */
async function loadDeliveries() {
  try {
    const response = await fetch(`${API_BASE_URL}/deliveries`);
    const data = await response.json();

    displayDeliveries(data.deliveries);
  } catch (error) {
    console.error('Error loading deliveries:', error);
  }
}

/**
 * Display deliveries list
 */
function displayDeliveries(deliveries) {
  const deliveriesList = document.getElementById('deliveriesList');

  if (deliveries.length === 0) {
    deliveriesList.innerHTML = '<p class="empty-state">No active deliveries</p>';
    return;
  }

  deliveriesList.innerHTML = deliveries.slice(-5).reverse().map(delivery => `
    <div class="delivery-item">
      <div class="delivery-header">
        <span class="delivery-id">Delivery #${delivery.id}</span>
        <span class="delivery-status status-${delivery.status}">${delivery.status}</span>
      </div>
      <div style="font-size: 0.75rem; color: var(--text-secondary); margin: 0.5rem 0;">
        ${delivery.stops.length} stops • ${delivery.start}
      </div>
      ${delivery.status !== 'completed' ? `
        <button class="btn-submit-delivery" onclick="openSubmitModal(${delivery.id})">
          ✓ Submit Delivery
        </button>
      ` : `
        <div style="font-size: 0.7rem; color: var(--success-color); margin-top: 0.5rem;">
          ✓ Delivered ${delivery.delivered_at ? new Date(delivery.delivered_at).toLocaleString() : ''}
        </div>
      `}
    </div>
  `).join('');
}

/**
 * Open submit delivery modal
 */
function openSubmitModal(deliveryId) {
  const modal = document.getElementById('submitModal');
  modal.style.display = 'flex';
  modal.dataset.deliveryId = deliveryId;

  // Reset form
  document.getElementById('recipientName').value = '';
  document.getElementById('deliveryNotes').value = '';
}

/**
 * Close submit delivery modal
 */
function closeSubmitModal() {
  document.getElementById('submitModal').style.display = 'none';
}

/**
 * Submit delivery confirmation
 */
async function submitDeliveryConfirmation() {
  const modal = document.getElementById('submitModal');
  const deliveryId = modal.dataset.deliveryId;
  const recipientName = document.getElementById('recipientName').value;
  const deliveryNotes = document.getElementById('deliveryNotes').value;

  if (!recipientName.trim()) {
    showToast('Please enter recipient name', 'warning');
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/deliveries/${deliveryId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        recipient_name: recipientName,
        delivery_notes: deliveryNotes,
        delivered_at: new Date().toISOString()
      })
    });

    const data = await response.json();

    if (data.success) {
      showToast('Delivery submitted successfully!', 'success');
      closeSubmitModal();
      loadDeliveries();
      updateStats();
    } else {
      showToast(data.error || 'Failed to submit delivery', 'error');
    }
  } catch (error) {
    console.error('Error submitting delivery:', error);
    showToast('Failed to submit delivery', 'error');
  }
}

/**
 * Update statistics
 */
async function updateStats() {
  try {
    const response = await fetch(`${API_BASE_URL}/analytics`);
    const data = await response.json();

    document.getElementById('totalDeliveries').textContent = data.total_deliveries;
    document.getElementById('activeRoutes').textContent = data.in_progress + data.pending;
  } catch (error) {
    console.error('Error updating stats:', error);
  }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Refresh deliveries and stats periodically
setInterval(() => {
  loadDeliveries();
  updateStats();
}, 30000); // Every 30 seconds