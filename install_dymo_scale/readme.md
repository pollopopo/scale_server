**ITALIANO**

Installazione del Driver della Bilancia DYMO tramite Zadig

Per installare correttamente i driver per la tua bilancia DYMO, segui attentamente questa procedura:

1. Copia della Libreria `libusb-1.0.dll`:
   - Individua la directory di installazione di MinGW sul tuo sistema.
   - Se il tuo sistema è a 64 bit, naviga nella sottocartella `MinGW64` e copia il file `libusb-1.0.dll`.
   - Se il tuo sistema è a 32 bit, naviga nella sottocartella `MinGW32` e copia il file `libusb-1.0.dll`.
   - Incolla il file `libusb-1.0.dll` copiato nella directory di destinazione `/install_dymo_bilance`. Assicurati che questa directory esista o creala se necessario.

2. Esecuzione di Zadig con Privilegi di Amministratore:
   - Individua l'eseguibile di `Zadig` (solitamente `zadig.exe`).
   - Fai clic con il pulsante destro del mouse sull'eseguibile di `Zadig`.
   - Seleziona l'opzione "Esegui come amministratore" dal menu contestuale. È fondamentale eseguire Zadig con questi privilegi per permettere la modifica e l'installazione dei driver di sistema.

3. Configurazione e Installazione del Driver tramite Zadig:
   - Una volta avviato Zadig, clicca sul menu "Options".
   - Seleziona l'opzione "List All Devices" per visualizzare tutti i dispositivi collegati al computer.
   - Dall'elenco a discesa dei dispositivi, seleziona la tua bilancia DYMO.
   - Nel selettore del driver (a destra del nome del dispositivo), seleziona `libusb-win32`.
   - Dopo aver verificato che il dispositivo corretto e il driver `libusb-win32` siano selezionati, clicca sul pulsante "Install Driver" (o "Replace Driver").
   - Attendi il completamento del processo di installazione.

Una volta completati questi passaggi, il driver `libusb-win32` dovrebbe essere installato per la tua bilancia DYMO. Potrebbe essere necessario scollegare e ricollegare la bilancia o riavviare il computer.

---

**ENGLISH**

DYMO Scale Driver Installation via Zadig

To correctly install the drivers for your DYMO scale, please follow this procedure carefully:

1. Copying the `libusb-1.0.dll` Library:
   - Locate the MinGW installation directory on your system.
   - If your system is 64-bit, navigate to the `MinGW64` subfolder and copy the `libusb-1.0.dll` file.
   - If your system is 32-bit, navigate to the `MinGW32` subfolder and copy the `libusb-1.0.dll` file.
   - Paste the copied `libusb-1.0.dll` file into the destination directory `/install_dymo_bilance`. Ensure this directory exists or create it if necessary.

2. Running Zadig with Administrator Privileges:
   - Locate the `Zadig` executable (usually `zadig.exe`).
   - Right-click on the `Zadig` executable.
   - Select the "Run as administrator" option from the context menu. It is crucial to run Zadig with these privileges to allow modification and installation of system drivers.

3. Driver Configuration and Installation via Zadig:
   - Once Zadig is started, click on the "Options" menu.
   - Select the "List All Devices" option to display all devices connected to the computer.
   - From the device drop-down list, select your DYMO scale.
   - In the driver selector (to the right of the device name), select `libusb-win32`.
   - After verifying that the correct device and the `libusb-win32` driver are selected, click the "Install Driver" (or "Replace Driver") button.
   - Wait for the installation process to complete.

Once these steps are completed, the `libusb-win32` driver should be installed for your DYMO scale. You may need to disconnect and reconnect the scale or restart your computer.

---

**FRANÇAIS**

Installation du Pilote de la Balance DYMO via Zadig

Pour installer correctement les pilotes de votre balance DYMO, veuillez suivre attentivement cette procédure :

