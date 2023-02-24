import numpy as np 
from typing import Iterable

from m23.file.log_file_combined_file import LogFileCombinedFile

def get_star_to_ignore_bit_vector(log_file_combined_file: LogFileCombinedFile) -> Iterable[int]:
    """
    Looks at the log_file_combined file and returns a bit vector representing whether that 
    star should be ignored when calculating the norm factor for the night. We create this 
    so that we can ignore stars at the edges which had a bright line at the edge after alignment 
    step in old camera images. Note that in the bit vector, 0 means that star is to be 
    avoided, 1 means the star is to be included.
    """
    x_coordinates = log_file_combined_file.get_x_position_column()
    y_coordinates = log_file_combined_file.get_y_position_column()
    bit_vector=[]
    # IDL and Python has axes reversed
    dist_from_top_left = np.sqrt(x_coordinates**2+y_coordinates**2) 
    dist_from_top_right = np.sqrt(x_coordinates**2 +(y_coordinates-1023)**2)
    dist_from_bottom_left = np.sqrt((x_coordinates-1023)**2+y_coordinates**2)
    dist_from_bottom_right = np.sqrt((x_coordinates-1023)**2+(y_coordinates-1023)**2)

    # indices of stars with least distances from four corners 
    min_top_left = np.argmin(dist_from_top_left)
    min_top_right = np.argmin(dist_from_top_right)
    min_bottom_left = np.argmin(dist_from_bottom_left)
    min_bottom_right = np.argmin(dist_from_bottom_right)
    
    # star coordinates nearest to the four corners 
    top_left_star = [x_coordinates[min_top_left], y_coordinates[min_top_left]]
    top_right_star = [x_coordinates[min_top_right], y_coordinates[min_top_right]]
    bottom_left_star = [x_coordinates[min_bottom_left], y_coordinates[min_bottom_left]]
    bottom_right_star = [x_coordinates[min_bottom_right], y_coordinates[min_bottom_right]]

    # Fit linear lines to the four stars in the four corners, making a quadrilateral
    left_line = np.polyfit([top_left_star[0], bottom_left_star[0]], [top_left_star[1], bottom_left_star[1]], 1)
    right_line = np.polyfit([top_right_star[0], bottom_right_star[0]], [top_right_star[1], bottom_right_star[1]], 1)
    top_line = np.polyfit([top_left_star[0], top_right_star[0]], [top_left_star[1], top_right_star[1]], 1)
    bottom_line = np.polyfit([bottom_left_star[0], bottom_right_star[0]], [bottom_left_star[1], bottom_right_star[1]], 1)

    # We crop in 12 pixels from those four lines, and exclude stars that are outside of this region 
    x_and_y_coordinates = np.stack((x_coordinates, y_coordinates), axis = 1)
    for star_index, star_position in enumerate(x_and_y_coordinates): 
        if ((star_position[1] >= left_line[0]*star_position[0] + left_line[1] + 12) # from left line 
            and (star_position[1] <= right_line[0]*star_position[0] + right_line[1] - 12) # from right line
            and (star_position[0] <= (star_position[1]-bottom_line[1])/bottom_line[0]-12) # from bottom line 
            and (star_position[0] >= (star_position[1]-top_line[1])/top_line[0]+12)): # from top line 
                bit_vector.append(1)
        else:
            bit_vector.append(0)

    return bit_vector
