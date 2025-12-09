from flask import Flask, request, jsonify
import requests
import json
import threading
import time
from datetime import datetime
import schedule
from urllib.parse import urlparse

app = Flask(__name__)

# İstek geçmişini saklamak için
request_history = []

# Kayıtlı API konfigürasyonları
saved_apis = {
    "default": {
        "name": "Email to User API",
        "url": "https://email-to-user.onrender.com/email_to_user",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        },
        "data_type": "json",  # json, form, params
        "data": {
            "email": "{email}",
            "dev": "@Z4usXcode"
        }
    }
}

# Aktif schedule'lar
active_schedules = {}

def validate_url(url):
    """URL doğrulama"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def make_api_request(api_config, custom_data=None):
    """API'ye istek gönderen fonksiyon"""
    try:
        url = api_config["url"]
        method = api_config.get("method", "GET").upper()
        headers = api_config.get("headers", {})
        data_type = api_config.get("data_type", "json")
        
        # Data'yı hazırla
        data = api_config.get("data", {})
        if custom_data:
            # Custom data ile merge et
            if isinstance(data, dict) and isinstance(custom_data, dict):
                data.update(custom_data)
            else:
                data = custom_data
        
        print(f"[{datetime.now()}] {api_config['name']} için istek gönderiliyor...")
        print(f"URL: {url}")
        print(f"Method: {method}")
        print(f"Data: {data}")
        
        response = None
        timeout = api_config.get("timeout", 10)
        
        if method == "GET":
            if data_type == "params" and data:
                response = requests.get(url, params=data, headers=headers, timeout=timeout)
            else:
                response = requests.get(url, headers=headers, timeout=timeout)
                
        elif method == "POST":
            if data_type == "json":
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif data_type == "form":
                response = requests.post(url, data=data, headers=headers, timeout=timeout)
            elif data_type == "params":
                response = requests.post(url, params=data, headers=headers, timeout=timeout)
            else:
                response = requests.post(url, data=json.dumps(data), headers=headers, timeout=timeout)
                
        elif method == "PUT":
            if data_type == "json":
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            else:
                response = requests.put(url, data=data, headers=headers, timeout=timeout)
                
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=timeout)
        
        # Response'u işle
        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_name": api_config["name"],
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds() if response else None,
            "headers": dict(response.headers) if response else {},
            "response": {}
        }
        
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                result["response"] = response.json()
            else:
                result["response"] = {"text": response.text[:500]}  # İlk 500 karakter
        except:
            result["response"] = {"text": "Response parse edilemedi"}
        
        # Geçmişe ekle (max 100 kayıt)
        request_history.append(result)
        if len(request_history) > 100:
            request_history.pop(0)
            
        print(f"[{datetime.now()}] İstek tamamlandı. Durum: {response.status_code}")
        return result
        
    except Exception as e:
        error_result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_name": api_config.get("name", "Unknown API"),
            "url": api_config.get("url", ""),
            "method": api_config.get("method", "GET"),
            "status_code": "ERROR",
            "response_time": None,
            "headers": {},
            "response": {"error": str(e)}
        }
        request_history.append(error_result)
        if len(request_history) > 100:
            request_history.pop(0)
        print(f"[{datetime.now()}] Hata: {str(e)}")
        return error_result