1. Copie de la Bibliothèque `libusb-1.0.dll` :
   - Localisez le répertoire d'installation de MinGW sur votre système.
   - Si votre système est en 64 bits, naviguez dans le sous-dossier `MinGW64` et copiez le fichier `libusb-1.0.dll`.
   - Si votre système est en 32 bits, naviguez dans le sous-dossier `MinGW32` et copiez le fichier `libusb-1.0.dll`.
   - Collez le fichier `libusb-1.0.dll` copié dans le répertoire de destination `/install_dymo_bilance`. Assurez-vous que ce répertoire existe ou créez-le si nécessaire.

2. Exécution de Zadig avec les Privilèges d'Administrateur :
   - Localisez l'exécutable de `Zadig` (généralement `zadig.exe`).
   - Faites un clic droit sur l'exécutable de `Zadig`.
   - Sélectionnez l'option "Exécuter en tant qu'administrateur" dans le menu contextuel. Il est crucial d'exécuter Zadig avec ces privilèges pour permettre la modification et l'installation des pilotes système.

3. Configuration et Installation du Pilote via Zadig :
   - Une fois Zadig démarré, cliquez sur le menu "Options".
   - Sélectionnez l'option "List All Devices" pour afficher tous les périphériques connectés à l'ordinateur.
   - Dans la liste déroulante des périphériques, sélectionnez votre balance DYMO.
   - Dans le sélecteur de pilote (à droite du nom du périphérique), sélectionnez `libusb-win32`.
   - Après avoir vérifié que le bon périphérique et le pilote `libusb-win32` sont sélectionnés, cliquez sur le bouton "Install Driver" (ou "Replace Driver").
   - Attendez la fin du processus d'installation.

Une fois ces étapes terminées, le pilote `libusb-win32` devrait être installé pour votre balance DYMO. Il se peut que vous deviez déconnecter et reconnecter la balance ou redémarrer votre ordinateur.

---

**DEUTSCH**

Installation des DYMO Waagentreibers über Zadig

Um die Treiber für Ihre DYMO Waage korrekt zu installieren, befolgen Sie bitte diese Schritte sorgfältig:

1. Kopieren der `libusb-1.0.dll` Bibliothek:
   - Finden Sie das MinGW-Installationsverzeichnis auf Ihrem System.
   - Wenn Ihr System 64-Bit ist, navigieren Sie zum Unterordner `MinGW64` und kopieren Sie die Datei `libusb-1.0.dll`.
   - Wenn Ihr System 32-Bit ist, navigieren Sie zum Unterordner `MinGW32` und kopieren Sie die Datei `libusb-1.0.dll`.
   - Fügen Sie die kopierte Datei `libusb-1.0.dll` in das Zielverzeichnis `/install_dymo_bilance` ein. Stellen Sie sicher, dass dieses Verzeichnis existiert oder erstellen Sie es bei Bedarf.

2. Ausführen von Zadig mit Administratorrechten:
   - Finden Sie die ausführbare Datei von `Zadig` (normalerweise `zadig.exe`).
   - Klicken Sie mit der rechten Maustaste auf die ausführbare Datei von `Zadig`.
   - Wählen Sie die Option "Als Administrator ausführen" aus dem Kontextmenü. Es ist entscheidend, Zadig mit diesen Rechten auszuführen, um die Änderung und Installation von Systemtreibern zu ermöglichen.

3. Treiberkonfiguration und -installation über Zadig:
   - Sobald Zadig gestartet ist, klicken Sie auf das Menü "Options".
   - Wählen Sie die Option "List All Devices", um alle mit dem Computer verbundenen Geräte anzuzeigen.
   - Wählen Sie aus der Dropdown-Liste der Geräte Ihre DYMO Waage aus.
   - Wählen Sie im Treiberauswahlfeld (rechts neben dem Gerätenamen) `libusb-win32` aus.
   - Nachdem Sie überprüft haben, dass das korrekte Gerät und der `libusb-win32`-Treiber ausgewählt sind, klicken Sie auf die Schaltfläche "Install Driver" (oder "Replace Driver").
   - Warten Sie, bis der Installationsvorgang abgeschlossen ist.

Nach Abschluss dieser Schritte sollte der `libusb-win32`-Treiber für Ihre DYMO Waage installiert sein. Möglicherweise müssen Sie die Waage trennen und wieder anschließen oder Ihren Computer neu starten.