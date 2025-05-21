"""
Scale Manager Lite - Applicazione semplificata per Bilancia Dymo
---------------------------------------------------
Un'applicazione leggera per testare e gestire bilance Dymo M5/M10 via USB.

Features:
- Test di connessione e lettura del peso
- API RESTful per l'accesso ai dati da altre applicazioni
- Avvio automatico all'avvio di Windows
- Configurazione del server API
"""

import sys
import time
import json
import os
import logging
from datetime import datetime
import threading
import winreg

import usb.core
import usb.util
import usb.backend.libusb1
from flask import Flask, jsonify, request

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QGroupBox, QGridLayout, QSpinBox, QCheckBox,
    QMessageBox, QFileDialog, QStatusBar, QDialog, QTextEdit, QDialogButtonBox,
    QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont, QIcon

# Configurazione del logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scale_manager_lite.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ScaleManagerLite")

# Costanti per la bilancia Dymo
DYMO_VENDOR_ID = 0x0922
DYMO_PRODUCT_ID = 0x8003
MAX_ATTEMPTS = 5

# Nome dell'applicazione per il registro di Windows
APP_NAME = "ScaleManagerLite"
APP_PATH = os.path.abspath(sys.argv[0])

# Classe per gestire la bilancia
class ScaleDevice:
    def __init__(self):
        self.device = None
        self.endpoint = None
        self.connected = False
        self.last_weight = 0
        self.device_type = "Unknown"
        self.device_name = "Unknown Scale"
        self.backend = None
        
        # Inizializza il backend esplicitamente
        self._init_backend()
    
    def _init_backend(self):
        """Inizializza il backend libusb utilizzando la DLL nella stessa cartella dello script"""
        try:
            # Percorso alla DLL nella stessa cartella dello script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            dll_path = os.path.join(script_dir, "libusb-1.0.dll")
            
            logger.info(f"Usando DLL: {dll_path}")
            
            # Verifica che la DLL esista
            if not os.path.exists(dll_path):
                logger.error(f"ERRORE: DLL non trovata in {dll_path}")
                return False
            
            # Crea il backend in modo esplicito
            self.backend = usb.backend.libusb1.get_backend(find_library=lambda x: dll_path)
            
            if self.backend is None:
                logger.error("ERRORE: Impossibile creare il backend con la DLL specificata")
                return False
                
            logger.info("Backend libusb creato con successo")
            return True
            
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione del backend: {str(e)}")
            return False
    
    def find_usb_scale(self) -> bool:
        """Cerca una bilancia Dymo connessa via USB utilizzando il backend esplicito"""
        try:
            # Verifica che il backend sia stato inizializzato
            if self.backend is None:
                if not self._init_backend():
                    return False
            
            # Cerca la bilancia Dymo utilizzando il backend esplicito
            self.device = usb.core.find(
                idVendor=DYMO_VENDOR_ID, 
                idProduct=DYMO_PRODUCT_ID,
                backend=self.backend
            )
            
            if self.device is not None:
                # Se su Linux, potrebbe essere necessario detach il kernel driver
                if sys.platform.startswith('linux'):
                    if self.device.is_kernel_driver_active(0):
                        self.device.detach_kernel_driver(0)
                
                # Configura il dispositivo
                self.device.set_configuration()
                self.endpoint = self.device[0][(0,0)][0]
                self.connected = True
                self.device_type = "USB"
                self.device_name = "Dymo M5/M10"
                logger.info(f"Bilancia USB trovata: {self.device_name}")
                return True
            
            logger.warning("Bilancia Dymo non trovata")
            return False
            
        except Exception as e:
            logger.error(f"Errore nella ricerca della bilancia USB: {str(e)}")
            return False
    
    def read_weight(self) -> int:
        """Legge il peso dalla bilancia Dymo USB con controlli migliorati"""
        if not self.connected or self.device is None:
            return 0
            
        attempts = MAX_ATTEMPTS
        while attempts > 0:
            try:
                # Verifica lo stato della connessione prima di tentare la lettura
                if not self.is_device_connected():
                    logger.warning("Bilancia disconnessa durante la lettura")
                    self.connected = False
                    self.device = None
                    self.endpoint = None
                    return 0
                
                data = self.device.read(
                    self.endpoint.bEndpointAddress, 
                    self.endpoint.wMaxPacketSize,
                    timeout=1000
                )
                
                if data and len(data) >= 6:
                    # Per Dymo M5/M10: peso in grammi = data[4] + data[5] * 256
                    grams = data[4] + (256 * data[5])
                    self.last_weight = grams
                    logger.debug(f"Peso letto: {grams}g")
                    return grams
                else:
                    logger.warning(f"Dati letti non validi: {data}")
                    # Se riceviamo dati vuoti, potrebbe indicare disconnessione
                    if not data or len(data) == 0:
                        attempts -= 1
                        if attempts == 0:
                            logger.error("Dispositivo probabilmente disconnesso - dati vuoti")
                            self.connected = False
                            return 0
            except usb.core.USBError as e:
                attempts -= 1
                logger.warning(f"Errore lettura USB: {str(e)}. Tentativi rimasti: {attempts}")
                
                # Disconnessione o errore critico
                if "no such device" in str(e).lower() or "device disconnected" in str(e).lower():
                    logger.error("Dispositivo disconnesso")
                    self.connected = False
                    self.device = None
                    self.endpoint = None
                    return 0
                
                # Altrimenti prova a riconfigurare
                try:
                    self.device.set_configuration()
                except Exception as config_error:
                    logger.error(f"Errore nella riconfigurazione: {str(config_error)}")
                    self.connected = False
                    return 0
                    
                time.sleep(0.5)
                
        logger.error("Impossibile leggere il peso dalla bilancia dopo diversi tentativi")
        return 0
        
    def is_device_connected(self) -> bool:
        """Verifica se il dispositivo è ancora connesso"""
        if self.device is None:
            return False
            
        try:
            # Prova una semplice operazione sul dispositivo
            # Questa può sollevare un'eccezione se il dispositivo è disconnesso
            self.device.get_active_configuration()
            return True
        except Exception as e:
            logger.warning(f"Controllo connessione: dispositivo non raggiungibile - {str(e)}")
            return False
        
    def disconnect(self):
        """Disconnette la bilancia"""
        if self.device is not None:
            usb.util.dispose_resources(self.device)
            self.device = None
            self.endpoint = None
            self.connected = False
            logger.info("Bilancia disconnessa")


