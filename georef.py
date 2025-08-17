import numpy as np
import csv

def georef(imgPoint, geoPoint):
    # Anzahl der Punkte
    n_points = imgPoint.shape[0]
    
    # Designmatrix A erstellen
    A = np.zeros((2 * n_points, 6))
    B = np.zeros((2 * n_points, 1))

    for i in range(n_points):
        A[2*i, 0] = imgPoint[i, 0]  # a * x
        A[2*i, 2] = imgPoint[i, 1]  # b * y
        A[2*i, 4] = 1                   # c (Offset in X)
        A[2*i + 1, 1] = imgPoint[i, 0]  # d * x
        A[2*i + 1, 3] = imgPoint[i, 1]  # e * y
        A[2*i + 1, 5] = 1                   # f (Offset in Y)
        B[2*i] = geoPoint[i, 0]  # Georeferenzierte X-Koordinaten
        B[2*i + 1] = geoPoint[i, 1]  # Georeferenzierte Y-Koordinaten
    
    X, residuals, rank, s = np.linalg.lstsq(A, B, rcond=None)
    # X enthält die gesuchten Parameter a, d, b, e, c, f
    parameters = X.flatten()
    print(parameters)
    #print(residuals)
    return(parameters)

def search_csv2(name,utm_file,utm_coords):
    region = name[:2]#.upper()
    number = name[2:7]
    searchtext = region.upper()+" "+number
    found = ""
    z = 0
    while found == "":
        utm_file.seek(0)
        for line in utm_coords:
            if searchtext in line:
                found = line
        #print(z, found)
        z += 1
    print("Anzahl:",z,"Suchtext:",searchtext,"Gefunden:",found)
    found = list(map(float, found[2:]))
    found = np.array(found).reshape(-1, 2)
    return(found)

def search_csv(name,utm_coords):
    while True:
        try:
            region = name[:2]#.upper()
            number = name[2:7]
            searchtext = region.upper()+" "+ number
            print(searchtext)
            found = ""
            for line in utm_coords:
                if searchtext in line:
                    found = line
            found = list(map(float, found[2:]))
            found = np.array(found).reshape(-1, 2)
            return(found)
        except Exception as e:
            print(e)

def load_coords2():
    utm_file = open('Flurkarten_Blattecken UTM.csv')
    utm_coords = csv.reader(utm_file, delimiter=';')
    print("UTM-Tabelle geladen")
    return(utm_file,utm_coords)

def load_coords():
    with open('Flurkarten_Blattecken UTM.csv') as utm_file:
        utm_coords = list(csv.reader(utm_file, delimiter=';'))  # Konvertiere in eine Liste
    print("UTM-Tabelle geladen")
    return utm_coords

def write_tfw(path, parameters):
    with open(path, mode='w', encoding='utf-8') as file:
        for e in parameters:
            file.write(str(e)+"\n")

def write_corner(path, imgPoint, geoPoint, openSides):
    with open(path, mode='w', encoding='utf-8') as file:
        for p, g in zip(imgPoint, geoPoint):
            line = f"{p[0]};{p[1]};{g[0]};{g[1]}\n"
            file.write(line)
        file.write(";".join(map(str, openSides)) + "\n")

def get_corner_param(imgPoint, geoPoint, openSides):
    fileList = []
    for p, g in zip(imgPoint, geoPoint):
        line = [p[0], p[1], g[0], g[1]]
        fileList.append(line)
    fileList.append(openSides)
    return(fileList)

"""
imgPoint = np.array([
    [1, 2],
    [3, 4],
    [4, 5],
    [6, 7]
])
geoPoint = np.array([
    [578153.2381, 5438252.039],
    [578152.5516, 5439397.263],
    [579297.8431, 5439397.924],
    [579298.5334, 5438252.711]
])
openSides = [0,1,1,0]
write_corner("corner_test.txt", imgPoint, geoPoint, openSides)
"""