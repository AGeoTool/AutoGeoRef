#conda install conda-forge::cx_freeze==7.2.8 anaconda::pyqt==5.15.11 anaconda::psutil anaconda::pillow
#pip install numpy==1.26.4 opencv-python==4.10.0.84
#conda install conda-forge::gdal 
import sys
import os
import psutil
import numpy as np
import georef
import Viewer
import threading
#import time
import cv2
import Crop_Image
import shutil
import traceback
from georefObject import georef_object
#from memory_profiler import memory_usage
#import rasterio
#from rasterio.transform import from_origin
#from rasterio.transform import Affine
#from rasterio.shutil import copy as rio_copy
from LSD1 import line_segment_detector, image_loader
from calc_corner import calc_corner
from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QTableWidget,
    QPushButton, 
    QFileDialog,
    QStatusBar,
    QToolBar,
    QAction,
    QCheckBox,
    QLabel,
    QMainWindow,
    QAbstractScrollArea,
    QMessageBox,
    QComboBox,
    QGridLayout,
    QSpinBox,
    QLineEdit,
    QTextEdit)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

from osgeo import gdal, osr
import osgeo
#print(os.path.join(os.path.dirname(osgeo.__file__), "data", "proj"))
os.environ["PROJ_LIB"] = os.path.join(os.path.dirname(sys.executable), "proj")
def save_image_as_tif(
    image_input,
    output_tif: str,
    tfw_param=None,
    crs: str = "EPSG:25832",
    compress: str = None,
    jpeg_quality: int = None
):
    """
    Speichert ein JPEG oder cv2/NumPy-Bild als TIFF oder GeoTIFF.
    
    - JPEG als Input: Wird als TIFF mit JPEG-Kompression übernommen
    - NumPy-Array: Wird als TIFF gespeichert (Kompression wählbar)
    
    Georeferenz und CRS sind optional!

    :param image_input: JPEG-Dateipfad ODER NumPy-Array (OpenCV Bild)
    :param output_tif: Zielpfad
    :param tfw_param: Optional. [A, D, B, E, C, F] wie .tfw
    :param crs: Optional. z.B. "EPSG:25832"
    :param compress: "JPEG", "LZW", "DEFLATE" oder None
    :param jpeg_quality: nur bei compress="JPEG"
    """
    
    #print(type(image_input))
    
    # --- TIFF-Optionen vorbereiten ---
    options = ["TILED=YES"]

    if compress == "JPEG":
        options += [
            "COMPRESS=JPEG",
            f"JPEG_QUALITY={jpeg_quality}",
            "PHOTOMETRIC=YCBCR"
        ]
    elif compress in ("LZW", "DEFLATE"):
        options += [f"COMPRESS={compress}", "PREDICTOR=2"]
    # else: no compression

    # --- 1: Bild-Pfad ---
    if isinstance(image_input, str):
        #print("Pfad")
        src_ds = gdal.Open(image_input, gdal.GA_ReadOnly)
        if src_ds is None:
            raise FileNotFoundError(f"Bild konnte nicht geöffnet werden: {image_input}")

        driver = gdal.GetDriverByName("GTiff")
        if image_input.endswith(".jpg") and compress == None:
            options += [
                "COMPRESS=JPEG",
                "PHOTOMETRIC=YCBCR"
            ]
        dst_ds = driver.CreateCopy(output_tif, src_ds, strict=0, options=options)

    # --- 2: NumPy/OpenCV-Array ---
    elif isinstance(image_input, np.ndarray):
        #print("Array")
        height, width = image_input.shape[:2]
        bands = 1 if image_input.ndim == 2 else image_input.shape[2]

        # Bei Graustufen Photometric anpassen
        if bands == 1 and compress == "JPEG":
            options = [opt for opt in options if not opt.startswith("PHOTOMETRIC")]
            options.append("PHOTOMETRIC=MINISBLACK")

        driver = gdal.GetDriverByName("GTiff")
        dst_ds = driver.Create(
            output_tif, width, height, bands, gdal.GDT_Byte, options=options
        )

        if bands == 1:
            dst_ds.GetRasterBand(1).WriteArray(image_input)
        else:
            for i in range(bands):
                dst_ds.GetRasterBand(i + 1).WriteArray(image_input[:, :, i])
    else:
        raise TypeError("image_input muss ein Dateipfad (str) oder ein NumPy-Array sein.")

    # --- Georeferenz & CRS optional setzen ---
    if tfw_param is not None:
        #print("TFW-Param")
        A, D, B, E, C, F = tfw_param
        geotransform = (C, A, B, F, D, E)
        dst_ds.SetGeoTransform(geotransform)
    
    if crs is not None:
        srs = osr.SpatialReference()
        srs.SetFromUserInput(crs)
        dst_ds.SetProjection(srs.ExportToWkt())

    dst_ds.FlushCache()
    dst_ds = None
    #print(f"✅ TIFF gespeichert: {output_tif}")
    """
    cog = True
    if cog:
        cog_output = output_tif.replace(".tif", "_COG.tif")
        gdal.Translate(
            cog_output,
            output_tif,
            format="COG",
            creationOptions=[
                f"COMPRESS={compress if compress else 'LZW'}",
                f"QUALITY={jpeg_quality}",
                "LEVEL=9",
                "NUM_THREADS=ALL_CPUS"
            ]
        )
        print(f"✅ Cloud Optimized GeoTIFF erstellt: {cog_output}")
    else:
        print(f"✅ TIFF gespeichert: {output_tif}")
    """
    