def schedule_api_request(api_name, api_config, interval_minutes=5, custom_data=None):
    """Periyodik API isteklerini planlayan fonksiyon"""
    def job():
        make_api_request(api_config, custom_data)
    
    # Bu API için schedule'ı temizle
    if api_name in active_schedules:
        active_schedules[api_name] = False
    
    # Yeni schedule oluştur
    schedule.every(interval_minutes).minutes.do(job)
    
    print(f"[{datetime.now()}] {api_name} için {interval_minutes} dakikada bir istek planlandı")
    
    # İlk isteği hemen gönder
    threading.Thread(target=make_api_request, args=(api_config, custom_data)).start()
    
    # Schedule loop'u çalıştır
    active_schedules[api_name] = True
    while active_schedules.get(api_name, False):
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def index():
    """Ana sayfa"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>📡 Gelişmiş API Test Aracı</title>
        <style>
            * { box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            .header {
                background: white;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            .header h1 {
                margin: 0;
                color: #333;
                font-size: 2.5em;
            }
            .header p {
                color: #666;
                margin: 10px 0 0 0;
            }
            .card {
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 20px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 20px;
            }
            .tab-buttons {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }
            .tab-button {
                padding: 12px 24px;
                background: #f0f0f0;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s;
            }
            .tab-button:hover {
                background: #e0e0e0;
            }
            .tab-button.active {
                background: #667eea;
                color: white;
            }
            .tab-content {
                display: none;
            }
            .tab-content.active {
                display: block;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #444;
            }
            input, select, textarea {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                transition: border 0.3s;
            }
            input:focus, select:focus, textarea:focus {
                border-color: #667eea;
                outline: none;
            }
            textarea {
                min-height: 120px;
                font-family: monospace;
                resize: vertical;
            }
            .button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 14px 28px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: transform 0.2s, box-shadow 0.2s;
                width: 100%;
            }
            .button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            .button.secondary {
                background: #6c757d;
            }
            .button.danger {
                background: #dc3545;
            }
            .button.success {
                background: #28a745;
            }
            .button-group {
                display: flex;
                gap: 10px;
                margin-top: 10px;
            }
            .button-group .button {
                flex: 1;
            }
            .history-item {
                border-left: 4px solid #667eea;
                padding: 15px;
                margin-bottom: 10px;
                background: #f8f9fa;
                border-radius: 0 8px 8px 0;
            }
            .history-item.success {
                border-left-color: #28a745;
            }
            .history-item.error {
                border-left-color: #dc3545;
            }
            .status-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                margin-right: 10px;
            }
            .status-200 { background: #d4edda; color: #155724; }
            .status-ERROR { background: #f8d7da; color: #721c24; }
            .status-other { background: #fff3cd; color: #856404; }
            .json-view {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-top: 10px;
                font-family: monospace;
                font-size: 12px;
                max-height: 200px;
                overflow-y: auto;
                white-space: pre-wrap;
            }
            .small-text {
                font-size: 12px;
                color: #666;
                margin-top: 5px;
            }
            .api-list {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            .api-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border: 2px solid #e0e0e0;
                cursor: pointer;
                transition: all 0.3s;
            }
            .api-card:hover {
                border-color: #667eea;
                transform: translateY(-2px);
            }
            .api-card h4 {
                margin: 0 0 10px 0;
                color: #333;
            }
            .api-card p {
                margin: 5px 0;
                font-size: 13px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📡 Gelişmiş API Test Aracı</h1>
                <p>API'lerinizi test edin, otomatik istekler planlayın ve sonuçları takip edin</p>
            </div>
            
            <div class="tab-buttons">
                <button class="tab-button active" onclick="showTab('tab-test')">🚀 Test API</button>
                <button class="tab-button" onclick="showTab('tab-schedule')">⏰ Schedule</button>
                <button class="tab-button" onclick="showTab('tab-saved')">💾 Kayıtlı API'ler</button>
                <button class="tab-button" onclick="showTab('tab-history')">📊 Geçmiş</button>
            </div>
            
            <!-- Test API Tab -->
            <div id="tab-test" class="tab-content active card">
                <h2>API Test Et</h2>
                <div class="grid">
                    <div>
                        <div class="form-group">
                            <label>API Adı:</label>
                            <input type="text" id="api-name" placeholder="API için bir isim verin">
                        </div>
                        
                        <div class="form-group">
                            <label>URL:</label>
                            <input type="url" id="api-url" placeholder="https://api.example.com/endpoint" required>
                        </div>
                        
                        <div class="form-group">
                            <label>Method:</label>
                            <select id="api-method">
                                <option value="GET">GET</option>
                                <option value="POST" selected>POST</option>
                                <option value="PUT">PUT</option>
                                <option value="DELETE">DELETE</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Data Type:</label>
                            <select id="api-data-type">
                                <option value="json">JSON</option>
                                <option value="form">Form Data</option>
                                <option value="params">URL Params</option>
                            </select>
                        </div>
                    </div>
                    
                    <div>
                        <div class="form-group">
                            <label>Headers (JSON formatında):</label>
                            <textarea id="api-headers">{"Content-Type": "application/json"}</textarea>
                            <div class="small-text">Örnek: {"Authorization": "Bearer token", "Content-Type": "application/json"}</div>
                        </div>
                        
                        <div class="form-group">
                            <label>Data/Payload (JSON formatında):</label>
                            <textarea id="api-data">{"email": "test@example.com"}</textarea>
                            <div class="small-text">Değişkenler için {variable} şeklinde kullanın</div>
                        </div>
                        
                        <div class="button-group">
                            <button class="button success" onclick="testApi()">🚀 Test Et</button>
                            <button class="button secondary" onclick="saveApi()">💾 Kaydet</button>
                        </div>
                    </div>
                </div>
                
                <div id="test-result" style="margin-top: 20px;"></div>
            </div>
            
            <!-- Schedule Tab -->
            <div id="tab-schedule" class="tab-content card">
                <h2>Periyodik İstek Planla</h2>
                <div class="grid">
                    <div>
                        <div class="form-group">
                            <label>API Seç:</label>
                            <select id="schedule-api" onchange="loadApiForSchedule()">
                                <option value="">API seçin...</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Interval (dakika):</label>
                            <input type="number" id="schedule-interval" min="1" value="5">
                        </div>
                        
                        <div class="form-group">
                            <label>Custom Data (opsiyonel, JSON):</label>
                            <textarea id="schedule-custom-data" placeholder='{"email": "dynamic@email.com"}'></textarea>
                        </div>
                        
                        <div class="button-group">
                            <button class="button success" onclick="startSchedule()">▶️ Başlat</button>
                            <button class="button danger" onclick="stopSchedule()">⏹️ Durdur</button>
                        </div>
                    </div>
                    
                    <div>
                        <h3>Aktif Schedule'lar</h3>
                        <div id="active-schedules"></div>
                    </div>
                </div>
            </div>
            
            <!-- Saved APIs Tab -->
            <div id="tab-saved" class="tab-content card">
                <h2>Kayıtlı API'ler</h2>
                <div class="api-list" id="saved-apis-list"></div>
            </div>
            
            <!-- History Tab -->
            <div id="tab-history" class="tab-content card">
                <h2>İstek Geçmişi</h2>
                <div class="button-group">
                    <button class="button secondary" onclick="loadHistory()">🔄 Yenile</button>
                    <button class="button danger" onclick="clearHistory()">🗑️ Temizle</button>
                </div>
                <div id="history-list" style="margin-top: 20px;"></div>
            </div>
        </div>
        
        <script>
            // Tab yönetimi
            function showTab(tabId) {
                // Butonları güncelle
                document.querySelectorAll('.tab-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');
                
                // İçerikleri güncelle
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                document.getElementById(tabId).classList.add('active');
                
                // Tab'a özel verileri yükle
                if (tabId === 'tab-saved') loadSavedApis();
                if (tabId === 'tab-history') loadHistory();
                if (tabId === 'tab-schedule') loadScheduleApis();
            }
            
            // API test et
            async function testApi() {
                const apiConfig = {
                    name: document.getElementById('api-name').value || 'Test API',
                    url: document.getElementById('api-url').value,
                    method: document.getElementById('api-method').value,
                    data_type: document.getElementById('api-data-type').value
                };
                
                // Headers'ı parse et
                try {
                    apiConfig.headers = JSON.parse(document.getElementById('api-headers').value);
                } catch {
                    apiConfig.headers = {};
                }
                
                // Data'yı parse et
                try {
                    apiConfig.data = JSON.parse(document.getElementById('api-data').value);
                } catch {
                    apiConfig.data = {};
                }
                
                if (!apiConfig.url) {
                    alert('URL gerekli!');
                    return;
                }
                
                const response = await fetch('/test-api', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(apiConfig)
                });
                
                const result = await response.json();
                displayTestResult(result);
            }
            
            // Test sonucunu göster
            function displayTestResult(result) {
                const statusClass = result.status_code === 200 ? 'success' : 
                                  result.status_code === 'ERROR' ? 'error' : 'other';
                
                const html = `
                    <div class="history-item ${statusClass}">
                        <div>
                            <span class="status-badge status-${result.status_code}">
                                ${result.status_code}
                            </span>
                            <strong>${result.api_name}</strong>
                            <small>${result.timestamp}</small>
                        </div>
                        <div><strong>URL:</strong> ${result.url}</div>
                        <div><strong>Method:</strong> ${result.method}</div>
                        <div><strong>Response Time:</strong> ${result.response_time || 'N/A'}s</div>
                        <div><strong>Response:</strong></div>
                        <div class="json-view">${JSON.stringify(result.response, null, 2)}</div>
                    </div>
                `;
                
                document.getElementById('test-result').innerHTML = html;
                loadHistory(); // Geçmişi güncelle
            }
            
            // API kaydet
            async function saveApi() {
                const apiConfig = {
                    name: document.getElementById('api-name').value || 'New API',
                    url: document.getElementById('api-url').value,
                    method: document.getElementById('api-method').value,
                    data_type: document.getElementById('api-data-type').value
                };
                
                try {
                    apiConfig.headers = JSON.parse(document.getElementById('api-headers').value);
                } catch {
                    apiConfig.headers = {};
                }
                
                try {
                    apiConfig.data = JSON.parse(document.getElementById('api-data').value);
                } catch {
                    apiConfig.data = {};
                }
                
                if (!apiConfig.url) {
                    alert('URL gerekli!');
                    return;
                }
                
                const response = await fetch('/save-api', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(apiConfig)
                });
                
                const result = await response.json();
                alert(result.message);
                loadSavedApis();
            }
            
            // Kayıtlı API'leri yükle
            async function loadSavedApis() {
                const response = await fetch('/get-apis');
                const apis = await response.json();
                
                let html = '';
                for (const [key, api] of Object.entries(apis)) {
                    html += `
                        <div class="api-card" onclick="loadApiToForm('${key}')">
                            <h4>${api.name}</h4>
                            <p><strong>URL:</strong> ${api.url}</p>
                            <p><strong>Method:</strong> ${api.method}</p>
                            <p><strong>Type:</strong> ${api.data_type}</p>
                        </div>
                    `;
                }
                
                document.getElementById('saved-apis-list').innerHTML = html || '<p>Kayıtlı API bulunamadı.</p>';
            }
            
            // Forma API yükle
            function loadApiToForm(apiKey) {
                fetch('/get-api/' + apiKey)
                    .then(r => r.json())
                    .then(api => {
                        document.getElementById('api-name').value = api.name;
                        document.getElementById('api-url').value = api.url;
                        document.getElementById('api-method').value = api.method;
                        document.getElementById('api-data-type').value = api.data_type || 'json';
                        document.getElementById('api-headers').value = JSON.stringify(api.headers || {}, null, 2);
                        document.getElementById('api-data').value = JSON.stringify(api.data || {}, null, 2);
                        showTab('tab-test');
                    });
            }
            
            // Schedule için API'leri yükle
            async function loadScheduleApis() {
                const response = await fetch('/get-apis');
                const apis = await response.json();
                
                const select = document.getElementById('schedule-api');
                select.innerHTML = '<option value="">API seçin...</option>';
                
                for (const [key, api] of Object.entries(apis)) {
                    select.innerHTML += `<option value="${key}">${api.name}</option>`;
                }
                
                loadActiveSchedules();
            }
            
            // Seçilen API'yi schedule formuna yükle
            function loadApiForSchedule() {
                const apiKey = document.getElementById('schedule-api').value;
                if (!apiKey) return;
                
                fetch('/get-api/' + apiKey)
                    .then(r => r.json())
                    .then(api => {
                        document.getElementById('schedule-custom-data').value = JSON.stringify(api.data || {}, null, 2);
                    });
            }
            
            // Schedule başlat
            async function startSchedule() {
                const apiKey = document.getElementById('schedule-api').value;
                const interval = document.getElementById('schedule-interval').value;
                
                if (!apiKey) {
                    alert('API seçin!');
                    return;
                }
                
                let customData = null;
                try {
                    customData = JSON.parse(document.getElementById('schedule-custom-data').value);
                } catch (e) {
                    // custom data yoksa veya geçersizse boş bırak
                }
                
                const response = await fetch('/start-schedule', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        api_key: apiKey,
                        interval: parseInt(interval),
                        custom_data: customData
                    })
                });
                
                const result = await response.json();
                alert(result.message);
                loadActiveSchedules();
            }
            
            // Schedule durdur
            async function stopSchedule() {
                const apiKey = document.getElementById('schedule-api').value;
                
                if (!apiKey) {
                    alert('API seçin!');
                    return;
                }
                
                const response = await fetch('/stop-schedule/' + apiKey, {
                    method: 'POST'
                });
                
                const result = await response.json();
                alert(result.message);
                loadActiveSchedules();
            }
            
            // Aktif schedule'ları yükle
            async function loadActiveSchedules() {
                const response = await fetch('/active-schedules');
                const schedules = await response.json();
                
                let html = '';
                for (const [key, active] of Object.entries(schedules)) {
                    if (active) {
                        html += `<div class="history-item success">▶️ ${key} - Aktif</div>`;
                    }
                }
                
                document.getElementById('active-schedules').innerHTML = html || '<p>Aktif schedule bulunamadı.</p>';
            }
            
            // Geçmişi yükle
            async function loadHistory() {
                const response = await fetch('/history');
                const history = await response.json();
                
                let html = '';
                history.slice().reverse().slice(0, 20).forEach(req => {
                    const statusClass = req.status_code === 200 ? 'success' : 
                                      req.status_code === 'ERROR' ? 'error' : 'other';
                    
                    html += `
                        <div class="history-item ${statusClass}">
                            <div>
                                <span class="status-badge status-${req.status_code}">
                                    ${req.status_code}
                                </span>
                                <strong>${req.api_name}</strong>
                                <small>${req.timestamp}</small>
                            </div>
                            <div><strong>URL:</strong> ${req.url}</div>
                            <div><strong>Method:</strong> ${req.method}</div>
                            <div><strong>Response:</strong></div>
                            <div class="json-view">${JSON.stringify(req.response, null, 2)}</div>
                        </div>
                    `;
                });
                
                document.getElementById('history-list').innerHTML = html || '<p>Geçmiş bulunamadı.</p>';
            }
            
            // Geçmişi temizle
            async function clearHistory() {
                if (!confirm('Geçmişi temizlemek istediğinize emin misiniz?')) return;
                
                const response = await fetch('/clear-history', { method: 'POST' });
                const result = await response.json();
                alert(result.message);
                loadHistory();
            }
            
            // Sayfa yüklenince
            window.onload = function() {
                loadSavedApis();
                loadScheduleApis();
                loadActiveSchedules();
                
                // Her 30 saniyede bir aktif schedule'ları kontrol et
                setInterval(loadActiveSchedules, 30000);
            };
        </script>
    </body>
    </html>
    """