# Worker per la lettura della bilancia in un thread separato
class ScaleReaderWorker(QObject):
    weight_read = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    connected = pyqtSignal(bool, str)
    
    def __init__(self, scale):
        super().__init__()
        self.scale = scale
        self.running = False
        self.reconnect_timer = None
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3
        
    def run(self):
        """Esegue la lettura continua dalla bilancia con gestione migliorata delle disconnessioni"""
        self.running = True
        self.reconnect_timer = None
        self.consecutive_errors = 0
        
        # Prima ricerca dispositivo USB
        if not self.scale.connected:
            if self.scale.find_usb_scale():
                self.connected.emit(True, "USB")
                self.consecutive_errors = 0
            else:
                self.connected.emit(False, "")
                self.error_occurred.emit("Nessuna bilancia trovata")
                self.start_reconnect_timer()
                return
                
        # Lettura continua
        while self.running:
            try:
                if not self.scale.connected:
                    # Se non siamo connessi, prova a riconnettersi
                    if self.scale.find_usb_scale():
                        self.connected.emit(True, "USB")
                        self.consecutive_errors = 0
                    else:
                        # Se non ci riusciamo, attendi prima di riprovare
                        time.sleep(2)
                        self.consecutive_errors += 1
                        
                        if self.consecutive_errors >= self.max_consecutive_errors:
                            self.error_occurred.emit("Impossibile trovare la bilancia dopo diversi tentativi")
                            self.start_reconnect_timer()
                            return
                        continue
                
                # Tenta la lettura solo se connessi
                weight = self.scale.read_weight()
                
                # Se non siamo più connessi dopo il tentativo di lettura, usciamo dal ciclo
                if not self.scale.connected:
                    self.connected.emit(False, "")
                    self.error_occurred.emit("Bilancia disconnessa durante la lettura")
                    self.start_reconnect_timer()
                    return
                    
                # Leggiamo con successo, resettiamo il contatore errori
                self.consecutive_errors = 0
                self.weight_read.emit(weight)
                
            except Exception as e:
                logger.error(f"Errore nel ciclo di lettura: {str(e)}")
                self.consecutive_errors += 1
                
                if self.consecutive_errors >= self.max_consecutive_errors:
                    self.error_occurred.emit(f"Errore ripetuto di lettura: {str(e)}")
                    self.connected.emit(False, "")
                    self.start_reconnect_timer()
                    return
                    
            # Pausa tra le letture
            time.sleep(0.2)
            
    def start_reconnect_timer(self):
        """Avvia un timer per verificare periodicamente se la bilancia è stata collegata"""
        if self.reconnect_timer is None:
            self.reconnect_timer = QTimer()
            self.reconnect_timer.timeout.connect(self.attempt_reconnect)
            self.reconnect_timer.start(5000)  # Controlla ogni 5 secondi
            
    def attempt_reconnect(self):
        """Tenta di riconnettersi alla bilancia"""
        if not self.running:
            if self.reconnect_timer:
                self.reconnect_timer.stop()
                self.reconnect_timer = None
            return
            
        logger.info("Tentativo di riconnessione automatica alla bilancia...")
        
        if self.scale.find_usb_scale():
            self.connected.emit(True, "USB")
            # Riavvia il ciclo di lettura
            if self.reconnect_timer:
                self.reconnect_timer.stop()
                self.reconnect_timer = None
            # Riavvia il ciclo di lettura
            self.consecutive_errors = 0
            self.run()
            
    def stop(self):
        """Ferma il worker e i timer"""
        self.running = False
        if self.reconnect_timer:
            self.reconnect_timer.stop()
            self.reconnect_timer = None


