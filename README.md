# AutoGeoRef V1.0.3
## Zweck der Software:
AutoGeoRef wurde entwickelt, um die Georeferenzierung von Flurkarten zu vereinfachen und zu beschleunigen. Zudem wird die Weiterverarbeitung der Daten vereinfacht.
## Funktionsüberblick
AutoGeoRef bietet folgende Funktionen:
- Automatische Georeferenzierung über Sektionspunkte
- Zuschneiden auf die Randlinie der Karte (auch für bereits georeferenzierte Karten)
- Export und Umwandlung der Daten in World-Datei oder GeoTIFF und Komprimierung der Bilddateien
- Verarbeitung von großen Datenmengen durch Batch-Verarbeitung
portable .exe-Datei wodurch keine Installation nötig ist.
## Installationsanleitung
Folgende Systemanforderungen werden empfohlen:
- CPU: mindestens vier logische Prozessoren
- RAM: mindestens 16GB
- Ausführen auf lokalem PC (nicht in einer virtuellen Umgebung, damit Arbeitsspeicherauslastung richtig ausgelesen wird)

Das Programm ist eine portable .exe-Datei und benötigt somit keine Installation.

## Handbuch
### Aufbau
Die Benutzeroberfläche von AutoGeoRef setzt sich aus zwei Bausteinen zusammen:
1. Übersichtsseite: Die Übersichtsseite dient zur Verwaltung von geladenen Dateien. Hier können Dateien hinzugefügt oder entfernt, die automatische Georeferenzierung gestartet oder Daten abgespeichert werden.
2. Viewer: Der Viewer dient zur Betrachtung und schnellen Qualitätssicherung der Digitalisate.
### Funktion der Schaltflächen in der Übersichtsseite
#### Dateitoolbar
<img width="128" height="128" alt="add-files-icon" src="https://github.com/user-attachments/assets/3b48e86a-62c2-4f57-90c5-ec3ff49e88c6" /> <img width="128" height="128" alt="add-folder-icon" src="https://github.com/user-attachments/assets/bf3c2a01-9fbd-4c34-9714-203df4e59b4c" />

Über diese beiden Schaltflächen kann ein Explorer-Fenster geöffnet werden. Bei der Auswahl von „Dateien laden“ können Bilddateien in diesem Fenster ausgewählt und in die Tabelle geladen werden. Bei der Auswahl über „Ordner öffnen“, werden alle Bilddateien (.png, .jpg, .jpeg, .bmp, .gif, .tif, .tiff, .geotiff), die sich im ausgewählten Ordner befinden, in die Tabelle übernommen.

<img width="128" height="128" alt="delete-files-icon" src="https://github.com/user-attachments/assets/d39d8d7e-09dc-4502-87d2-258d98775bc9" />

Mit der dritten Schaltfläche in dieser Toolbar können ausgewählte Dateien aus der Tabelle wieder entfernt werden.

#### Tabelle
In der Mitte des Fensters befindet sich die Übersichtstabelle, in welcher alle, über die oben beschriebenen Schaltflächen geöffneten Dateien aufgelistet sind. Beim Laden der Datei in die Tabelle wird geprüft, ob Georeferenzierungsparameter in Form einer GeoTIFF oder World-Datei vorhanden sind. Eine Erfolgreiche Prüfung wird durch einen grünen Haken in der jeweiligen Spalte dargestellt.
Die Auswahl in der Tabelle erfolgt über klicken oder ziehen mit der linken Maustaste. Durch gleichzeitiges Drücken der Umschalt-Taste kann der Bereich zwischen dem letzten ausgewählten Element und dem angeklickten Element ausgewählt werden. Durch Drücken der Strg-Taste können einzelne Dateien durch Linksklicks zur Auswahl hinzugefügt werden. Durch einen Doppelklick wird das Viewerfenster für das ausgewählte Element geöffnet.

#### Georeferenzierungstoolbar
<img width="128" height="128" alt="reload-map-location-outline-icon" src="https://github.com/user-attachments/assets/4decee58-285a-4008-aba7-faa100f78029" />

Mit dieser Schaltfläche wird die automatische Georeferenzierung für die ausgewählten Bilder gestartet. In der Statusspalte wird der aktuelle Arbeitsschritt angezeigt. 

<img width="128" height="128" alt="view-show-all-icon" src="https://github.com/user-attachments/assets/79fe8a94-d1c1-45ae-8f58-d4ee77e8f0fa" />

Mit der Schaltfläche "Dateien ansehen" kann der Viewer für alle ausgewählten Bilder geöffnet werden. Der nächste Bild wird im Viewer wird erst nach dem Schließen des vorherigen Viewers angezeigt.

#### Speichern-Toolbar
Im ersten Abschnitt der Speichern-Toolbar kann ausgewählt werden, welche Dateien abgespeichert werden. Zur Auswahl stehen die Bilddatei, die dazugehörige World- und Corner-Datei oder die GeoTIFF.

Im zweiten Abschnitt können die Bearbeitungen für die abgespeicherten Objekte konfiguriert werden. Durch Setzen des Hakens bei „zugeschnitten“ werden Bilddateien auf die Eckpunkte zugeschnitten und in die Waagerechte gedreht. In der Auswahlliste kann zwischen „keine“, „LZW“, „zip“ und „JPEG“ Komprimierung ausgewählt werden. Bei JPEG-Komprimierung steht ein Feld zur Eingabe der Qualität zur Verfügung.

Im nächsten Abschnitt kann durch einen Klick auf die Ordner Schaltfläche ein Exportpfad ausgewählt werden, der auch in der Zeile daneben angezeigt und angepasst werden kann.

