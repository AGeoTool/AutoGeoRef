import cv2
import Crop_Image
import georef
import numpy as np
#import sys
import threading
import psutil
#import time
from georefObject import georef_object
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QToolBar,
    QAction,
    QComboBox,
    QGraphicsEllipseItem,
    QStatusBar,
    QFileDialog,
    QMessageBox
)
from PyQt5.QtGui import (
    QPixmap,
    QIcon,
    QWheelEvent,
    QMouseEvent,
    QBrush,
    QPen,
    QImage)
from PyQt5.QtCore import Qt, QSize

class DrawImage(QGraphicsView):
    def __init__(self, main_window):
        super(DrawImage, self).__init__()
        self.main_window = main_window  # Referenz zum MainWindow
        self.geoRefObject = self.main_window.GeoRefObject
        self.local_image = self.geoRefObject.filepath
        self.local_scene = QGraphicsScene(self)

        # Add the image to the scene
        self.pixMapItem = QGraphicsPixmapItem()
        self.local_scene.addItem(self.pixMapItem)
        self.setScene(self.local_scene)

        self.setTransformationAnchor(
            QGraphicsView.AnchorUnderMouse)  # Zoom on mouse position
        self.zoom_factor = 1.1  # Factor for zooming in/out

        # Disable dragging by default
        self.is_drag_mode = False
        self.is_right_dragging = False  # Flag to indicate right-drag mode

        # Store last position for dragging
        self.last_mouse_position = None
        self.cornerPoints = []
        
    def loadCV2Image(self, cv_img):
        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)  # BGR zu RGB konvertieren
        
        # Konvertiere cv_img (numpy.ndarray) zu QImage
        height, width, channels = cv_img.shape
        bytes_per_line = channels * width
        q_image = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        # Konvertiere QImage zu QPixmap
        q_pixmap = QPixmap.fromImage(q_image)
        
        # Setze das QPixmap in den QGraphicsPixmapItem
        self.pixMapItem.setPixmap(q_pixmap)
        
        self.local_scene.setSceneRect(0, 0, width, height)

    def enterEvent(self, event):
        """Change the cursor to crosshair when entering the widget."""
        self.setCursor(Qt.CrossCursor)  # Set the cursor to crosshair
        super(DrawImage, self).enterEvent(event)  # Call base class method

    def leaveEvent(self, event):
        """Reset the cursor when leaving the widget."""
        self.setCursor(Qt.ArrowCursor)  # Reset the cursor to default
        super(DrawImage, self).leaveEvent(event)  # Call base class method

    def draw_point(self):
        """Draw a point (circle) at the given position."""
        if self.main_window.showPointAction.isChecked():
            self.remove_point()
            for row in range(self.main_window.table.rowCount()):
                x = float(self.main_window.table.item(row, 0).text())
                y = float(self.main_window.table.item(row, 1).text())
                point_size = 10  # Size of the point
                transform = self.transform()  # Gibt die aktuelle Transformationsmatrix zurück
                scale = transform.m11()  # Skalierungsfaktor in X-Richtung
                point_size = 10*(1/scale)
                ellipse = QGraphicsEllipseItem(x - point_size / 2,
                                               y - point_size / 2,
                                               point_size, point_size)
                # Style the point with brush and pen
                ellipse.setBrush(QBrush(Qt.green))  # Red color for the point
                ellipse.setPen(QPen(Qt.green))  # Black border for the point
                self.cornerPoints.append(ellipse)
                self.local_scene.addItem(ellipse)  # Add point to the scene

    def remove_point(self):
        """Remove Points."""
        for point in self.cornerPoints:
            if point.scene() == self.local_scene:  # Nur entfernen, wenn die Szene übereinstimmt
                self.local_scene.removeItem(point)
        self.cornerPoints = []

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press event for drag or pixel selection."""
        if event.button() == Qt.RightButton:  # Right mouse button for drag
            self.is_right_dragging = True
            self.setCursor(Qt.OpenHandCursor)  # Show hand cursor
            self.last_mouse_position = event.pos()  # Record mouse position
        elif event.button() == Qt.LeftButton:  # Left mouse button for pixel selection
            self.setDragMode(QGraphicsView.NoDrag)
            self.is_right_dragging = False
            self.pixelSelect(event)
        super(DrawImage, self).mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move event for dragging."""
        if self.is_right_dragging:
            # Calculate how much the mouse moved
            delta = event.pos() - self.last_mouse_position
            self.last_mouse_position = event.pos()

            # Adjust the scrollbars manually to simulate dragging
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        else:
            super(DrawImage, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Stop dragging when releasing the right mouse button."""
        if event.button() == Qt.RightButton:
            self.is_right_dragging = False
        self.setCursor(Qt.CrossCursor)
        super(DrawImage, self).mouseReleaseEvent(event)
        self.main_window.table.setFocus()

    def wheelEvent(self, event: QWheelEvent):
        """Handle zooming in and out with Ctrl + Mouse Wheel"""
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.scale(self.zoom_factor, self.zoom_factor)  # Zoom in
            else:
                self.scale(1 / self.zoom_factor, 1 /
                           self.zoom_factor)  # Zoom out
            self.draw_point()
        elif event.modifiers() == Qt.ShiftModifier:
            if event.angleDelta().y() > 0:
                delta = 100
            else:
                delta = -100
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta)
        else:
            super(DrawImage, self).wheelEvent(event)  # Default scroll behavior

    def pixelSelect(self, event):
        """Handle pixel selection with the left mouse button."""
        if event.button() == Qt.LeftButton:
            # Map the position in the view to the scene coordinates
            scene_position = self.mapToScene(event.pos())
            image_position = self.pixMapItem.mapFromScene(scene_position)
            
            #selected_rows = {index.row() for index in self.main_window.table.selectedIndexes()}
            # Output the correct position considering zoom and transformations
            #print(f"Clicked position on image: {image_position}, row: {self.main_window.row}")
            if self.main_window.showImage.isChecked():
                self.main_window.calc_UTM_xy(image_position.x(), image_position.y())
            else:
                self.main_window.table.item(self.main_window.row,0).setText(str(image_position.x()))
                self.main_window.table.item(self.main_window.row,1).setText(str(image_position.y()))
                self.main_window.show_point()
                self.main_window.table.resizeColumnsToContents()
            #else:
                #print("Click outside the image")

class Viewer(QMainWindow):
    def __init__(self, GeoRefObject, mainWindow):
        super(Viewer, self).__init__()
        self.setWindowIcon(QIcon("Icon/search-map-location-icon.png"))
        #s = time.time()
        self.mainWindow = mainWindow
        self.GeoRefObject = GeoRefObject
        self.mainWindow.viewer_queue.append(self)
        self.setWindowTitle(GeoRefObject.filepath)
        self.ready = False
        
        self.utmCoords = sorted(self.mainWindow.utm_coords, key=lambda x: (x[0], x[1]))
        self.setStatusBar(QStatusBar(self))

        # Create main widget and layout
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        
        # Add the DrawImage (image viewer)
        self.image_viewer = DrawImage(self)
        thread = threading.Thread(target=self.load_image)
        thread.start()
        self.layout.addWidget(self.image_viewer)
        
        print("Erstelle Werkzeugleiste")
        # Werkzeugleiste
        self.toolbar = QToolBar("Werkzeugleiste")
        self.addToolBar(self.toolbar)

        print("Erstelle Tabelle")
        # Add the table widget
        self.table = QTableWidget()
        self.table.setRowCount(4)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Bild x",
            "Bild y",
            "UTM-E",
            "UTM-N"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.center_view)
        #self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.row = 0
        # Set the main layout
        self.layout.addWidget(self.table)
        self.setCentralWidget(self.central_widget)
        self.set_table_minimum_height(4)
        self.georef_toolbar()
        self.fill_table()
        self.table.selectRow(0)
        print("")
      
    def load_image(self):
        print(f"{self.GeoRefObject.filepath} warte auf Reihenfolge")
        while self.mainWindow.viewer_queue[self.mainWindow.readyViewer] != self:
            #print(self.mainWindow.readyViewer)
            pass
        print(f"{self.GeoRefObject.filepath} warte auf vorheriges Bild")
        while self.mainWindow.imageLoading2:
            while self.mainWindow.imageLoading:
                if self.main_window.viewer_queue.index(self) == 0:
                    break
                pass
            memory_info = psutil.virtual_memory()
            #start = time.time()
            while memory_info.available / (1024 ** 3) < 2:
                if self.main_window.viewer_queue.index(self) == 0:
                    break
                memory_info = psutil.virtual_memory()
                
            pass
        self.mainWindow.imageLoading2 = True
        print(f"{self.GeoRefObject.filepath} Lade Bild")
        self.cv2Image = cv2.imread(self.GeoRefObject.filepath)
        self.mainWindow.imageLoading2 = False
        self.image_viewer.loadCV2Image(self.cv2Image)
        self.mainWindow.readyViewer += 1
        self.ready = True
        print(f"{self.GeoRefObject.filepath} Bild fertig geladen")
      
    def center_view(self):
        self.row = self.table.currentRow()
        self.show_point()
    
    def georef_toolbar(self):
        print("Erstelle GeoRef Werkzeugleiste")
        # Aktionen für die Werkzeugleiste
        self.showPointAction = QAction(
            QIcon("Icon/location-pin-icon.png"), "Georeferenzierungspunkte anzeigen", self)
        self.zoomToPoint = QAction(
            QIcon("Icon/find-location-icon.png"), "Ansicht auf Punkt zentrieren", self)
        
        self.showPointAction.setStatusTip("Georeferenzierungspunkte im Bild anzeigen")
        self.showPointAction.setCheckable(True)
        self.showPointAction.setChecked(True)
        self.showPointAction.triggered.connect(self.show_point)
        
        self.zoomToPoint.setStatusTip(
            "Ansicht auf den ausgewählten Punkt zentrieren")
        self.zoomToPoint.setCheckable(True)
        self.zoomToPoint.setChecked(True)
        self.zoomToPoint.triggered.connect(self.show_point)
        
        self.AutoGeorefAction = QAction(
            QIcon("Icon/reload-map-location-outline-icon.png"), "Automatische Georeferenzierung", self)
        self.AutoGeorefAction.setStatusTip(
            "Automatische Georeferenzierung starten")
        self.AutoGeorefAction.triggered.connect(self.AutoGeoRef)
        
        self.cb_utm_corner = QComboBox()
        filename = self.GeoRefObject.filename
        region = filename[:2]
        number = filename[2:7]
        searchtext = region.upper()+" "+ number
        
        for index, liste in enumerate(self.utmCoords):
            eintrag = f"{liste[0]} {liste[1]}"
            self.cb_utm_corner.addItem(eintrag)
            if liste[1] == searchtext:
                self.cb_utm_corner.setCurrentIndex(index)
        
        self.applyGeoPoint = QAction(
            QIcon("Icon/check-mark-box-line-icon.png"), "UTM-Koordinaten anwenden")
        self.applyGeoPoint.setStatusTip("Ausgewählte Flurkartenecken in die Tabelle schreiben")
        self.applyGeoPoint.triggered.connect(self.write_UTM)
        
        self.showImage = QAction(
            QIcon("Icon/img-file-icon.png"), "Koordinaten aus Bild auswählen", self)
        self.showImage.setStatusTip("UTM-Koordinaten aus georefernziertem Bild auswählen")
        self.showImage.setCheckable(True)
        self.showImage.triggered.connect(self.open_image)
        
        self.showCroppedImage = QAction(
            QIcon("Icon/object-select-icon.png"), "Zugeschnittenes Bild", self)
        self.showCroppedImage.setStatusTip("Zugeschnittenes Bild anzeigen")
        self.showCroppedImage.setCheckable(True)
        self.showCroppedImage.setChecked(False)
        self.showCroppedImage.triggered.connect(self.load_cropped)
        
        self.CroppL = QAction(
            QIcon("Icon/object-select-iconL.png"), "linke Seite", self)
        self.CroppL.setStatusTip("Zugeschnittenes Bild anzeigen")
        self.CroppL.setCheckable(True)
        self.CroppL.setDisabled(True)
        self.CroppL.triggered.connect(self.load_cropped)
        
        self.CroppO = QAction(
            QIcon("Icon/object-select-iconO.png"), "obere Seite", self)
        self.CroppO.setStatusTip("Zugeschnittenes Bild anzeigen")
        self.CroppO.setCheckable(True)
        self.CroppO.setDisabled(True)
        self.CroppO.triggered.connect(self.load_cropped)
        
        self.CroppR = QAction(
            QIcon("Icon/object-select-iconR.png"), "rechte Seite", self)
        self.CroppR.setStatusTip("Zugeschnittenes Bild anzeigen")
        self.CroppR.setCheckable(True)
        self.CroppR.setDisabled(True)
        self.CroppR.triggered.connect(self.load_cropped)
        
        self.CroppU = QAction(
            QIcon("Icon/object-select-iconU.png"), "untere Seite", self)
        self.CroppU.setStatusTip("Zugeschnittenes Bild anzeigen")
        self.CroppU.setCheckable(True)
        self.CroppU.setDisabled(True)
        self.CroppU.triggered.connect(self.load_cropped)

        arrowRight = QAction(
            QIcon("Icon/select-box-arrow-right-icon.png"), "nächster Punkt", self)
        arrowRight.setStatusTip("nächsten Punkt auswählen")
        arrowRight.triggered.connect(self.next_line)
        
        # Aktionen der Werkzeugleiste hinzufügen
        self.toolbar.setIconSize(QSize(32, 32))
        self.toolbar.addAction(self.showPointAction)
        self.toolbar.addAction(self.zoomToPoint)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.cb_utm_corner)
        self.toolbar.addAction(self.applyGeoPoint)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.showImage)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.showCroppedImage)
        self.toolbar.addAction(self.CroppL)
        self.toolbar.addAction(self.CroppO)
        self.toolbar.addAction(self.CroppR)
        self.toolbar.addAction(self.CroppU)
        self.toolbar.addSeparator()
        self.toolbar.addAction(arrowRight)
        #self.toolbar.addAction(self.AutoGeorefAction)
        
        # self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    
    def next_line(self):
        if self.row == 3:
            self.close()
        else:
            self.table.selectRow(self.row+1)
            self.center_view()
    
    def write_UTM(self):
        index = self.cb_utm_corner.currentIndex()
        line = self.utmCoords[index]
        for row, e in enumerate(range(0,self.table.rowCount()*2,2)):
            self.table.item(row,2).setText(line[e+2])
            self.table.item(row,3).setText(line[e+3])
        self.table.resizeColumnsToContents()
    
    def open_image(self):
        if self.showImage.isChecked():
            options = QFileDialog.Options()
            files, _ = QFileDialog.getOpenFileNames(self, "Bilddateien auswählen", "", "Bilddateien (*.png *.jpg *.jpeg *.bmp *.tif);;Alle Dateien (*)", options=options)
            if files:
                file = files[0]
                for e in self.mainWindow.georefObjectList:
                    if e.filepath == file:
                        ex_image = e
                if not ex_image:
                    ex_image = georef_object(file)
                self.worldParam = ex_image.worldParam
                if self.worldParam:
                    self.showImage.setChecked(True)
                    self.mainWindow.imageLoading2 = True
                    image = cv2.imread(ex_image.filepath)
                    self.mainWindow.imageLoading2 = False
                    self.image_viewer.loadCV2Image(image)
                else:
                    self.showImage.setChecked(False)
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText(f"Die Datei {ex_image.filepath} enthält keine Georeferenzierungsparameter und kann nicht für die Koordinatenauswahl verwendet werden.")
                    msg.setWindowTitle("Keine Georeferenzierung")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
            else:
                self.showImage.setChecked(False)
        else:
            self.showImage.setChecked(False)
            self.image_viewer.loadCV2Image(self.cv2Image)
        self.showPointAction.setChecked(not self.showImage.isChecked())
        self.showPointAction.setEnabled(not self.showImage.isChecked())
        self.zoomToPoint.setChecked(not self.showImage.isChecked())
        self.zoomToPoint.setEnabled(not self.showImage.isChecked())
        self.showCroppedImage.setChecked(False)
        self.showCroppedImage.setEnabled(not self.showImage.isChecked())
        self.show_point()
    
    def calc_UTM_xy(self,x,y):
        A = float(self.worldParam[0])
        D = float(self.worldParam[1])
        B = float(self.worldParam[2])
        E = float(self.worldParam[3])
        C = float(self.worldParam[4])
        F = float(self.worldParam[5])
        geo_x = C + y * B + x * A
        geo_y = F + y * E + x * D
        self.table.item(self.row,2).setText(str(geo_x))
        self.table.item(self.row,3).setText(str(geo_y))
        self.table.resizeColumnsToContents()
    
    def load_cropped(self):
        if self.showCroppedImage.isChecked():
            cornerParam = []
            for row in range(self.table.rowCount()):
                x = float(self.table.item(row, 0).text())
                y = float(self.table.item(row, 1).text())
                ux = float(self.table.item(row, 2).text())
                uy = float(self.table.item(row, 3).text())
                cornerParam.append((x,y,ux,uy))
            L = self.CroppL.isChecked()
            O = self.CroppO.isChecked()
            R = self.CroppR.isChecked()
            U = self.CroppU.isChecked()
            cornerParam.append((L,O,R,U))
            crop = Crop_Image.RotCropImage(cv2Image = self.cv2Image)
            image, cropCorners = crop.rotcrop(cornerParam)
            self.image_viewer.centerOn(cropCorners[1][0],cropCorners[1][1])
        else:
            image = self.cv2Image
        self.CroppL.setDisabled(not self.showCroppedImage.isChecked())
        self.CroppO.setDisabled(not self.showCroppedImage.isChecked())
        self.CroppR.setDisabled(not self.showCroppedImage.isChecked())
        self.CroppU.setDisabled(not self.showCroppedImage.isChecked())
        self.showPointAction.setChecked(not self.showCroppedImage.isChecked())
        self.showPointAction.setDisabled(self.showCroppedImage.isChecked())
        self.zoomToPoint.setChecked(not self.showCroppedImage.isChecked())
        self.zoomToPoint.setDisabled(self.showCroppedImage.isChecked())
        self.showImage.setChecked(False)
        self.showImage.setDisabled(self.showCroppedImage.isChecked())
        self.show_point()
        self.image_viewer.loadCV2Image(image)
        
    def fill_table(self):
        """
        self.table.setHorizontalHeaderLabels([
            "Bild x",
            "Bild y",
            "UTM-E",
            "UTM-N",
        """
        print("Fülle Tabelle")
        if self.GeoRefObject.txtParam:
            txtParam = self.GeoRefObject.txtParam
        elif self.GeoRefObject.worldParam:
            txtParam = self.calc_corner_param()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Berechnung Corner-Daten")
            msg.setText(f"{self.GeoRefObject.filename}: \nDie Daten für die Bildpunkte wurden aus Georeferenzierungsdaten und den Koordinaten der Flurkarten-Blattecken berechnet.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        else:
            daten = georef.search_csv(self.GeoRefObject.filename, self.utmCoords)
            txtParam = []
            for p in daten:
                txtParam.append([0,0,p[0],p[1]])
            txtParam.append([1,1,1,1])
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Corner-Daten")
            msg.setText(f"{self.GeoRefObject.filename}: \nEs sind keine Daten für die Blattecken vorhanden. Die Punktkoordinaten wurden  auf X=0 und Y=0 gesetzt")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        for r, point in enumerate(txtParam[:-1]):
            for c, e in enumerate(point):
                self.table.setItem(r, c, QTableWidgetItem(str(e)))
        self.table.itemChanged.connect(self.show_point)
        self.CroppL.setChecked(bool(txtParam[-1][0]))
        self.CroppO.setChecked(bool(txtParam[-1][1]))
        self.CroppR.setChecked(bool(txtParam[-1][2]))
        self.CroppU.setChecked(bool(txtParam[-1][3]))
        self.showPointAction.triggered.connect(self.show_point)
        self.zoomToPoint.triggered.connect(self.show_point)
        self.table.resizeColumnsToContents()

    def calc_corner_param(self):
        A = self.GeoRefObject.worldParam[0]
        D = self.GeoRefObject.worldParam[1]
        B = self.GeoRefObject.worldParam[2]
        E = self.GeoRefObject.worldParam[3]
        C = self.GeoRefObject.worldParam[4]
        F = self.GeoRefObject.worldParam[5]

        daten = georef.search_csv(self.GeoRefObject.filename, self.utmCoords)
        txtParam = []
        for p in daten:
            geoX = p[0]
            geoY = p[1]
            col = (geoX - C) / A
            row = (geoY - F) / E
            # Berücksichtigung von Rotation
            if B != 0 or D != 0:
                det = A * E - B * D
                col = ((geoX - C) * E - (geoY - F) * B) / det
                row = ((geoY - F) * A - (geoX - C) * D) / det
            txtParam.append([col,row,geoX,geoY])
        txtParam.append([1,1,1,1])
        return(txtParam)
            

    def set_table_minimum_height(self, visible_rows):
        """Setzt die Mindesthöhe der Tabelle basierend auf der Anzahl sichtbarer Zeilen."""
        # Höhe einer Tabellenzeile ermitteln
        row_height = self.table.verticalHeader().sectionSize(0)  # Höhe einer Zeile
        header_height = self.table.horizontalHeader().height()   # Höhe des Tabellenkopfs

        # Gesamthöhe berechnen: Höhe der sichtbaren Zeilen + Tabellenkopf + Rahmen
        total_height = row_height * visible_rows + \
            header_height + (self.table.frameWidth() * 2)
        self.table.setMaximumHeight(total_height)
        self.table.setMinimumHeight(total_height)
    
    def AutoGeoRef(self):
        print("AutoGeoRef gestartet")
        self.MainWindow.georef_task(self.MainWindowRow)
        
    def show_point(self):
        if self.showPointAction.isChecked():
            self.showPointAction.setStatusTip(
                "Georeferenzierungspunkte im Bild ausblenden")
            self.showPointAction.setText("Georeferenzierungspunkte ausblenden")
            self.image_viewer.draw_point()
        else:
            self.showPointAction.setStatusTip(
                "Georeferenzierungspunkte im Bild anzeigen")
            self.showPointAction.setText("Georeferenzierungspunkte anzeigen")
            self.image_viewer.remove_point()
        if self.zoomToPoint.isChecked():
            #print(f"Zoome auf Punkt {self.tempX, self.tempY}")
            self.image_viewer.centerOn(float(self.table.item(self.row,0).text()), 
                                       float(self.table.item(self.row,1).text()))
            
    def closeEvent(self, event):
        imgPoints = []
        geoPoints = []
        for row in range(self.table.rowCount()):
            imgPoints.append((float(self.table.item(row,0).text()),
                             float(self.table.item(row,1).text())))
            geoPoints.append((float(self.table.item(row,2).text()),
                             float(self.table.item(row,3).text())))
        openSides = [int(self.CroppL.isChecked()),
                     int(self.CroppO.isChecked()),
                     int(self.CroppR.isChecked()),
                     int(self.CroppU.isChecked())]
        imgPoints = np.array(imgPoints)
        geoPoints = np.array(geoPoints)
        self.GeoRefObject.worldParam = list(georef.georef(imgPoints, geoPoints))
        self.GeoRefObject.txtParam = georef.get_corner_param(imgPoints, geoPoints, openSides)
        self.GeoRefObject.update_wc_icon()
        self.GeoRefObject.statusItem.setText("")
        self.mainWindow.table.viewport().update()
        self.GeoRefObject.lock = False
        del self.cv2Image
        self.mainWindow.show_next_viewer()