# Classe per l'API RESTful
class ScaleAPI:
    def __init__(self, scale, host='0.0.0.0', port=5000):
        self.app = Flask(__name__)
        self.scale = scale
        self.host = host
        self.port = port
        self.thread = None
        self.running = False
        self.setup_routes()
        
    def setup_routes(self):
        """Configura i percorsi dell'API"""
        
        @self.app.route('/api/weight', methods=['GET'])
        def get_weight():
            """Ottiene l'ultimo peso misurato"""
            weight = self.scale.last_weight
            return jsonify({
                "weight": weight,
                "unit": "g",
                "timestamp": datetime.now().isoformat(),
                "connected": self.scale.connected
            })
            
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Ottiene lo stato della bilancia"""
            return jsonify({
                "connected": self.scale.connected,
                "device_type": self.scale.device_type,
                "device_name": self.scale.device_name,
                "api_running": self.running
            })
            
        # Aggiunta di una route di base per la documentazione
        @self.app.route('/', methods=['GET'])
        def api_docs():
            """Pagina di documentazione API basilare"""
            docs_html = f"""
            <html>
            <head>
                <title>Scale Manager API</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #0078d7; }}
                    h2 {{ color: #333; margin-top: 20px; }}
                    pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 3px; }}
                    .endpoint {{ margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
                </style>
            </head>
            <body>
                <h1>Scale Manager API</h1>
                <p>Benvenuto nell'API REST di Scale Manager. Usa i seguenti endpoint per interagire con la bilancia:</p>
                
                <div class="endpoint">
                    <h2>GET /api/weight</h2>
                    <p>Restituisce il peso attuale misurato dalla bilancia.</p>
                    <p><strong>URL:</strong> <a href="/api/weight">/api/weight</a></p>
                    <p><strong>Esempio di risposta:</strong></p>
                    <pre>{{
  "weight": 245,
  "unit": "g",
  "timestamp": "2025-05-21T21:45:30.123456",
  "connected": true
}}</pre>
                </div>
                
                <div class="endpoint">
                    <h2>GET /api/status</h2>
                    <p>Restituisce lo stato attuale della bilancia e dell'API.</p>
                    <p><strong>URL:</strong> <a href="/api/status">/api/status</a></p>
                    <p><strong>Esempio di risposta:</strong></p>
                    <pre>{{
  "connected": true,
  "device_type": "USB",
  "device_name": "Dymo M5/M10",
  "api_running": true
}}</pre>
                </div>
            </body>
            </html>
            """
            return docs_html
            
    def start(self):
        """Avvia il server API in un thread separato"""
        if self.running:
            return
            
        def run_app():
            try:
                self.running = True
                self.app.run(host=self.host, port=self.port)
            except Exception as e:
                logger.error(f"Errore nell'avvio del server API: {str(e)}")
            finally:
                self.running = False
            
        self.thread = threading.Thread(target=run_app)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"API server avviato su http://{self.host}:{self.port}")
        
    def stop(self):
        """Ferma il server API"""
        self.running = False
        # Nota: per una corretta implementazione, sarebbe necessario 
        # usare un server WSGI come Waitress che supporti l'arresto pulito.
        logger.info("API server fermato")


# Classe per gestire l'avvio automatico
class AutoStartManager:
    def __init__(self, app_name, app_path):
        self.app_name = app_name
        self.app_path = app_path
        self.startup_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
    def is_autostart_enabled(self):
        """Verifica se l'avvio automatico è abilitato"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.startup_key)
            value, _ = winreg.QueryValueEx(key, self.app_name)
            winreg.CloseKey(key)
            return value == self.app_path
        except WindowsError:
            return False
            
    def enable_autostart(self):
        """Abilita l'avvio automatico all'avvio di Windows"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.startup_key, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, self.app_path)
            winreg.CloseKey(key)
            logger.info(f"Avvio automatico abilitato per {self.app_name}")
            return True
        except WindowsError as e:
            logger.error(f"Errore nell'abilitazione dell'avvio automatico: {str(e)}")
            return False
            
    def disable_autostart(self):
        """Disabilita l'avvio automatico all'avvio di Windows"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.startup_key, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, self.app_name)
            winreg.CloseKey(key)
            logger.info(f"Avvio automatico disabilitato per {self.app_name}")
            return True
        except WindowsError as e:
            logger.error(f"Errore nella disabilitazione dell'avvio automatico: {str(e)}")
            return False


# Classe per gestire le impostazioni
class SettingsManager:
    def __init__(self, settings_file="scale_manager_settings.json"):
        self.settings_file = settings_file
        self.settings = {
            "api": {
                "host": "0.0.0.0",
                "port": 5000,
                "autostart": True
            },
            "application": {
                "start_minimized": False,
                "autostart_windows": False
            }
        }
        self.load_settings()
        
    def load_settings(self):
        """Carica le impostazioni da file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Aggiorna solo le chiavi esistenti
                    if "api" in loaded_settings:
                        self.settings["api"].update(loaded_settings["api"])
                    if "application" in loaded_settings:
                        self.settings["application"].update(loaded_settings["application"])
                logger.info("Impostazioni caricate")
        except Exception as e:
            logger.error(f"Errore nel caricamento delle impostazioni: {str(e)}")
            
    def save_settings(self):
        """Salva le impostazioni su file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            logger.info("Impostazioni salvate")
            return True
        except Exception as e:
            logger.error(f"Errore nel salvataggio delle impostazioni: {str(e)}")
            return False
            
    def get_api_settings(self):
        """Ottiene le impostazioni dell'API"""
        return self.settings["api"]
        
    def get_application_settings(self):
        """Ottiene le impostazioni dell'applicazione"""
        return self.settings["application"]
        
    def update_api_settings(self, host=None, port=None, autostart=None):
        """Aggiorna le impostazioni dell'API"""
        if host is not None:
            self.settings["api"]["host"] = host
        if port is not None:
            self.settings["api"]["port"] = port
        if autostart is not None:
            self.settings["api"]["autostart"] = autostart
        return self.save_settings()
        
    def update_application_settings(self, start_minimized=None, autostart_windows=None):
        """Aggiorna le impostazioni dell'applicazione"""
        if start_minimized is not None:
            self.settings["application"]["start_minimized"] = start_minimized
        if autostart_windows is not None:
            self.settings["application"]["autostart_windows"] = autostart_windows
        return self.save_settings()


# Dialog per il setup esterno API
class SetupHelpDialog(QDialog):
    def __init__(self, api_settings, parent=None):
        super().__init__(parent)
        self.api_settings = api_settings
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia del dialog di setup"""
        self.setWindowTitle("Setup API Esterno - Scale Manager Lite")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Titolo
        title_label = QLabel("🔧 Setup API per Accesso Esterno")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FF9A3C; margin-bottom: 15px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Area di testo per i contenuti dell'aiuto
        self.help_text = QTextEdit()
        self.help_text.setReadOnly(True)
        self.help_text.setFont(QFont("Consolas", 9))
        
        # Contenuto dell'aiuto per setup esterno
        help_content = f"""
<h3 style="color: #FF9A3C;">🌐 Configurazione Rete per Accesso Esterno</h3>

<div style="background-color: #3F3F46; padding: 15px; margin: 10px 0; border-radius: 5px;">
<h4 style="color: #FFD700;">📍 Step 1: Configurazione Host</h4>

<p><strong>Opzioni disponibili:</strong></p>
<ul>
<li><code>0.0.0.0</code> - <span style="color: #6BFF72;">CONSIGLIATO</span> - Accessibile da qualsiasi dispositivo sulla rete</li>
<li><code>127.0.0.1</code> - Solo accesso locale (stesso computer)</li>
<li><code>192.168.x.x</code> - IP specifico del computer sulla rete locale</li>
</ul>

<p><strong>⚠️ Importante:</strong> Per accesso da altri dispositivi, usa <code>0.0.0.0</code></p>
</div>

<div style="background-color: #3F3F46; padding: 15px; margin: 10px 0; border-radius: 5px;">
<h4 style="color: #FFD700;">🔍 Step 2: Trova l'IP del Computer</h4>

<p><strong>Su Windows:</strong></p>
<pre style="background-color: #2d2d30; color: #6BFF72; padding: 8px; border-radius: 3px;">
# Apri Command Prompt (cmd) e digita:
ipconfig

# Cerca "Indirizzo IPv4" 
# Esempio output:
#   Indirizzo IPv4. . . . . . . . . : 192.168.1.100
</pre>

<p><strong>Su Linux/Mac:</strong></p>
<pre style="background-color: #2d2d30; color: #6BFF72; padding: 8px; border-radius: 3px;">
# Apri Terminal e digita:
ip addr show  # Linux
ifconfig      # Mac

# Cerca inet 192.168.x.x
</pre>
</div>

<div style="background-color: #3F3F46; padding: 15px; margin: 10px 0; border-radius: 5px;">
<h4 style="color: #FFD700;">🔥 Step 3: Configurazione Firewall Windows</h4>

<p><strong>Opzione A - Rapida (Disabilita temporaneamente):</strong></p>
<pre style="background-color: #2d2d30; color: #FFD700; padding: 8px; border-radius: 3px;">
1. Pannello di Controllo > Sistema e Sicurezza > Windows Defender Firewall
2. "Attiva o disattiva Windows Defender Firewall"
3. Disattiva temporaneamente per "Rete privata"
4. ⚠️ RIATTIVA dopo il test!
</pre>

<p><strong>Opzione B - Sicura (Crea regola specifica):</strong></p>
<pre style="background-color: #2d2d30; color: #6BFF72; padding: 8px; border-radius: 3px;">
1. Pannello di Controllo > Sistema e Sicurezza > Windows Defender Firewall
2. "Impostazioni avanzate"
3. "Regole connessioni in entrata" > "Nuova regola"
4. Tipo: "Porta" > Avanti
5. "TCP" > "Porte locali specifiche" > {self.api_settings['port']} > Avanti
6. "Consenti connessione" > Avanti
7. Seleziona "Privato" > Avanti
8. Nome: "Scale Manager API" > Fine
</pre>
</div>

<div style="background-color: #3F3F46; padding: 15px; margin: 10px 0; border-radius: 5px;">
<h4 style="color: #FFD700;">📱 Step 4: Test da Altri Dispositivi</h4>

<p><strong>URL per test:</strong></p>
<pre style="background-color: #2d2d30; color: #6BFF72; padding: 8px; border-radius: 3px;">
# Sostituisci [IP-COMPUTER] con l'IP trovato nello Step 2
http://[IP-COMPUTER]:{self.api_settings['port']}/

# Esempi:
http://192.168.1.100:{self.api_settings['port']}/
http://192.168.1.100:{self.api_settings['port']}/api/weight
http://192.168.1.100:{self.api_settings['port']}/api/status
</pre>

<p><strong>Test con smartphone/tablet:</strong></p>
<ol>
<li>Connetti il dispositivo alla stessa rete WiFi</li>
<li>Apri il browser</li>
<li>Vai all'URL sopra (sostituendo [IP-COMPUTER])</li>
<li>Dovresti vedere la pagina di documentazione API</li>
</ol>
</div>

<div style="background-color: #3F3F46; padding: 15px; margin: 10px 0; border-radius: 5px;">
<h4 style="color: #FFD700;">🐛 Risoluzione Problemi</h4>

<p><strong>❌ Non riesco ad accedere dall'esterno:</strong></p>
<ul>
<li>Verifica che l'host sia impostato su <code>0.0.0.0</code></li>
<li>Controlla che l'API sia attiva (verde nell'applicazione)</li>
<li>Verifica l'IP del computer (può cambiare)</li>
<li>Controlla le impostazioni firewall</li>
<li>Assicurati che i dispositivi siano sulla stessa rete</li>
</ul>

<p><strong>❌ Errore "Connessione rifiutata":</strong></p>
<ul>
<li>Firewall di Windows blocca la connessione</li>
<li>Porta {self.api_settings['port']} non accessibile</li>
<li>Prova una porta diversa (es. 8080, 3000)</li>
</ul>

<p><strong>❌ "Timeout" o caricamento infinito:</strong></p>
<ul>
<li>IP errato o dispositivo non raggiungibile</li>
<li>Rete WiFi diversa</li>
<li>Router blocca comunicazioni interne</li>
</ul>
</div>

<div style="background-color: #3F3F46; padding: 15px; margin: 10px 0; border-radius: 5px;">
<h4 style="color: #FFD700;">💡 Suggerimenti Avanzati</h4>

<p><strong>🔒 Per maggiore sicurezza:</strong></p>
<ul>
<li>Usa <code>127.0.0.1</code> se non serve accesso esterno</li>
<li>Cambia la porta default se usi più applicazioni</li>
<li>Crea regole firewall specifiche invece di disabilitarlo</li>
</ul>

<p><strong>📊 Per uso professionale:</strong></p>
<ul>
<li>Considera l'uso di un reverse proxy (nginx)</li>
<li>Implementa HTTPS per connessioni sicure</li>
<li>Aggiungi log dettagliati per monitoraggio</li>
</ul>
</div>

<h3 style="color: #FF9A3C;">✅ Checklist Finale</h3>
<ul style="color: #CCCCCC;">
<li>☐ Host impostato su <code>0.0.0.0</code></li>
<li>☐ API attiva (stato verde)</li>
<li>☐ IP computer identificato</li>
<li>☐ Firewall configurato correttamente</li>
<li>☐ Test dal browser locale: <code>http://127.0.0.1:{self.api_settings['port']}</code></li>
<li>☐ Test da dispositivo esterno: <code>http://[IP-COMPUTER]:{self.api_settings['port']}</code></li>
</ul>
"""
        
        self.help_text.setHtml(help_content)
        self.help_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d30;
                color: #ffffff;
                border: 1px solid #3f3f46;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout.addWidget(self.help_text)
        
        # Pulsanti
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        
        # Pulsante per test locale
        test_local_btn = QPushButton("🧪 Test Locale")
        test_local_btn.clicked.connect(self.test_local_api)
        test_local_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 15px; border-radius: 3px;")
        button_box.addButton(test_local_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        copy_ip_btn = QPushButton("📋 Copia Info IP")
        copy_ip_btn.clicked.connect(self.copy_ip_info)
        copy_ip_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px 15px; border-radius: 3px;")
        button_box.addButton(copy_ip_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        layout.addWidget(button_box)
        
        # Applica stile al dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d30;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1c86d9;
            }
        """)
        
    def test_local_api(self):
        """Apre l'API nel browser per test locale"""
        import webbrowser
        local_url = f"http://127.0.0.1:{self.api_settings['port']}"
        webbrowser.open(local_url)
        
    def copy_ip_info(self):
        """Copia informazioni IP negli appunti"""
        import socket
        
        try:
            # Ottieni IP locale
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            info = f"""Informazioni IP per Scale Manager API:

Host configurato: {self.api_settings['host']}
Porta: {self.api_settings['port']}
IP locale rilevato: {local_ip}

URL per test locale:
http://127.0.0.1:{self.api_settings['port']}

URL per accesso esterno:
http://{local_ip}:{self.api_settings['port']}

Endpoint API:
http://{local_ip}:{self.api_settings['port']}/api/weight
http://{local_ip}:{self.api_settings['port']}/api/status"""
            
            # Copia negli appunti
            import subprocess
            subprocess.run(['clip'], input=info.encode('utf-8'), shell=True)
            
            QMessageBox.information(self, "Info Copiate", 
                "Le informazioni IP sono state copiate negli appunti!\n\n"
                "Incollale dove serve per accedere all'API.")
                
        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Impossibile ottenere IP: {str(e)}")