Am Ende der Toolbar steht der Knopf „Speichern“. Durch diesen werden die in der Tabelle ausgewählten Dateien abgespeichert. Der Fortschritt wird in der Statusspalte der Tabelle angezeigt.

### Funktionen der Schaltflächen im Viewer
#### Koordinatenliste
Im unteren Bereich befindet sich eine Tabelle mit vier Zeilen, in welcher die Koordinaten für die Bildkoordinaten und die Geokoordinaten in der Reihenfolge UL, OL, OR, UR dargestellt sind. Durch einen einfachen Klick kann die Zeile ausgewählt werden und durch den Bildbereich angepasst werden. Durch einen Doppelklick wird die Zelle geöffnet und es können händisch Zahlenwerte für die Koordinaten eingegeben werden.
#### Bildbereich
Das zentrale Element des Viewers ist der Bildbereich. Mit der rechten Maustaste kann der angezeigte Bereich verschoben werden. Durch Scrollen wird der Bildbereich nach oben und unten verschoben, durch zusätzliches Drücken der Umschalt-Taste kann nach rechts und links verschoben werden. Der Zoom wird durch Strg + Scrollen verändert.

An den Punktkoordinaten, welche in der Tabelle stehen wird ein hellgrüner Punkt angezeigt. Bei einem Wechsel der Tabellenzeile wird die Ansicht auf den ausgewählten Punkt zentriert.

Durch einen Klick mit der linken Maustaste wird die angeklickte Position im Bild in die Tabelle übertragen. 
#### Anzeige der Punkte und automatische Zentrierung
<img width="128" height="128" alt="location-pin-icon" src="https://github.com/user-attachments/assets/f7f92857-73b2-45c7-94d3-cf6cbc6f41cd" />

Durch Deaktivierung dieses Knopfes in der oberen Toolbar wird die Anzeige der grünen Punkte im Bildbetrachter deaktiviert. Nach dem Start eines Viewers ist diese Schaltfläche aktiviert.

<img width="128" height="128" alt="find-location-icon" src="https://github.com/user-attachments/assets/581b67c8-0020-47b1-859b-abf5d11f81a3" />

Dieser Knopf schaltet die automatische Zentrierung ein oder aus.

#### Liste zum Setzen der Geokoordinaten
In der oberen Werkzeugleiste findet sich eine Liste mit allen Baden-Württembergischen Flurkarten. Durch Klick auf den Haken neben dem Auswahlfeld werden die Geokoordinaten für alle Punkte in die Tabelle übernommen.

#### Öffnen eines externen Bildes zur georeferenzierung einer Vergrößerung
<img width="128" height="128" alt="img-file-icon" src="https://github.com/user-attachments/assets/40b83e2b-579f-4db0-8709-58643f111192" />

Durch das Aktivieren dieser Schaltfläche kann ein Bild geladen werden, welches dann im Viewer angezeigt wird. Für das ausgewählte Bild müssen Georeferenzierungsparameter entweder am Dateispeicherort oder im Projekt vorhanden sein. Durch einen Klick in das externe Bild werden die UTM-Koordinaten der ausgewählten Zeile verändert. Durch einen weiteren Klick auf die Schaltfläche wird das externe Bild wieder geschlossen und das ursprüngliche Bild angezeigt.

Diese Funktion ist zur Georeferenzierung von Kartenvergrößerungen gedacht. Auch können somit Punkte abweichend von den Eckpunkten zur Georeferenzierung verwendet werden.

#### Anzeigen des gedrehten und zugeschnittenen Bildes
<img width="128" height="128" alt="object-select-icon" src="https://github.com/user-attachments/assets/9b2de5e1-f7b9-4433-b9af-f49bf7726a42" />

Durch Aktivierung dieser Schaltfläche wird das Bild zugeschnitten und gedreht angezeigt. Mit den weiteren vier Schaltflächen daneben, kann der Zuschnitt an der rot markierten Kante aktiviert oder deaktiviert werden. Beim Schließen des Viewers wird der zuletzt eingestellte Zuschnitt abgespeichert.
#### Nächsten Punkt anzeigen
<img width="128" height="128" alt="select-box-arrow-right-icon" src="https://github.com/user-attachments/assets/5be17e7e-524f-4ae2-bb30-a01743f520e7" />

Über diesen Knopf wird die nächste Tabellenzeile ausgewählt. Wenn die letzte Zeile bereits ausgewählt ist, wird das aktuelle Viewerfenster geschlossen und der nächste Viewer angezeigt.
## Weitere technische Details
### Corner Datei
Zusätzlich zur World-Datei wird eine weitere txt-Datei abgelegt, die Corner-Datei genannt wird. In dieser sind die Bildkoordinaten und UTM-Koordinaten der vier Georeferenzierungspunkte aufgelistet (Reihenfolge: UL, OL, OR, UR). Zudem werden die offenen Seiten für den Zuschnitt abgespeichert (Reihenfolge: L, O, R, U). Somit wird die spätere Verarbeitung vereinfacht und beschleunigt.
### Unterstützte Dateinamen
Die Erkennung des Flurkartenblatts erfolgt über den Dateinamen des Bildes. Die Erkennung ist nur erfolgreich, wenn der Dateiname in der Form QQSSSRR (2 Stellen Quadrant, 3 Stellen Schicht, 2 Stellen Reihe) vorliegt. Die Erkennung von badischen Flurkartenblättern ist aktuell nicht möglich.
### Ladezeit beim Öffnen des Viewers
Beim Öffnen von mehreren Viewerfenstern kann es, abhängig von der Anzahl der ausgewählten Dateien, zu erheblichen Ladezeiten kommen. Dies liegt daran, dass vor der Anzeige des ersten Viewerfensters alle weiteren Viewer erstellt und das erste Bild geladen wird.
