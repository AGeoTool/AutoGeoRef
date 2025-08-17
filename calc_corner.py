import numpy as np

def calc_corner(rect):
    O, L, U, R = add_min_max(rect[0],0), add_min_max(rect[1],1), add_min_max(rect[2],2), add_min_max(rect[3],3)
    #print(O,L,U,R)
    OL = intersection_of_vectors(O[0][0],O[0][1],O[0][2],L[0][0],L[0][1],L[0][2])
    OR = intersection_of_vectors(O[1][0],O[1][1],O[1][2],R[0][0],R[0][1],R[0][2])
    UL = intersection_of_vectors(U[0][0],U[0][1],U[0][2],L[1][0],L[1][1],L[1][2])
    UR = intersection_of_vectors(U[1][0],U[1][1],U[1][2],R[1][0],R[1][1],R[1][2])
    return(UL,OL,OR,UR)
    
def add_min_max(lines,s):
    x_min = []
    y_min = []
    theta_min = []
    weight_min = []
    x_max = []
    y_max = []
    theta_max = []
    weight_max = []
    min_x = min(np.min(lines[:, [0, 2]], axis=1))
    max_x = max(np.max(lines[:, [0, 2]], axis=1))
    min_y = min(np.min(lines[:, [1, 3]], axis=1))
    max_y = max(np.max(lines[:, [1, 3]], axis=1))
    for (x1, y1, x2, y2) in lines:
        # Calculate directional vector
        dx, dy = x2 - x1, y2 - y1
        
        # Check if the direction is primarily negative in x; if so, reverse the direction
        if s in (0,2):
            if dx < 0:
                x1, y1, x2, y2 = x2, y2, x1, y1
                dx, dy = -dx, -dy
            weight_low = (min_x/min(x1,x2))**4
            weight_high = (max(x1,x2)/max_x)**4
        else:
            if dy < 0:
                x1, y1, x2, y2 = x2, y2, x1, y1
                dx, dy = -dx, -dy
            weight_low = (min_y/min(y1,y2))**4
            weight_high = (max(y1,y2)/max_y)**4
        
        x_min.append(x1)
        y_min.append(y1)
        theta_min.append(np.degrees(np.arctan2(dy, dx)))
        weight_min.append(weight_low)
        
        x_max.append(x1)
        y_max.append(y1)
        theta_max.append(np.degrees(np.arctan2(dy, dx)))
        weight_max.append(weight_high)
        
        #print(np.degrees(np.arctan2(dy, dx)),x1,y1,x2,y2,weight_low,weight_high)
    w_x_min = np.average(x_min, weights=weight_min)
    w_y_min = np.average(y_min, weights=weight_min)
    theta = np.mean(theta_min)
    w_x_max = np.average(x_max, weights=weight_max)
    w_y_max = np.average(y_max, weights=weight_max)
    return((w_x_min,w_y_min,theta), (w_x_max,w_y_max,theta))

def intersection_of_vectors(x1, y1, theta1, x2, y2, theta2):
    # Convert angles to radians
    theta1_rad = np.radians(theta1)
    theta2_rad = np.radians(theta2)
    
    # Calculate slopes (m1, m2) using the tangent of the angles
    m1 = np.tan(theta1_rad)
    m2 = np.tan(theta2_rad)
    
    # Check for parallel vectors (no intersection if slopes are equal)
    if np.isclose(m1, m2):
        return None  # No intersection point (vectors are parallel)
    
    # Calculate x-coordinate of intersection
    x_intersect = ((m1 * x1 - m2 * x2) + (y2 - y1)) / (m1 - m2)
    
    # Calculate y-coordinate of intersection using one of the line equations
    y_intersect = m1 * (x_intersect - x1) + y1
    
    return x_intersect, y_intersect
