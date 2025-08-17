import cv2
import numpy as np
from PIL import Image
    
def image_loader(imgPath):
    image = cv2.imread(imgPath, cv2.IMREAD_GRAYSCALE)
    dpi = get_image_dpi(imgPath)[0]
    return(image, dpi)

def get_image_dpi(image_path):
    with Image.open(image_path) as img:
        dpi = img.info.get('dpi')
        return dpi

def line_segment_detector(image, dpi):
    lsd = cv2.createLineSegmentDetector(0)
    rect = []
    for s in range(4):
        # print()
        # print("Linie:", s)
        h, w = image.shape
        lines = lsd.detect(image[int(h/20):int(h/10),0:w])[0]
        
        lines = np.reshape(lines,(len(lines),4))
        lines[:,[1,3]] += h/20
        #np.savetxt(f'daten{s}.csv', lines, delimiter=';')
        lines = filter_lines(lines, dpi)
        lines = rot_lines(lines,s,h,w)
        lines = np.delete(lines, np.s_[4:7],axis=1)
        
        rect.append(lines)
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        
    #color_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    #draw_lines(rect, "All", color_image)
    return(rect)

def rot_lines(lines,pos,h,w):
    match pos:
        case 0:
            pass
        case 1:
            #print(f"Pos {pos}")
            lines[:,[0,1,2,3]] = lines[:,[1,0,3,2]]
            lines[:,[1,3]] = h - lines[:,[1,3]]
        case 2:
            #print(f"Pos {pos}")
            lines[:,[0,2]] = w - lines[:,[0,2]]
            lines[:,[1,3]] = h - lines[:,[1,3]]
        case 3:
            #print(f"Pos {pos}")
            lines[:,[0,1,2,3]] = lines[:,[1,0,3,2]]
            lines[:,[0,2]] = h - lines[:,[0,2]]
    return(lines)

def draw_lines(rect,name,image):
    for lines in rect:
        file = lines
        #file = open(filepath, mode='r', encoding='utf-8')
        
        for l in file:
            #print(l[0])
            x1 = int(float(l[0]))
            y1 = int(float(l[1]))
            x2 = int(float(l[2]))
            y2 = int(float(l[3]))
            drawn_img = cv2.line(image, (x1,y1), (x2,y2), (255,255,0))
    cv2.imwrite(name+".jpg", drawn_img)

