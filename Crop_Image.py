import math
import cv2
import numpy as np

class RotCropImage:
    def __init__(self, cv2Image):
        """
        Initialisiert die Klasse mit einem Bild.
        :param cv2Image: cv2 Bild
        """
        self.image = cv2Image

    def rotcrop(self, corner_param: list[list[float]]):
        """
        Führt die Rotation und das Zuschneiden des Bildes aus.
        :param corner_param: Liste von Eckkoordinaten (mindestens 4 Punkte)
        :return: Zugeschnittes und gedrehtes Bild, Eckkoordinaten.
        """
        self.corner_param = corner_param
        self.corners = [(c[0], c[1]) for c in corner_param[:4]]
        self.rot_center = self.corners[1]
        
        # Winkel berechnen
        angle = self._get_angle()

        # Bild rotieren
        rotated_image = self._rotate_image(angle)

        # Neue Eckpunkte nach Rotation berechnen
        new_corners = self._get_new_corners(angle)
        #print(f"Neue Eckpunkte für Zuschnitt: {new_corners}")

        # Bild zuschneiden
        cropped_image, crop_x, crop_y = self._crop_image(new_corners, rotated_image)
        #print(f"Zugeschnittenes Bild: {cropped_image.shape}, Startpunkt: ({crop_x}, {crop_y})")
        
        #Neue Eckpunkte nach Zuschneiden berechnen
        new_corners = [(x[0] - crop_x, x[1] - crop_y) for x in new_corners]
        #print(f"Neue Eckpunkte: {new_corners}")
        return(cropped_image, new_corners)

    def _get_angle(self) -> float:
        """
        Berechnet den Durchschnittswinkel basierend auf den Ecken.

        :return: Durchschnittlicher Rotationswinkel in Radiant.
        """
        def calculate_distance(p1, p2):
            return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

        def berechne_winkel(punkt1, punkt2):
            """
            Berechnet den Winkel zwischen der Strecke durch punkt1 und punkt2 und der x-Achse.
            
            Args:
                punkt1 (tuple): Koordinaten des ersten Punktes (x1, y1).
                punkt2 (tuple): Koordinaten des zweiten Punktes (x2, y2).
            
            Returns:
                float: Winkel in Grad.
            """
            x1, y1 = punkt1
            x2, y2 = punkt2
            
            delta_x = x2 - x1
            delta_y = y2 - y1
            
            winkel_radiant = math.atan2(delta_y, delta_x)
            
            diff = np.pi/20
            
            if winkel_radiant < 0:
                winkel_radiant = np.pi + winkel_radiant
            while winkel_radiant > diff:
                winkel_radiant = winkel_radiant - np.pi / 2
            return winkel_radiant

        distance = []
        for i in range(len(self.corners)):
            for j in range(i + 1, len(self.corners)):
                dist = calculate_distance(self.corners[i], self.corners[j])
                distance.append(dist)
        
        angles = []
        for i in range(len(self.corners)):
            for j in range(len(self.corners)):
                if i < j:
                    angles.append(berechne_winkel(self.corners[i], self.corners[j]))
        distanceWeighted = 0
        weight = 0
        for d, a in zip(distance,angles):
            weight += np.mean(angles)/a
            distanceWeighted += np.mean(angles)/a*d
        
        epsilon = 0.1
        mean = distanceWeighted/weight
        diff = mean * epsilon
        
        wrongIndex = []
        for i, w in enumerate(angles):
            if abs(w) > np.pi/20:
                wrongIndex.append(i)
            if not (mean - diff < distance[i] < mean + diff):
                wrongIndex.append(i)
        wrongIndex = set(wrongIndex)
        wrongIndex = list(sorted(wrongIndex,reverse=True))
        
        for i in wrongIndex:
            angles.pop(i)
        
        return(np.mean(angles))

    def _rotate_image(self, angle: float, scale: float = 1) -> np.ndarray:
        """
        Rotiert das Bild um den gegebenen Winkel.

        :param angle: Winkel in Radiant.
        :param scale: Skalierungsfaktor.
        :return: Rotiertes Bild.
        """
        (h, w) = self.image.shape[:2]
        M = cv2.getRotationMatrix2D(self.rot_center, np.degrees(angle), scale)
        rotated = cv2.warpAffine(self.image, M, (w, h))
        return rotated

    def _get_new_corners(self, angle: float) -> list[tuple[float, float]]:
        """
        Berechnet die neuen Eckpunkte nach der Rotation.

        :param angle: Rotationswinkel in Radiant.
        :return: Liste der neuen Eckpunkte.
        """
        new_corners = []
        for c in self.corners:
            dx = c[0] - self.rot_center[0]
            dy = c[1] - self.rot_center[1]
            dist = math.dist(c, self.rot_center)
            beta = np.pi / 2 - np.arctan2(dx, dy)
            beta -= angle
            xn = self.rot_center[0] + np.cos(beta) * dist
            yn = self.rot_center[1] + np.sin(beta) * dist
            new_corners.append((xn, yn))
        return new_corners

    def _crop_image(self, corners: list[tuple[float, float]], image: np.ndarray) -> tuple[np.ndarray, int, int]:
        """
        Schneidet das Bild anhand der Eckpunkte zu.

        :param corners: Liste der Eckpunkte.
        :param image: Bild (nach Rotation).
        :return: Zugeschnittenes Bild, Startpunkt (x, y).
        """
        open_sides = self.corner_param[-1]

        # Minimal- und Maximalwerte für x und y berechnen
        min_x = int(min(corners, key=lambda x: x[0])[0]) if open_sides[0] else 0
        min_y = int(min(corners, key=lambda x: x[1])[1]) if open_sides[1] else 0
        max_x = int(max(corners, key=lambda x: x[0])[0]) if open_sides[2] else image.shape[1]
        max_y = int(max(corners, key=lambda x: x[1])[1]) if open_sides[3] else image.shape[0]

        # Zuschneiden
        cropped = image[min_y:max_y, min_x:max_x]
        return cropped, min_x, min_y
"""
cvImage = cv2.imread("D:/UK/NO08269_0393000_1_UK_00.tif")
rotcropImage = RotCropImage(cvImage)

with open("D:/UK/NO08269_0393000_1_UK_00.txt") as txt:
    txtParam = []
    for line in txt:
        line = line.strip()
        elem = [float(elem) for elem in line.split(";")]
        txtParam.append(elem)
rotcropImage.rotcrop(txtParam)
"""