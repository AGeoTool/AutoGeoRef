import os, rasterio
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtGui import QIcon
class georef_object():
    def __init__(self, filepath):
        self.filepath = filepath
        self.filepathItem = QTableWidgetItem(self.filepath)
        self.filename = os.path.basename(self.filepath)
        self.GTiffFileItem = QTableWidgetItem()
        self.worldFileItem = QTableWidgetItem()
        self.txtFileItem = QTableWidgetItem()
        self.worldItem = QTableWidgetItem()
        self.statusItem = QTableWidgetItem()
        self.txtItem = QTableWidgetItem()
        self.lock = False
        
        self.update_wc_path()
        self.update_wc_param()
        self.check_geotiff()
        
    def get_current_row(self):
        return(self.filepathItem.row())
            
    def update_wc_path(self):
        self.lock = True
        def create_icon_item(path, extension, icon_item):
            """Hilfsfunktion, um den Pfad zu prüfen und ein Icon-Item zu erstellen."""
            full_path = f"{path[:-len(extension)]}{extension}"
            if os.path.exists(full_path):
                icon_item.setIcon(QIcon("Icon/green-checkmark-icon.png"))
                return full_path
            else:
                icon_item.setIcon(QIcon("Icon/remove-close-round-red-icon.png"))
                return False

        # World-Datei prüfen und Icon setzen
        worldExt =  self.filepath[-3:-2] + self.filepath[-1:] + "w"
        self.worldPath = create_icon_item(self.filepath, worldExt, self.worldFileItem)
    
        # TXT-Datei prüfen und Icon setzen
        self.txtPath = create_icon_item(self.filepath, "txt", self.txtFileItem)
        
    
    def update_wc_param(self):
        if self.worldPath:
            with open(self.worldPath) as world:
                self.worldParam = [float(line.strip()) for line in world]
                #print(self.worldParam)
        else:
            self.worldParam = False
            
        
        if self.txtPath:
            with open(self.txtPath) as txt:
                self.txtParam = []
                for line in txt:
                    line = line.strip()
                    elem = [float(elem) for elem in line.split(";")]
                    self.txtParam.append(elem)
                
                #print(self.txtParam)
        else:
            self.txtParam = False
        
        self.lock = False
    
    def update_wc_icon(self):
        self.set_item(self.worldItem, self.worldParam)
        self.set_item(self.txtItem, self.txtParam)
            
    def check_geotiff(self):
        self.lock = True
        try:
            # Datei öffnen
            with rasterio.open(self.filepath) as src:
                # Überprüfen, ob es sich um eine GeoTIFF-Datei handelt
                is_geotiff = src.driver == "GTiff"
                # Georeferenzierungsinformationen auslesen
                if not src.crs:
                    is_geotiff = False
                if is_geotiff:
                    # Transformationsmatrix auslesen
                    transform = src.transform
                    # Georeferenzierungsparameter extrahieren
                    # pixel_size_x = transform.a  # Pixelgröße in X-Richtung
                    # rotation_x = transform.b   # Rotation in X-Richtung
                    # rotation_y = transform.d   # Rotation in Y-Richtung
                    # pixel_size_y = transform.e  # Pixelgröße in Y-Richtung (negativ für nach unten)
                    # upper_left_x = transform.c  # X-Koordinate des oberen linken Pixels
                    # upper_left_y = transform.f  # Y-Koordinate des oberen linken Pixels
                    if (transform.c, transform.f) == (0,0):
                        is_geotiff = False
                    else:
                        self.worldParam = [transform.a, transform.d, transform.b, transform.e, transform.c, transform.f]
                    """
                    print()
                    print(f"Datei: {self.filepath}")
                    print(f"Driver: {src.driver}")
                    print(f"CRS: {src.crs}")  # Koordinatenreferenzsystem
                    print(f"Transform: {src.transform}")  # Transformationsmatrix
                    print(f"Breite x Höhe: {src.width} x {src.height}")
                    print(f"Anzahl der Bänder: {src.count}")
                    print(f"Auflösung: {src.res}")  # Pixelgröße (X und Y)
                    """
                self.set_item(self.GTiffFileItem, is_geotiff)
        except Exception as e:
            self.set_item(self.GTiffFileItem, False)
            print(f"Fehler beim Verarbeiten der Datei: {e}")
        self.update_wc_icon()
        self.lock = False
    
    def set_item(self, Item, check):
        if check:
            Item.setIcon(QIcon("Icon/green-checkmark-icon.png"))
        else:
            Item.setIcon(QIcon("Icon/remove-close-round-red-icon.png"))