# API Endpoints
@app.route('/test-api', methods=['POST'])
def test_api():
    """API test et"""
    data = request.json
    if not data.get('url'):
        return jsonify({"error": "URL gerekli"}), 400
    
    result = make_api_request(data)
    return jsonify(result)

@app.route('/save-api', methods=['POST'])
def save_api():
    """API kaydet"""
    data = request.json
    
    # URL doğrulama
    if not validate_url(data.get('url', '')):
        return jsonify({"error": "Geçersiz URL"}), 400
    
    # Benzersiz key oluştur
    import hashlib
    api_key = hashlib.md5(f"{data['name']}{data['url']}".encode()).hexdigest()[:8]
    
    saved_apis[api_key] = data
    return jsonify({"message": "API kaydedildi", "api_key": api_key})

@app.route('/get-apis')
def get_apis():
    """Kayıtlı API'leri getir"""
    return jsonify(saved_apis)

@app.route('/get-api/<api_key>')
def get_api(api_key):
    """Belirli bir API'yi getir"""
    if api_key in saved_apis:
        return jsonify(saved_apis[api_key])
    return jsonify({"error": "API bulunamadı"}), 404

@app.route('/start-schedule', methods=['POST'])
def start_schedule():
    """Schedule başlat"""
    data = request.json
    api_key = data.get('api_key')
    interval = data.get('interval', 5)
    custom_data = data.get('custom_data')
    
    if api_key not in saved_apis:
        return jsonify({"error": "API bulunamadı"}), 404
    
    # Arka planda schedule thread'ini başlat
    thread = threading.Thread(
        target=schedule_api_request,
        args=(api_key, saved_apis[api_key], interval, custom_data),
        daemon=True
    )
    thread.start()
    
    return jsonify({
        "message": f"{saved_apis[api_key]['name']} için {interval} dakikada bir istekler başlatıldı",
        "status": "started"
    })