def filter_lines(lines, dpi):
    lines = m_filter(lines)
    lines_start = lines
    lines_filtered = np.zeros(shape=(0, 4))
    returnline = lines_filtered
    search_go = True
    i = 0
    while search_go:
        try:
            # print()
            # print("Durchlauf:",i)
            array1 = lines_start
            array2 = lines_filtered
            
            # Kombinieren und doppelte Zeilen entfernen
            combined = np.vstack((array1, array2))
            #rounded = np.round(combined, decimals=4)
            # Doppelte Zeilen identifizieren
            unique_rows, counts = np.unique(combined, axis=0, return_counts=True)
            
            # Behalte nur Zeilen, die genau einmal vorkommen
            lines = unique_rows[counts == 1]
            lines_start = lines
            #print(lines.shape)
            # Berechne den kleinsten und größten x-Wert (Spalten 0 und 2)
            min_x = np.min(lines[:, [0, 2]], axis=1)
            max_x = np.max(lines[:, [0, 2]], axis=1)
            min_y = np.min(lines[:, [1, 3]], axis=1)
            # Füge die min_x und max_x Spalten zum Array hinzu
            lines = np.column_stack((lines, min_x, max_x, min_y))
            go = calc_x_cover(lines, dpi)
            while go:
                lines = lines[lines[:, 6].argsort()]
                #print(lines,len(lines))
                # Extrahiere die 7. Spalte (kleinster y-Wert)
                min_y_values = lines[:, 6]
                # Berechne die Differenzen zwischen aufeinanderfolgenden Werten
                diffs = np.diff(min_y_values)
                
                # Berechne den Mittelwert der Differenzen
                mean_deviation_all = np.mean(diffs)
                
                # Bestimme den Index der maximalen Differenz
                index_of_max_diff = np.argmax(diffs)
                
                # Teil 1: Differenzen von Anfang bis zur maximalen Differenz (einschließlich)
                diffs_part_1 = diffs[:index_of_max_diff + 1]
                
                # Teil 2: Differenzen von der maximalen Differenz bis zum Ende
                diffs_part_2 = diffs[index_of_max_diff:]
                #print("Teilung:", min_y_values[index_of_max_diff])
                # Berechne den Mittelwert für beide Teile
                mean_part_1 = np.mean(diffs_part_1)
                mean_part_2 = np.mean(diffs_part_2)
                
                diff_std_1 = mean_part_1-mean_deviation_all
                diff_std_2 = mean_part_2-mean_deviation_all
                
                diff_y_1 = min_y_values[index_of_max_diff]-min_y_values[0]
                diff_y_2 = min_y_values[-1]-min_y_values[index_of_max_diff]
                
                evalu_part_1 = abs(diff_std_1*diff_y_1)
                evalu_part_2 = abs(diff_std_2*diff_y_2)
                
                #print("Werte gesamt",std_deviation_all,index_of_max_diff)
                #print("Werte 1",diff_y_1,std_part_1,diff_std_1,evalu_part_1)
                #print("Werte 2",diff_y_2,std_part_2,diff_std_2,evalu_part_2)
                if go:
                    if evalu_part_1 > evalu_part_2:
                        #print("Part 1")
                        #delete Part one
                        lines_new = np.delete(lines, np.s_[:index_of_max_diff+1], axis=0)
                    elif evalu_part_1 < evalu_part_2:
                        #print("Part 2")
                        #delete Part Two
                        lines_new = np.delete(lines, np.s_[index_of_max_diff+1:], axis=0)
                    else:
                        #Ausweichen auf Mittelwert
                        if abs(diff_std_1) > abs(diff_std_2):
                            #print("Part 1")
                            #delete Part one
                            lines_new = np.delete(lines, np.s_[:index_of_max_diff+1], axis=0)
                        else:
                            #print("Part 2")
                            #delete Part Two
                            lines_new = np.delete(lines, np.s_[index_of_max_diff+1:], axis=0)
                #print(len(lines))
                go = calc_x_cover(lines_new, dpi)
                lines = lines_new
            lines = np.delete(lines, np.s_[4:7],axis=1)
            lines_filtered = lines
            #print("Gefiltert")
            #print(lines_filtered.shape)
            #print(lines_filtered)
            
            i += 1
            if len(lines_filtered) > len(returnline):
                returnline = lines_filtered
        except Exception as e:
            print(e)
            search_go = False
    return(returnline)
    
def m_filter(lines):
    slopes = abs((lines[:, 3] - lines[:, 1]) / (lines[:, 2] - lines[:, 0]))
    # Zeilen filtern, bei denen die Steigung <= 1 ist
    filtered_array = lines[slopes <= 0.01]
    #print(len(filtered_array))
    #print("M-Filter fertig")
    return(filtered_array)

def calc_x_cover(lines, dpi):
    sorted_array = lines[lines[:, 4].argsort()]
    #print(sorted_array.shape)
    current_max = sorted_array[0][5]
    current_gap = 0
    min_y = np.min(lines[:, 6], axis=0)
    max_y = np.max(lines[:, 6], axis=0)
    #min_x = np.min(lines[:, 4], axis=0)
    #max_x = np.max(lines[:, 4], axis=0)
    
    #print(current_max)
    for i in sorted_array:
        if i[4]>current_max:
            current_gap += i[4]-current_max
        if i[5]>current_max:
            current_max = i[5]
    
    cover = 1-(current_gap/(current_max-sorted_array[0][4]))
    # print("calc_x_cover:", cover,
    #       "\nDelta Cover:", 1-(max_y-min_y)*0.01*2,
    #       "\ny min / max:", min_y, "/", max_y,
    #       "\nx min / max:", min_x, "/", max_x,
    #       "\ncurrent max:", current_max)
    return(cover>1-(max_y-min_y)*0.01*(dpi/300))

# import calc_corner
# image, dpi = image_loader("D:/UNK/NO07050-A.tif")
# rect = line_segment_detector(image, dpi)
# print(calc_corner.calc_corner(rect))