class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("Icon/reload-map-location-icon.png"))
        #self.log_toolbar()
        #self.log.append("Lade Koordinatendatei")
        self.utm_coords = georef.load_coords()
        
        self.georefObjectList = []
        self.imageLoading = False
        self.imageLoading2 = False
        self.viewer_queue = []
        self.current_viewer = None 
        self.readyViewer = 0
        
        #self.log.append("Erstelle Tabelle")
        # Tabelle auf der linken Seite
        self.table = QTableWidget()
        self.table.setRowCount(0)  # Anfangs keine Zeilen
        self.table.setColumnCount(7)  # Anzahl der Spalten
        self.table.setHorizontalHeaderLabels(
            ["Dateipfad",
             "Datei ist GeoTiff",
             "World Datei vorhanden",
             "Corner Datei vorhanden",
             "Transformationsparameter vorhanden",
             "Daten für Corner-Datei vorhanden",
             "Status"])

        # Zeilenweise Auswahl aktivieren
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        # Erweiterte Auswahl mit Strg und Umschalt erlauben
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        # Alle Editier-Trigger deaktivieren, um die gesamte Tabelle nicht bearbeitbar zu machen
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.table.cellDoubleClicked.connect(self.start_viewer)
        self.setCentralWidget(self.table)
        
        #self.log.append("Erstelle Toolbars")
        self.file_toolbar()
        self.georef_toolbar()
        self.save_toolbar()
        self.setStatusBar(QStatusBar(self))
        
        # Fenstereinstellungen
        self.setWindowTitle("AutoGeoRef")
    
    def log_toolbar(self):
        logToolbar = QToolBar("Log Toolbar")
        self.addToolBar(Qt.BottomToolBarArea, logToolbar)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        logToolbar.addWidget(self.log)
    
    def start_viewer(self):
        selected_rows = {index.row() for index in self.table.selectedIndexes()}
        viewers = 0
        for e in self.georefObjectList:
            row = e.get_current_row()
            if row in selected_rows:
                if e.lock:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText(f"{e.filepath} ist aktuell durch einen anderen Prozess gesperrt und kann deshalb nicht im Viewer angezeigt werden.")
                    msg.setWindowTitle("Gesperrtes Objekt")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    e.lock = True
                    Viewer.Viewer(e, self)
                    viewers += 1
                    e.statusItem.setText("wird geöffnet")
                    self.table.viewport().update()
        if viewers > 0:
            # Starten Sie die gesteuerte Erstellung
            self.show_next_viewer()
        
    def show_next_viewer(self):
        if self.sender() == self.current_viewer:
            print("Das aktuelle Fenster schließen")
            # Das aktuelle Fenster schließen
            self.current_viewer.close()
            
        # Prüfen, ob noch Fenster in der Warteschlange sind
        if self.viewer_queue:
            print("Warte bis Viewer fertig geladen")
            while not self.viewer_queue[0].ready:
                pass
            print("Zeige Viewer")
            self.current_viewer = self.viewer_queue.pop(0)
            self.readyViewer -= 1
            self.current_viewer.showMaximized()
            self.current_viewer.GeoRefObject.statusItem.setText("wird angezeigt")
            self.table.viewport().update()
        else:
            print("Keine weiteren Fenster")
            # Keine weiteren Fenster
            self.current_viewer = None
    
    def georef_task(self,georefObject):
        try:
            #start = time.time()
            filepath = georefObject.filepath
            self.imageLoading = True
            georefObject.statusItem.setText("Lade Bild")
            self.table.viewport().update()
            image, dpi = image_loader(filepath)
            self.imageLoading = False
            georefObject.statusItem.setText("Linienerkennung")
            self.table.viewport().update()
            rect = line_segment_detector(image, dpi)
            del image
            georefObject.statusItem.setText("berechne Schnittpunkte")
            self.table.viewport().update()
            imgPoints = np.array(calc_corner(rect))
            georefObject.statusItem.setText("suche UTM-Koordinaten")
            self.table.viewport().update()
            geoPoints = np.array(georef.search_csv(georefObject.filename,self.utm_coords))
            georefObject.statusItem.setText("berechne Georeferenzierung")
            self.table.viewport().update()
            georefObject.worldParam = list(georef.georef(imgPoints, geoPoints))
            openSides = [1,1,1,1]
            georefObject.txtParam = georef.get_corner_param(imgPoints, geoPoints, openSides)
            georefObject.update_wc_icon()
            georefObject.statusItem.setText("")
            georefObject.lock = False
            self.table.viewport().update()
            #print(f"{filepath}: {time.time()-start:.2f}s")
        except Exception as error:
            print(error)
            georefObject.statusItem.setText(str(error))
    
    def AutoGeoRef(self):
        selected_rows = {index.row() for index in self.table.selectedIndexes()}
        threads = []
        #print("creating")
        for e in self.georefObjectList:
            row = e.get_current_row()
            if row in selected_rows:
                if e.lock:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText(f"{e.filepath} ist aktuell durch einen anderen Prozess gesperrt und kann deshalb nicht bearbeitet werden.")
                    msg.setWindowTitle("Gesperrtes Objekt")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    e.lock = True
                    e.statusItem.setText("Task erstellt")
                    thread = threading.Thread(target=self.georef_task,args=[e])
                    threads.append(thread)
        
        threadStarter = threading.Thread(target=self.thread_starter,args=[threads])
        threadStarter.start()     
    
    def thread_starter(self, threads):
        #print("starting threads")
        #gest = time.time()
        for t in threads:
            #start = time.time()
            #print(self.imageLoading,self.imageLoading2)
            #print("Warte auf geladene Bilder")
            while self.imageLoading or self.imageLoading2:
                #sys.stdout.write(f"\rLadezeit: {time.time()-start:.2f}")
                pass
            #print()
            memory_info = psutil.virtual_memory()
            #start = time.time()
            #print("warte auf Arbeitsspeicher")
            while memory_info.available / (1024 ** 3) < 2:
                memory_info = psutil.virtual_memory()
                #sys.stdout.write(f"\rZeit Limit: {time.time()-start:.2f}\t")
                #sys.stdout.write(f"Arbeitsspeicher Verfügbar: {memory_info.available / (1024 ** 3):.2f} GB\t")
            #print()
            #print(f"Arbeitsspeicher Verfügbar: {memory_info.available / (1024 ** 3):.2f} GB")
            t.start()
        #print(f"Gesamtzeit Threadstarter: {time.time()-gest}")
    
    def load_files(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, "Bilddateien auswählen", "", "Bilddateien (*.jpg *.jpeg *.tif *.tiff *.geotiff);;Alle Dateien (*)", options=options)
        
        # Überprüfen, ob Dateien ausgewählt wurden
        if files:
            self.add_files_to_table(files)
            return

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Ordner auswählen", "", QFileDialog.ShowDirsOnly)
        if folder:
            # Bilddateien aus dem ausgewählten Ordner laden
            image_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.tif', '.tiff', '.geotiff'))]
            self.add_files_to_table(image_files)

    def add_files_to_table(self, files):
        # Aktuelle Zeilenanzahl ermitteln
        current_row_count = self.table.rowCount()
        # Liste aller vorhandenen Dateipfade aus der Tabelle holen (Spalte 0)
        existing_paths = [self.table.item(row, 0).text() for row in range(current_row_count) if self.table.item(row, 0)]
        # Tabelle mit neuen Daten füllen, falls noch nicht vorhanden
        for file in files:
            file = file.replace("\\", "/")
            #print(file)
            if file not in existing_paths:
                self.georefObjectList.append(georef_object(file))
                # Neue Zeile hinzufügen
                self.table.insertRow(current_row_count)
                self.table.setItem(current_row_count, 0, self.georefObjectList[current_row_count].filepathItem)
                self.table.setItem(current_row_count, 1, self.georefObjectList[current_row_count].GTiffFileItem)
                self.table.setItem(current_row_count, 2, self.georefObjectList[current_row_count].worldFileItem)
                self.table.setItem(current_row_count, 4, self.georefObjectList[current_row_count].worldItem)
                self.table.setItem(current_row_count, 3, self.georefObjectList[current_row_count].txtFileItem)
                self.table.setItem(current_row_count, 5, self.georefObjectList[current_row_count].txtItem)
                self.table.setItem(current_row_count, 6, self.georefObjectList[current_row_count].statusItem)
                #self.log.append(f"{self.georefObjectList[current_row_count].filename}: Füge Objekt zu Tabelle hinzu")
                current_row_count += 1  # Zeilenanzahl erhöhen
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Dateipfad vorhanden")
                msg.setText(f"Dateipfad bereits vorhanden: {file}")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()
        self.table.resizeColumnsToContents()
        self.table.viewport().update()
        #self.update_wcPath()
    
    def remove_selected(self):
        # Hole die ausgewählten Zeilen, ohne Duplikate
        selected_rows = {index.row() for index in self.table.selectedIndexes()}
        filtered = []
        objectList = self.georefObjectList.copy()
        for e in objectList:
            remove = 0
            row = e.get_current_row()
            if not (row in selected_rows):
                remove += 1
            if e.lock:
                remove += 1
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText(f"{e.filepath} ist aktuell durch einen anderen Prozess gesperrt und kann deshalb nicht gelöscht werden.")
                msg.setWindowTitle("Gesperrtes Objekt")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            if remove == 0:
                #self.log.append(f"{e.filename}: Entferne Objekt aus Tabelle")
                #print(f"{e.filename}: Entferne Objekt aus Tabelle")
                filtered.append(row)
                self.georefObjectList.remove(e)
        filtered = sorted(filtered,reverse=True)
        for r in filtered:
            self.table.removeRow(r)
        self.table.viewport().update()
        
    def remove_list(self):
        self.table.setRowCount(0)
        self.georefObjectList.clear()
        self.table.viewport().update()

    def file_toolbar(self):
        #menubar = self.menuBar()

        toolbar = QToolBar("Datei")
        toolbar.setIconSize(QSize(64, 64))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        
        buttonAddFile = QAction(
            QIcon("Icon/add-files-icon.png"), "Dateien hinzufügen", self)
        buttonAddFile.setStatusTip("Dateien zur Liste hinzufügen")
        buttonAddFile.triggered.connect(self.load_files)
        
        buttonAddFolder = QAction(
            QIcon("Icon/add-folder-icon.png"), "Ordner hinzufügen", self)
        buttonAddFolder.setStatusTip("Ordner zur Liste hinzufügen")
        buttonAddFolder.triggered.connect(self.load_folder)
        
        buttonRemoveFile = QAction(
            QIcon("Icon/delete-files-icon.png"), "Ausgewählte Dateien entfernen", self)
        buttonRemoveFile.setStatusTip("Ausgewählte Dateien aus Liste entfernen")
        buttonRemoveFile.triggered.connect(self.remove_selected)
        
        # buttonRemoveList = QAction(self.IconRedCross, "Liste leeren", self)
        # buttonRemoveList.setStatusTip("Entfernt alle Dateien aus der Liste")
        # buttonRemoveList.triggered.connect(self.remove_list)
        
        buttonClose = QAction("Schließen", self)
        buttonClose.setStatusTip("Schließt das Programm")
        buttonClose.triggered.connect(self.close)
        
        toolbar.addAction(buttonAddFile)
        toolbar.addAction(buttonAddFolder)
        toolbar.addSeparator()
        toolbar.addAction(buttonRemoveFile)
        
        #toolbar.addAction(buttonRemoveList)
        """
        actionFile = menubar.addMenu("Datei")
        actionFile.addAction(buttonAddFile)
        actionFile.addAction(buttonAddFolder)
        actionFile.addSeparator()
        actionFile.addAction(buttonRemoveFile)
        actionFile.addAction(buttonRemoveList)
        actionFile.addAction(buttonClose)
        """
        
    def georef_toolbar(self):
        QIcon("Icon_freepic/Basic Rounded Flat/1161311_a.png")
        toolbar = QToolBar("Georeferenzierung")
        toolbar.setIconSize(QSize(64, 64))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        
        btAutoGeoref = QAction(
            QIcon("Icon/reload-map-location-outline-icon.png"), "Automatisch georeferenzieren", self)
        btAutoGeoref.setStatusTip("Ausgewählte Dateien automatisch georeferenzieren")
        btAutoGeoref.triggered.connect(self.AutoGeoRef)
        
        btStartViewer = QAction(
            QIcon("Icon/view-show-all-icon.png"),"Dateien ansehen", self)
        btStartViewer.setStatusTip("Ausgewählte Dateien ansehen")
        btStartViewer.triggered.connect(self.start_viewer)
        
        
        
        toolbar.addAction(btAutoGeoref)
        toolbar.addAction(btStartViewer)
        
    def save_toolbar(self):
        toolbar = QToolBar("Speichern")
        self.addToolBar(Qt.RightToolBarArea, toolbar)
        
        """Abzuspeichernde Objekte"""
        widgetObject = QWidget()
        layout = QGridLayout(widgetObject)
        
        laSaveObject = QLabel("Abzuspeichernde Objekte:")
        layout.addWidget(laSaveObject, 0, 0)
        
        self.ChImgFile = QCheckBox("Bilddatei")
        self.ChImgFile.setStatusTip("nicht georeferenzierte Bilder abspeichern")
        layout.addWidget(self.ChImgFile, 1, 0)
        
        self.ChWorld = QCheckBox("World + Corner-Datei")
        self.ChWorld.setStatusTip("World- und Corner-Datei abspeichern")
        layout.addWidget(self.ChWorld, 2, 0)
        
        self.ChGeotiff = QCheckBox("GeoTIFF")
        self.ChGeotiff.setStatusTip("Bilder als GeoTIFF abspeichern")
        layout.addWidget(self.ChGeotiff, 3, 0)
        
        """Einstellungen"""
        widgetSetting = QWidget()
        layout = QGridLayout(widgetSetting)
        
        laSetting = QLabel("Einstellungen:")
        layout.addWidget(laSetting, 0, 0, 1, 3)
        
        self.ChCropped = QCheckBox("zugeschnitten")
        self.ChCropped.setStatusTip("gedrehte und zugeschnittene Bilder abspeichern")
        layout.addWidget(self.ChCropped, 1, 0, 1, 3)
        
        self.cbCompMethod = QComboBox()
        self.cbCompMethod.setStatusTip("Auswahl der Kompressionsmethode")
        self.cbCompMethod.addItems(["keine Kompression","LZW","zip","JPEG"])
        self.cbCompMethod.currentIndexChanged.connect(self.set_strength)
        layout.addWidget(self.cbCompMethod, 2, 0)
        
        laQuality = QLabel("Qualität:")
        layout.addWidget(laQuality, 2, 1)
        
        self.sbComp = QSpinBox()
        self.sbComp.setStatusTip("Auswahl der Kompressionsstärke")
        self.sbComp.setMinimum(0)
        self.sbComp.setMaximum(100)
        layout.addWidget(self.sbComp, 2, 2)
        
        self.laLossless = QLabel("verlustfrei")
        layout.addWidget(self.laLossless, 2, 2)
        self.set_strength()
        
        """Speicherort"""
        widgetFolder = QWidget()
        layout = QGridLayout(widgetFolder)
        
        laFolder = QLabel("Speicherort:")
        layout.addWidget(laFolder, 0, 0, 1, 2)

        self.leSaveLoc = QLineEdit()
        layout.addWidget(self.leSaveLoc, 1, 1)
        
        pbSaveLocation = QPushButton()
        pbSaveLocation.setIcon(QIcon("Icon/computer-folder-open-icon.png"))
        pbSaveLocation.setStatusTip("Speicherort auswählen")
        pbSaveLocation.clicked.connect(self.select_save_folder)
        layout.addWidget(pbSaveLocation, 1, 0)
        
        """Speichern"""
        pbSave = QPushButton("Speichern")
        pbSave.clicked.connect(self.task_file)
        
        toolbar.addWidget(widgetObject)
        toolbar.addSeparator()
        toolbar.addWidget(widgetSetting)
        toolbar.addSeparator()
        toolbar.addWidget(widgetFolder)
        toolbar.addSeparator()
        toolbar.addWidget(pbSave)
    
    def set_strength(self):
        match self.cbCompMethod.currentIndex():
            case 0:
                self.sbComp.hide()
                self.laLossless.show()
            case 1:
                self.sbComp.hide()
                self.laLossless.show()
            case 2:
                self.sbComp.hide()
                self.laLossless.show()
            case 3:
                self.sbComp.show()
                self.laLossless.hide()
        self.sbComp.setValue(self.sbComp.maximum())
    
    def select_save_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Ordner auswählen", "", QFileDialog.ShowDirsOnly)
        if folder:
            self.leSaveLoc.setText(folder)
    
    def task_file(self):
        folder = self.leSaveLoc.text()
        if not os.path.exists(folder):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(f"Der Pfad {folder} existiert nicht.")
            msg.setWindowTitle("Pfad existiert nicht")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        change = self.ChCropped.isChecked() or self.cbCompMethod.currentIndex() > 0
        selection = [self.ChCropped.isChecked(),
                     self.cbCompMethod.currentIndex(), 
                     self.sbComp.value(), 
                     self.ChImgFile.isChecked(), 
                     self.ChWorld.isChecked(), 
                     self.ChGeotiff.isChecked()]
        selected_rows = {index.row() for index in self.table.selectedIndexes()}
        threads = []
        for e in self.georefObjectList:
            row = e.get_current_row()
            if row in selected_rows:
                if e.lock:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText(f"{e.filepath} ist aktuell durch einen anderen Prozess gesperrt und kann deshalb nicht abgespeichert werden.")
                    msg.setWindowTitle("Gesperrtes Objekt")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    e.lock = True
                    if not e.txtParam:
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Question)
                        msg.setText(f"Es sind keine Corner-Daten für {e.filepath} vorhanden. Bei der weiteren Verarbeitung werden alle Schritte, die Corner-Daten benötigen, nicht ausgeführt.")
                        msg.setWindowTitle("Keine Corner-Daten")
                        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                        retval = msg.exec_()
                        if retval == QMessageBox.Ok:
                            if selection[0]:
                                e.lock = False
                                continue
                            if selection[4]:
                                selection[4] = False
                        elif retval == QMessageBox.Cancel:
                            e.lock = False
                            continue
                    elements = [e, folder, change, selection]
                    #print("Erstelle Speicher Thread")
                    e.statusItem.setText("Speicher-Task erstellt")
                    self.table.viewport().update()
                    thread = threading.Thread(target=self.write_file,args=elements)
                    threads.append(thread)
        threadStarter = threading.Thread(target=self.thread_starter,args=[threads])
        threadStarter.start()
        
    def write_file(self,e, folder, change, selection):
        self.imageLoading = True
        image = False
        newFilepath = folder + "/" + e.filename
        worldParam = e.worldParam
        geoPoints = []
        imgPoints =[]
        if e.txtParam:
            for l in e.txtParam[:-1]:
                imgPoints.append((l[0],l[1]))
                geoPoints.append((l[2],l[3]))
        
        if selection[0]:
            e.statusItem.setText("Bild zuschneiden")
            self.table.viewport().update()
            image = cv2.imread(e.filepath)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            filename, ending = os.path.splitext(newFilepath)
            ending = ".tif"
            newFilepath = filename + "_cropped" + ending
            cropImage = Crop_Image.RotCropImage(image)
            image, imgPoints = cropImage.rotcrop(e.txtParam)
            imgPoint = np.array(imgPoints)
            geoPoint = np.array(geoPoints)
            worldParam = list(georef.georef(imgPoint, geoPoint))
        
        comp = None
        qual = None
        match selection[1]:
            case 0:
                comp = None
            case 1:
                comp = "LZW"
                filename, ending = os.path.splitext(newFilepath)
                ending = ".tif"
                newFilepath = filename + "_lzw" + ending
            case 2:
                comp = "DEFLATE"
                filename, ending = os.path.splitext(newFilepath)
                ending = ".tif"
                newFilepath = filename + "_deflate" + ending
            case 3:
                comp = "JPEG"
                qual = selection[2]
                filename, ending = os.path.splitext(newFilepath)
                newFilepath = filename + f"_jpeg_{qual}" + ending
                
        #print(newFilepath)
        try:
            if selection[4]:
                e.statusItem.setText("speichere World/Corner")
                self.table.viewport().update()
                filename, ending = os.path.splitext(newFilepath)
                print(ending, filename + "." + ending[1] + ending[-1] + "w", worldParam)
                georef.write_tfw(filename + "." + ending[1] + ending[-1] + "w", worldParam)
                georef.write_corner(filename + ".txt", imgPoints, geoPoints, e.txtParam[-1])
            
            if selection[3]:
                e.statusItem.setText("speichere Bild")
                if not change:
                    shutil.copy(e.filepath, newFilepath)
                else:
                    if not isinstance(image, np.ndarray):
                        image = cv2.imread(e.filepath)
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    filename, ending = os.path.splitext(newFilepath)
                    if ending == ".geotiff":
                        ending = ".tif"
                    save_image_as_tif(image, filename + ending, None , compress=comp, jpeg_quality=qual)
            
            if selection[5]:
                e.statusItem.setText("erstelle GeoTIFF")
                self.table.viewport().update()
                if not isinstance(image, np.ndarray):
                    image = e.filepath
                filename, ending = os.path.splitext(newFilepath)
                if not ending in ["tif","tiff"]:
                    change = True
                    ending = ".tif"
                newFilepath = filename + "_GTIF" + ending
                save_image_as_tif(image, newFilepath, worldParam, compress=comp, jpeg_quality=qual)
            
            del image
            e.statusItem.setText("")
        except Exception as error:
            print(error)
            e.statusItem.setText(str(error))
            traceback.print_exc()  
        self.table.viewport().update()

        self.imageLoading = False
        e.lock= False

def main():
    app = QApplication(sys.argv)
    window = MyWindow() 
    window.showMaximized()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