# Dialog personalizzato per l'aiuto API semplice
class APIHelpDialog(QDialog):
    def __init__(self, api_settings, parent=None):
        super().__init__(parent)
        self.api_settings = api_settings
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia del dialog di aiuto"""
        self.setWindowTitle("Aiuto API - Scale Manager Lite")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Titolo
        title_label = QLabel("📡 API Scale Manager Lite")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #4DC0FF; margin-bottom: 15px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Area di testo per i contenuti dell'aiuto
        self.help_text = QTextEdit()
        self.help_text.setReadOnly(True)
        self.help_text.setFont(QFont("Consolas", 10))
        
        # Contenuto dell'aiuto base
        base_url = f"http://{self.api_settings['host']}:{self.api_settings['port']}"
        help_content = f"""
<h3 style="color: #4DC0FF;">🔗 Informazioni di Accesso</h3>
<p><strong>URL Base:</strong> <a href="{base_url}" style="color: #6BFF72;">{base_url}</a></p>

<h3 style="color: #4DC0FF;">📋 Endpoint Disponibili</h3>

<div style="background-color: #3F3F46; padding: 10px; margin: 10px 0; border-radius: 5px;">
<h4 style="color: #FFD700;">⚖️ GET /api/weight</h4>
<p><strong>URL:</strong> <a href="{base_url}/api/weight" style="color: #6BFF72;">{base_url}/api/weight</a></p>
<p>Restituisce il peso attuale della bilancia in formato JSON.</p>
</div>

