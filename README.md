![image](https://github.com/user-attachments/assets/043bccce-76cb-4cc0-9d60-7dd3b8865d2e)

# Scale Server - Applicazione Semplificata per Bilancia Dymo

Benvenuto in Scale Manager Lite! Questa è un'applicazione leggera progettata per testare e gestire bilance Dymo M5/M10 collegate via USB. Fornisce un'interfaccia utente semplice e un'API RESTful per accedere ai dati del peso da altre applicazioni.

## Caratteristiche Principali

* **Test di Connessione e Lettura del Peso**: Verifica rapidamente la connessione alla tua bilancia Dymo e leggi il peso.
* **API RESTful**: Accedi al peso e allo stato della bilancia tramite una semplice API HTTP.
    * `GET /api/weight`: Restituisce il peso corrente, l'unità (grammi), il timestamp e lo stato della connessione.
    * `GET /api/status`: Fornisce informazioni sullo stato della connessione della bilancia, il tipo di dispositivo, il nome e lo stato di esecuzione dell'API.
    * `GET /`: Fornisce una pagina di documentazione HTML di base per l'API.
* **Avvio Automatico con Windows**: Configura l'applicazione per avviarsi automaticamente all'avvio di Windows.
* **Configurazione Server API**: Personalizza host e porta per il server API.
* **Interfaccia Utente Intuitiva**: Gestisci le impostazioni e visualizza il peso con facilità.
* **Rilevamento Automatico della Bilancia**: L'applicazione tenta di rilevare automaticamente la bilancia a intervalli regolari.
* **Gestione Errori e Riconnessione**: Tentativi di riconnessione automatici in caso di disconnessione della bilancia.
* **Logging**: Registra gli eventi dell'applicazione e gli errori in un file `scale_manager_lite.log` per facilitare la risoluzione dei problemi.

## Librerie Incluse e Licenze

Questa applicazione utilizza diverse librerie di terze parti:

* **PyQt6**: Utilizzata per l'interfaccia grafica.
    * Licenza: GNU General Public License v3.0
    * Copyright (c) 2023 Riverbank Computing Limited
* **Flask**: Utilizzata per creare l'API RESTful.
    * Licenza: BSD a 3 clausole
    * Copyright (c) 2010 Pallets
* **pyusb**: Utilizzata per la comunicazione USB con la bilancia.
    * Licenza: BSD a 3 clausole
    * Copyright (c) 2009-2023 Wander Lairson Costa e collaboratori
* **libusb**: Backend per pyusb, necessario per la comunicazione USB.
    * Licenza: GNU Lesser General Public License v2.1
    * Copyright (c) 2001-2023 libusb team
* **Zadig**: Applicazione (menzionata per la gestione dei driver USB su Windows, sebbene non direttamente inclusa nel codice Python, la sua licenza influenza quella del progetto).
    * Licenza: GNU General Public License v3.0
    * Copyright (c) 2010-2023 Pete Batard e collaboratori

A causa dell'inclusione di componenti con licenza GPL (PyQt6 e Zadig), **l'intera applicazione "Scale Server" (Scale Manager Lite) è distribuita sotto licenza GNU General Public License v3.0 (GPL-3.0)**.

## Requisiti

* Python 3.x
* Bilancia Dymo M5 o M10
* Windows (per la funzionalità di avvio automatico e la gestione dei driver con Zadig, se necessario)
* La libreria `libusb-1.0.dll` deve essere presente nella stessa cartella dello script `scale_server.py`. [cite: 13] Lo script è configurato per cercare la DLL in questa posizione specifica. [cite: 13, 14]

## Installazione e Configurazione

1.  **Clona il Repository**:
    ```bash
    git clone https://github.com/tuo-username/scale-manager-lite.git
    cd scale-manager-lite
    ```

2.  **Installa le Dipendenze Python**:
    ```bash
    pip install PyQt6 Flask pyusb
    ```

3.  **Libreria `libusb`**:
    * Scarica la DLL `libusb-1.0.dll` dal sito ufficiale di [libusb](https://libusb.info/).
    * Assicurati che la versione della DLL sia compatibile con la tua architettura Python (32-bit o 64-bit).
    * Copia il file `libusb-1.0.dll` nella directory principale dell'applicazione (la stessa di `scale_server.py`).

4.  **Driver USB (Windows)**:
    * Potrebbe essere necessario utilizzare [Zadig](https://zadig.akeo.ie/) per installare il driver corretto (libusb-win32 o libusbK) per la bilancia Dymo (Vendor ID: `0x0922`, Product ID: `0x8003`) affinché `pyusb` possa accedervi. Consultare la documentazione di Zadig e pyusb per maggiori dettagli.

5.  **File di Impostazioni**:
    * Al primo avvio, l'applicazione creerà un file `scale_manager_settings.json` con le impostazioni predefinite.
    * È possibile modificare questo file per configurare l'host e la porta dell'API, e le opzioni di avvio.

## Utilizzo

Esegui l'applicazione con:
```bash
python scale_server.py
```

### Interfaccia Grafica (GUI)

L'interfaccia utente permette di:

* **Visualizzare il Peso Attuale**: Il peso letto dalla bilancia viene mostrato in grammi.
* **Stato Connessione**: Indica se la bilancia è connessa e il tipo di connessione.
* **Cercare Bilancia**: Un pulsante per avviare manualmente la ricerca della bilancia.
* **Impostazioni API**:
    * Configurare l'**Host** e la **Porta** per il server API. 
    * Abilitare/disabilitare l'**avvio automatico dell'API** all'avvio dell'applicazione.
    * **Avviare/Fermare** manualmente il server API. Lo stato dell'API (attiva/inattiva e indirizzo) viene visualizzato.
    * Salvare le impostazioni API.
    * Accedere a una finestra di **Aiuto API** che mostra gli endpoint e come usarli.
    * Accedere a una finestra di **Setup Esterno** con istruzioni dettagliate per configurare l'accesso all'API da altri dispositivi sulla rete, inclusa la configurazione del firewall.
* **Impostazioni Applicazione**:
    * Abilitare/disabilitare l'**avvio minimizzato** dell'applicazione. 
    * Abilitare/disabilitare l'**avvio automatico all'avvio di Windows**. 
    * Salvare le impostazioni dell'applicazione.
* **Barra di Stato**: Mostra messaggi informativi ed errori.

### API RESTful

Se il server API è attivo, è possibile accedere ai seguenti endpoint:

* **`GET /api/weight`** 
    Restituisce l'ultimo peso letto dalla bilancia.
    Esempio di risposta:
    ```json
    {
      "weight": 245,
      "unit": "g",
      "timestamp": "2025-05-21T21:45:30.123456",
      "connected": true
    }
    ```
   

* **`GET /api/status`** 
    Restituisce lo stato attuale della bilancia e del server API.
    Esempio di risposta:
    ```json
    {
      "connected": true,
      "device_type": "USB",
      "device_name": "Dymo M5/M10",
      "api_running": true
    }
    ```
    

* **`GET /`**
    Mostra una semplice pagina HTML con la documentazione degli endpoint API, direttamente nel browser.

### Avvio Automatico con Windows

L'applicazione può essere configurata per avviarsi automaticamente all'avvio di Windows tramite l'opzione "Avvia automaticamente all'avvio di Windows" nelle Impostazioni Applicazione. Questa funzionalità modifica il registro di Windows.

## Risoluzione dei Problemi

* **"DLL non trovata"**: Assicurarsi che `libusb-1.0.dll` sia nella stessa cartella di `scale_server.py`.
* **"Bilancia Dymo non trovata"**:
    * Verificare che la bilancia sia correttamente collegata via USB.
    * Assicurarsi che i driver USB corretti siano installati (potrebbe essere necessario Zadig su Windows).
    * Provare a premere il pulsante "Cerca Bilancia" nell'applicazione. 
* **Errori API**: Controllare che l'host e la porta siano configurati correttamente e che non ci siano conflitti con altre applicazioni che utilizzano la stessa porta. Verificare le impostazioni del firewall se si tenta di accedere all'API da un altro dispositivo. La finestra "Setup Esterno" fornisce una guida dettagliata.
* **Log**: Controllare il file `scale_manager_lite.log` per messaggi di errore dettagliati.

## Licenza

Questo programma è software libero: è possibile ridistribuirlo e/o modificarlo secondo i termini della **GNU General Public License v3.0** come pubblicata dalla Free Software Foundation.

Questo programma è distribuito nella speranza che sia utile, ma SENZA ALCUNA GARANZIA; senza nemmeno la garanzia implicita di COMMERCIABILITÀ o IDONEITÀ PER UNO SCOPO PARTICOLARE. Vedere la GNU General Public License per ulteriori dettagli.

Una copia della GNU General Public License dovrebbe essere inclusa con questo programma (LICENSE.txt). In caso contrario, visitare [https://www.gnu.org/licenses/](https://www.gnu.org/licenses/). 

Quando si ridistribuisce questo software, è necessario includere una copia completa del documento di licenza.

---

Speriamo che Scale Server ti sia utile!