@app.route('/stop-schedule/<api_key>', methods=['POST'])
def stop_schedule():
    """Schedule durdur"""
    api_key = request.view_args['api_key']
    
    if api_key in active_schedules:
        active_schedules[api_key] = False
        return jsonify({"message": f"{api_key} schedule durduruldu"})
    
    return jsonify({"error": "Aktif schedule bulunamadı"}), 404

@app.route('/active-schedules')
def get_active_schedules():
    """Aktif schedule'ları getir"""
    return jsonify(active_schedules)

@app.route('/history')
def get_history():
    """İstek geçmişini getir"""
    return jsonify(request_history)

@app.route('/clear-history', methods=['POST'])
def clear_history():
    """Geçmişi temizle"""
    request_history.clear()
    return jsonify({"message": "Geçmiş temizlendi"})

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║       📡 Gelişmiş API Test Aracı Başlatılıyor...        ║
    ╠══════════════════════════════════════════════════════════╣
    ║ Web Arayüzü: http://localhost:5000                       ║
    ║                                                          ║
    ║ Özellikler:                                              ║
    ║ ✅ API Test Etme                                         ║
    ║ ✅ JSON/Form/Params desteği                             ║
    ║ ✅ Custom Headers                                       ║
    ║ ✅ Periyodik İstekler (Schedule)                        ║
    ║ ✅ API Kaydetme                                         ║
    ║ ✅ İstek Geçmişi                                        ║
    ║                                                          ║
    ║ Kullanım:                                                ║
    ║ 1. Tarayıcıda http://localhost:5000 açın                ║
    ║ 2. "Test API" tabından yeni API ekleyin                 ║
    ║ 3. "Schedule" tabından otomatik istek planlayın         ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
        import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