<div style="background-color: #3F3F46; padding: 10px; margin: 10px 0; border-radius: 5px;">
<h4 style="color: #FFD700;">📊 GET /api/status</h4>
<p><strong>URL:</strong> <a href="{base_url}/api/status" style="color: #6BFF72;">{base_url}/api/status</a></p>
<p>Restituisce lo stato della bilancia e dell'API.</p>
</div>

<h3 style="color: #4DC0FF;">💻 Esempi di Utilizzo</h3>
<pre style="background-color: #2d2d30; color: #6BFF72; padding: 8px; border-radius: 3px;">
# Command Line
curl {base_url}/api/weight

# Browser
Vai a: {base_url}/
</pre>
"""
        
        self.help_text.setHtml(help_content)
        self.help_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d30;
                color: #ffffff;
                border: 1px solid #3f3f46;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout.addWidget(self.help_text)
        
        # Pulsanti
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        
        # Pulsante per aprire nel browser
        open_browser_btn = QPushButton("🌐 Apri nel Browser")
        open_browser_btn.clicked.connect(self.open_in_browser)
        open_browser_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 15px; border-radius: 3px;")
        button_box.addButton(open_browser_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        layout.addWidget(button_box)
        
        # Applica stile al dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d30;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
        """)
        
    def open_in_browser(self):
        """Apre l'API nel browser predefinito"""
        import webbrowser
        base_url = f"http://{self.api_settings['host']}:{self.api_settings['port']}"
        webbrowser.open(base_url)


