"""
Flask web server for live motorcycle location visualization.
Uses Leaflet.js for interactive map display.
"""

from flask import Flask, jsonify, render_template_string, request

# HTML template with Leaflet.js map
MAP_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Motorcycle Tracker - Live Map</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
        #map { position: absolute; top: 60px; bottom: 0; width: 100%; }
        .header {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: #2c3e50;
            color: white;
            display: flex;
            align-items: center;
            padding: 0 20px;
            z-index: 1000;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }
        .header h1 { margin: 0; font-size: 1.5em; flex-grow: 1; }
        .status-box {
            display: flex;
            gap: 20px;
            font-size: 0.9em;
        }
        .status-item { display: flex; align-items: center; gap: 5px; }
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .status-moving { background: #27ae60; }
        .status-rest { background: #e74c3c; }
        .info-panel {
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            min-width: 200px;
        }
        .info-panel h3 { margin: 0 0 10px 0; color: #2c3e50; }
        .info-row { display: flex; justify-content: space-between; margin: 5px 0; }
        .info-label { color: #7f8c8d; }
        .info-value { font-weight: bold; color: #2c3e50; }
        .last-update { font-size: 0.8em; color: #95a5a6; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏍️ Motorcycle Tracker</h1>
        <div class="status-box">
            <div class="status-item">
                <span class="status-dot" id="statusDot"></span>
                <span id="statusText">Loading...</span>
            </div>
            <div class="status-item">
                Refresh: {{ refresh_rate }}s
            </div>
        </div>
    </div>
    
    <div id="map"></div>
    
    <div class="info-panel">
        <h3>Current Position</h3>
        <div class="info-row">
            <span class="info-label">Latitude:</span>
            <span class="info-value" id="lat">-</span>
        </div>
        <div class="info-row">
            <span class="info-label">Longitude:</span>
            <span class="info-value" id="lng">-</span>
        </div>
        <div class="info-row">
            <span class="info-label">Speed:</span>
            <span class="info-value" id="speed">-</span>
        </div>
        <div class="last-update">Last update: <span id="lastUpdate">-</span></div>
    </div>

    <script>
        // Initialize map centered on Europe (will auto-center on first data)
        var map = L.map('map').setView([40.0, -8.0], 13);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        // Custom motorcycle icon
        var bikeIcon = L.divIcon({
            html: '<div style="font-size: 24px;">🏍️</div>',
            iconSize: [30, 30],
            iconAnchor: [15, 15],
            className: 'bike-marker'
        });
        
        var marker = null;
        var pathLine = null;
        var pathCoords = [];
        var firstLoad = true;
        
        function updatePosition() {
            fetch('/api/current')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error:', data.error);
                        return;
                    }
                    
                    var lat = parseFloat(data.lat);
                    var lng = parseFloat(data.lng);
                    
                    // Update info panel
                    document.getElementById('lat').textContent = lat.toFixed(6);
                    document.getElementById('lng').textContent = lng.toFixed(6);
                    document.getElementById('speed').textContent = data.speed + ' km/h';
                    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
                    
                    // Update status
                    var statusDot = document.getElementById('statusDot');
                    var statusText = document.getElementById('statusText');
                    if (data.status === 'MOVING') {
                        statusDot.className = 'status-dot status-moving';
                        statusText.textContent = 'Moving';
                    } else {
                        statusDot.className = 'status-dot status-rest';
                        statusText.textContent = 'At Rest';
                    }
                    
                    // Update or create marker
                    if (marker === null) {
                        marker = L.marker([lat, lng], {icon: bikeIcon}).addTo(map);
                    } else {
                        marker.setLatLng([lat, lng]);
                    }
                    
                    // Add to path
                    pathCoords.push([lat, lng]);
                    if (pathCoords.length > 100) {
                        pathCoords.shift(); // Keep last 100 points
                    }
                    
                    // Update path line
                    if (pathLine) {
                        map.removeLayer(pathLine);
                    }
                    if (pathCoords.length > 1) {
                        pathLine = L.polyline(pathCoords, {
                            color: '#3498db',
                            weight: 3,
                            opacity: 0.7
                        }).addTo(map);
                    }
                    
                    // Center map on first load
                    if (firstLoad) {
                        map.setView([lat, lng], 15);
                        firstLoad = false;
                    }
                })
                .catch(error => console.error('Fetch error:', error));
        }
        
        // Initial load
        updatePosition();
        
        // Auto-refresh
        setInterval(updatePosition, {{ refresh_rate }} * 1000);
    </script>
</body>
</html>
'''


def create_app(mapit_instance, refresh_rate=5):
    """Create Flask app with mapit instance for API calls."""
    app = Flask(__name__)
    app.config['mapit'] = mapit_instance
    app.config['refresh_rate'] = refresh_rate
    
    @app.route('/')
    def index():
        """Serve the map page."""
        return render_template_string(MAP_TEMPLATE, refresh_rate=app.config['refresh_rate'])
    
    @app.route('/api/current')
    def get_current():
        """Get current vehicle position."""
        try:
            mapit = app.config['mapit']
            lng, lat, speed, status, _ = mapit.checkStatus()
            return jsonify({
                'lng': lng,
                'lat': lat,
                'speed': speed,
                'status': status
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/history')
    def get_history():
        """Get location history from Oracle database."""
        try:
            mapit = app.config['mapit']
            limit = int(request.args.get('limit', 100))
            history = mapit.get_history_from_oracle(limit)
            return jsonify(history)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app


if __name__ == '__main__':
    print("This module should be imported by mapit.py")
    print("Usage: python mapit.py --serve-map --map-port 5000 --refresh-rate 5")