# UI principale
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Inizializzazione degli oggetti principali
        self.scale = ScaleDevice()
        self.settings_manager = SettingsManager()
        
        # Inizializza l'API con le impostazioni salvate
        api_settings = self.settings_manager.get_api_settings()
        self.api = ScaleAPI(self.scale, api_settings["host"], api_settings["port"])
        
        # Autostart dell'API se abilitato
        if api_settings["autostart"]:
            self.api.start()
        
        # Inizializza il gestore dell'avvio automatico
        self.autostart_manager = AutoStartManager(APP_NAME, APP_PATH)
        
        # Sincronizza le impostazioni di avvio automatico con Windows
        app_settings = self.settings_manager.get_application_settings()
        if app_settings["autostart_windows"] != self.autostart_manager.is_autostart_enabled():
            if app_settings["autostart_windows"]:
                self.autostart_manager.enable_autostart()
            else:
                self.autostart_manager.disable_autostart()
        
        # Thread per la lettura della bilancia
        self.scale_thread = QThread()
        self.scale_worker = ScaleReaderWorker(self.scale)
        self.scale_worker.moveToThread(self.scale_thread)
        
        # Connessione dei segnali
        self.scale_thread.started.connect(self.scale_worker.run)
        self.scale_worker.weight_read.connect(self.update_weight_display)
        self.scale_worker.error_occurred.connect(self.show_error)
        self.scale_worker.connected.connect(self.update_connection_status)
        
        # Timer per rilevamento automatico della bilancia
        self.auto_detect_timer = QTimer(self)
        self.auto_detect_timer.timeout.connect(self.auto_detect_scale)
        
        # Setup dell'interfaccia utente
        self.setup_ui()
        
        # Avvio minimizzato se configurato
        if app_settings["start_minimized"]:
            self.showMinimized()
        
        # Timer per aggiornamento UI
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(1000)  # Aggiorna UI ogni secondo
        
        # Avvio del thread di lettura
        self.scale_thread.start()
        
        # Avvio del timer di rilevamento automatico
        self.auto_detect_timer.start(10000)  # Controlla ogni 10 secondi

    def auto_detect_scale(self):
        """Verifica periodicamente se la bilancia è connessa"""
        if not self.scale.connected:
            logger.debug("Verifica automatica presenza bilancia...")
            if self.scale.find_usb_scale():
                self.statusBar().showMessage("Bilancia rilevata automaticamente")
                self.update_connection_status(True, "USB")
        else:
            # Se siamo già connessi, verifichiamo che la connessione sia ancora valida
            if not self.scale.is_device_connected():
                logger.warning("Bilancia disconnessa rilevata dal controllo periodico")
                self.scale.connected = False
                self.scale.device = None
                self.scale.endpoint = None
                self.update_connection_status(False, "")
        
    def setup_ui(self):
        """Configurazione dell'interfaccia utente"""
        self.setWindowTitle("Scale Manager Lite")
        self.setMinimumSize(450, 400)
        
        # Widget principale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principale
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)  # Aumenta lo spazio tra i widget
        
        # Sezione principale - Display peso
        weight_group = QGroupBox("Peso Attuale")
        weight_layout = QVBoxLayout(weight_group)
        weight_layout.setSpacing(10)  # Aumenta lo spazio tra gli elementi
        
        # Display grande del peso
        self.weight_label = QLabel("0")
        self.weight_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.weight_label.setFont(QFont("Arial", 60, QFont.Weight.Bold))
        self.weight_label.setStyleSheet("color: #4DC0FF;") # Colore azzurro per il peso
        weight_layout.addWidget(self.weight_label)
        
        # Unità di misura
        self.unit_label = QLabel("g")
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.unit_label.setFont(QFont("Arial", 24))
        self.unit_label.setStyleSheet("color: #CCCCCC;") # Colore grigio chiaro
        weight_layout.addWidget(self.unit_label)
        
        # Stato connessione
        self.connection_label = QLabel("Non connesso")
        self.connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_label.setStyleSheet("color: #FF6B6B;") # Colore rosso per disconnesso
        weight_layout.addWidget(self.connection_label)
        
        # Pulsanti di azione rapida
        actions_layout = QHBoxLayout()
        
        self.connect_button = QPushButton("Cerca Bilancia")
        self.connect_button.clicked.connect(self.find_scale)
        self.connect_button.setMinimumHeight(40) # Pulsante più grande
        actions_layout.addWidget(self.connect_button)
        
        weight_layout.addLayout(actions_layout)
        
        main_layout.addWidget(weight_group)
        
        # Impostazioni API
        api_group = QGroupBox("Impostazioni API")
        api_layout = QGridLayout(api_group)
        api_layout.setVerticalSpacing(10) # Spaziatura maggiore
        
        # Etichette con colore distintivo
        host_label = QLabel("Host:")
        host_label.setStyleSheet("color: #CCCCCC; font-weight: bold;")
        api_layout.addWidget(host_label, 0, 0)
        
        api_settings = self.settings_manager.get_api_settings()
        self.api_host_edit = QLineEdit(api_settings["host"])
        self.api_host_edit.setStyleSheet("color: #FFFFFF; background-color: #3F3F46; padding: 5px; border-radius: 3px; border: 1px solid #555555;")
        self.api_host_edit.setPlaceholderText("es. 0.0.0.0 o 192.168.1.100")
        api_layout.addWidget(self.api_host_edit, 0, 1)
        
        port_label = QLabel("Porta:")
        port_label.setStyleSheet("color: #CCCCCC; font-weight: bold;")
        api_layout.addWidget(port_label, 1, 0)
        
        self.api_port_spin = QSpinBox()
        self.api_port_spin.setRange(1024, 65535)
        self.api_port_spin.setValue(api_settings["port"])
        self.api_port_spin.setMinimumHeight(30) # Spinbox più grande
        api_layout.addWidget(self.api_port_spin, 1, 1)
        
        self.api_autostart_check = QCheckBox("Avvia API automaticamente all'avvio")
        self.api_autostart_check.setChecked(api_settings["autostart"])
        api_layout.addWidget(self.api_autostart_check, 2, 0, 1, 2)
        
        api_status_layout = QHBoxLayout()
        self.api_status_label = QLabel("API: Inattiva")
        self.api_status_label.setStyleSheet("color: #FF9A3C;") # Colore arancione per inattivo
        api_status_layout.addWidget(self.api_status_label)
        
        self.api_toggle_button = QPushButton("Avvia API")
        self.api_toggle_button.clicked.connect(self.toggle_api)
        api_status_layout.addWidget(self.api_toggle_button)
        
        api_layout.addLayout(api_status_layout, 3, 0, 1, 2)
        
        # Layout per i pulsanti di impostazioni API
        api_buttons_layout = QHBoxLayout()
        
        self.api_save_button = QPushButton("Salva Impostazioni API")
        self.api_save_button.clicked.connect(self.save_api_settings)
        api_buttons_layout.addWidget(self.api_save_button)
        
        self.api_help_button = QPushButton("📖 Aiuto API")
        self.api_help_button.clicked.connect(self.show_api_help)
        self.api_help_button.setStyleSheet("background-color: #4CAF50;")  # Verde per il pulsante aiuto
        api_buttons_layout.addWidget(self.api_help_button)
        
        self.setup_help_button = QPushButton("🔧 Setup Esterno")
        self.setup_help_button.clicked.connect(self.show_setup_help)
        self.setup_help_button.setStyleSheet("background-color: #FF9A3C;")  # Arancione per setup
        api_buttons_layout.addWidget(self.setup_help_button)
        
        api_layout.addLayout(api_buttons_layout, 4, 0, 1, 2)
        
        main_layout.addWidget(api_group)
        
        # Impostazioni applicazione
        app_group = QGroupBox("Impostazioni Applicazione")
        app_layout = QVBoxLayout(app_group)
        app_layout.setSpacing(10) # Spaziatura maggiore
        
        app_settings = self.settings_manager.get_application_settings()
        
        self.start_minimized_check = QCheckBox("Avvia minimizzato")
        self.start_minimized_check.setChecked(app_settings["start_minimized"])
        app_layout.addWidget(self.start_minimized_check)
        
        self.autostart_windows_check = QCheckBox("Avvia automaticamente all'avvio di Windows")
        self.autostart_windows_check.setChecked(app_settings["autostart_windows"])
        app_layout.addWidget(self.autostart_windows_check)
        
        self.app_save_button = QPushButton("Salva Impostazioni Applicazione")
        self.app_save_button.clicked.connect(self.save_app_settings)
        app_layout.addWidget(self.app_save_button)
        
        main_layout.addWidget(app_group)
        
        # Barra di stato
        self.statusBar().showMessage("Pronto")
        
        # Carica lo stile
        self.set_style()
        
    def set_style(self):
        """Imposta lo stile dell'interfaccia utente con colori più contrastanti"""
        style = """
        QMainWindow {
            background-color: #2d2d30;
            color: #ffffff;
        }
        QWidget {
            background-color: #2d2d30;
            color: #ffffff;
        }
        QLabel {
            color: #ffffff;
            font-weight: normal;
        }
        QGroupBox {
            border: 1px solid #3f3f46;
            border-radius: 5px;
            margin-top: 1.5ex;
            padding-top: 10px;
            font-weight: bold;
            color: #4dc0ff;
            background-color: #333337;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 8px;
            color: #4dc0ff;
            background-color: #333337;
        }
        QPushButton {
            background-color: #0078d7;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 8px 15px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1c86d9;
        }
        QPushButton:pressed {
            background-color: #0063b1;
        }
        QSpinBox {
            background-color: #3f3f46;
            color: white;
            border: 1px solid #555555;
            padding: 4px;
            border-radius: 3px;
        }
        QLineEdit {
            background-color: #3f3f46;
            color: white;
            border: 1px solid #555555;
            padding: 4px;
            border-radius: 3px;
        }
        QCheckBox {
            color: #ffffff;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }
        QCheckBox::indicator:unchecked {
            border: 1px solid #5f5f5f;
            background-color: #3f3f46;
        }
        QCheckBox::indicator:checked {
            border: 1px solid #5f5f5f;
            background-color: #0078d7;
        }
        QStatusBar {
            background-color: #1e1e1e;
            color: #999999;
        }
        """
        self.setStyleSheet(style)
        
    def update_ui(self):
        """Aggiorna l'interfaccia utente"""
        # Aggiorna lo stato dell'API
        if self.api.running:
            self.api_status_label.setText(f"API: Attiva su {self.api.host}:{self.api.port}")
            self.api_status_label.setStyleSheet("color: #6BFF72;") # Verde per attivo
            self.api_toggle_button.setText("Ferma API")
        else:
            self.api_status_label.setText("API: Inattiva")
            self.api_status_label.setStyleSheet("color: #FF9A3C;") # Arancione per inattivo
            self.api_toggle_button.setText("Avvia API")
        
    def update_weight_display(self, weight):
        """Aggiorna il display del peso"""
        self.weight_label.setText(str(weight))
        
    def update_connection_status(self, connected, conn_type):
        """Aggiorna lo stato della connessione"""
        if connected:
            self.connection_label.setText(f"Connesso ({conn_type})")
            self.connection_label.setStyleSheet("color: #6BFF72;") # Verde per connesso
            self.statusBar().showMessage(f"Bilancia connessa via {conn_type}")
        else:
            self.connection_label.setText("Non connesso")
            self.connection_label.setStyleSheet("color: #FF6B6B;") # Rosso per non connesso
            self.statusBar().showMessage("Bilancia non connessa")
        
    def show_error(self, message):
        """Mostra un messaggio di errore"""
        self.statusBar().showMessage(f"Errore: {message}")
        logger.error(message)
        
    def find_scale(self):
        """Cerca la bilancia"""
        self.statusBar().showMessage("Ricerca bilancia in corso...")
        
        if self.scale.find_usb_scale():
            self.update_connection_status(True, "USB")
            return True
        
        self.update_connection_status(False, "")
        QMessageBox.warning(self, "Errore", "Nessuna bilancia trovata.")
        return False
        
    def toggle_api(self):
        """Avvia o ferma l'API"""
        if self.api.running:
            self.api.stop()
            self.statusBar().showMessage("API fermata")
        else:
            # Aggiorna le impostazioni dell'API
            self.api.host = self.api_host_edit.text()
            self.api.port = self.api_port_spin.value()
            self.api.start()
            self.statusBar().showMessage(f"API avviata su {self.api.host}:{self.api.port}")
            
    def save_api_settings(self):
        """Salva le impostazioni dell'API"""
        host = self.api_host_edit.text().strip()
        port = self.api_port_spin.value()
        autostart = self.api_autostart_check.isChecked()
        
        # Validazione dell'host
        if not host:
            QMessageBox.warning(self, "Errore", "Il campo host non può essere vuoto.")
            return
            
        # Validazione IP (semplice)
        if not self.validate_host(host):
            QMessageBox.warning(self, "Errore", 
                "Host non valido. Usa:\n"
                "• 0.0.0.0 (tutte le interfacce)\n"
                "• 127.0.0.1 (solo locale)\n" 
                "• Un IP valido (es. 192.168.1.100)")
            return
        
        if self.settings_manager.update_api_settings(host, port, autostart):
            self.statusBar().showMessage("Impostazioni API salvate")
            
            # Se l'API è in esecuzione, riavviala con le nuove impostazioni
            if self.api.running:
                self.api.stop()
                self.api.host = host
                self.api.port = port
                self.api.start()
        else:
            QMessageBox.warning(self, "Errore", "Impossibile salvare le impostazioni API")
            
    def save_app_settings(self):
        """Salva le impostazioni dell'applicazione"""
        start_minimized = self.start_minimized_check.isChecked()
        autostart_windows = self.autostart_windows_check.isChecked()
        
        if self.settings_manager.update_application_settings(start_minimized, autostart_windows):
            self.statusBar().showMessage("Impostazioni applicazione salvate")
            
            # Gestisce l'avvio automatico di Windows
            if autostart_windows:
                self.autostart_manager.enable_autostart()
            else:
                self.autostart_manager.disable_autostart()
        else:
            QMessageBox.warning(self, "Errore", "Impossibile salvare le impostazioni dell'applicazione")
    
    def validate_host(self, host):
        """Valida l'indirizzo host"""
        import re
        
        # Pattern per IP valido
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        
        # Controlla se è un IP valido
        if re.match(ip_pattern, host):
            # Verifica che ogni ottetto sia tra 0-255
            octets = host.split('.')
            for octet in octets:
                if not (0 <= int(octet) <= 255):
                    return False
            return True
        
        # Accetta anche localhost
        if host in ['localhost', '0.0.0.0', '127.0.0.1']:
            return True
            
        return False
    
    def show_api_help(self):
        """Mostra l'aiuto per l'API"""
        api_settings = self.settings_manager.get_api_settings()
        dialog = APIHelpDialog(api_settings, self)
        dialog.exec()
    
    def show_setup_help(self):
        """Mostra l'aiuto per il setup esterno dell'API"""
        api_settings = self.settings_manager.get_api_settings()
        dialog = SetupHelpDialog(api_settings, self)
        dialog.exec()
        
    def closeEvent(self, event):
        """Gestisce l'evento di chiusura dell'applicazione"""
        # Ferma il thread di lettura
        self.scale_worker.stop()
        self.scale_thread.quit()
        self.scale_thread.wait()
        
        # Disconnette la bilancia
        self.scale.disconnect()
        
        # Ferma l'API
        self.api.stop()
        
        # Accetta l'evento di chiusura
        event.accept()


# Punto di ingresso principale
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())