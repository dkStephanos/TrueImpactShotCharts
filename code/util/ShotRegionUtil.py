import numpy as np
from shapely.geometry import Polygon, Point

# Constants for court dimensions
BASKET_X = 41.75
THREE_POINT_RADIUS = 23.75
THREE_POINT_CURVE_START = 14
CORNER_THREE_DISTANCE_TO_SIDELINE = 3
CORNER_THREE_DISTANCE = 22
RESTRICTED_AREA_RADIUS = 4
COURT_LENGTH = 94
COURT_WIDTH_HALF = 25
FREE_THROW_LINE_DISTANCE = 19
FREE_THROW_LINE_WIDTH_HALF = 8  # Half the width of the free throw line
ELBOW_DISTANCE_FROM_CENTER = 19
X_MIN = 0
X_MAX = 47
Y_MIN = -25
Y_MAX = 25

def compute_full_arc_coords():
    # Calculate the angle where the three-point arc needs to intersect the sideline.
    # The hypotenuse in this case is directly the three-point radius.
    delta_x = COURT_WIDTH_HALF - CORNER_THREE_DISTANCE_TO_SIDELINE  # Horizontal distance from the sideline inside the arc
    
    # Calculate the angle at which the three-point line intersects the sidelines using the correct triangle dimensions
    theta_sideline = np.arcsin(delta_x / THREE_POINT_RADIUS)

    # Generate points for the full three-point arc
    return [
        (
            BASKET_X - THREE_POINT_RADIUS * np.cos(angle),
            THREE_POINT_RADIUS * np.sin(angle),
        )
        for angle in np.linspace(-theta_sideline, theta_sideline, 360)
    ]
    
def compute_center_arc(full_arc_coords):
    # Filter the full arc coordinates to narrow down to the center three-point arc segment
    center_arc_coords = [
        (x, y) for (x, y) in full_arc_coords
        if -FREE_THROW_LINE_WIDTH_HALF <= y <= FREE_THROW_LINE_WIDTH_HALF
    ]
    return center_arc_coords
    
def compute_wing_arcs(full_arc_coords):
    # Define the wing arc sections by filtering out the center part
    wing_arc_coords = [
        point for point in full_arc_coords
        if abs(point[1]) > FREE_THROW_LINE_WIDTH_HALF
    ]

    # Extending and finalizing left wing arc
    left_wing_arc = [
        (0, Y_MAX - CORNER_THREE_DISTANCE_TO_SIDELINE)  # Starting at the top sideline intersection
    ] + [point for point in wing_arc_coords if point[1] > 0] + [
        (33, COURT_WIDTH_HALF),  # Additional point at the bottom of the corner three, at the court edge
        (0, COURT_WIDTH_HALF)   # Endpoint at the sideline at half-court width
    ]
    left_wing_arc.append((0, Y_MAX - CORNER_THREE_DISTANCE_TO_SIDELINE))  # Close the polygon by returning to the starting point

    # Extending and finalizing right wing arc
    right_wing_arc = [
        (0, Y_MIN + CORNER_THREE_DISTANCE_TO_SIDELINE)  # Start at the lower sideline intersection
    ] + list(reversed([point for point in wing_arc_coords if point[1] < 0])) + [
        (33, -COURT_WIDTH_HALF),  # Additional point at the bottom of the corner three, at the court edge
        (0, -COURT_WIDTH_HALF)  # Existing endpoint at the sideline at half-court width (negative)
    ]
    right_wing_arc.append((0, Y_MIN + CORNER_THREE_DISTANCE_TO_SIDELINE))  # Close the polygon by returning to the starting point

    return left_wing_arc, right_wing_arc

def compute_close_range_arc():
    # Define the center and radius
    center_point = Point(45, 0)
    radius = 11  # Adjusted radius to match the desired coverage

    # Generate points for the left half-circle
    arc = [
        (center_point.x + radius * np.cos(angle), center_point.y + radius * np.sin(angle))
        for angle in np.linspace(np.pi / 2, 3 * np.pi / 2, 180)  # Generate left half-circle from 90 to 270 degrees
    ]

    # Add points to connect the semicircle to the out-of-bounds line
    # This rectangle will run from (45, 11) to (47, 11) and back down to (47, -11) and (45, -11)
    arc += [(45, -11), (47, -11), (47, 11)]

    # Complete the arc by connecting back to the start
    arc.append((45, 11))  # Closing the shape by connecting to the start of the semicircle

    return arc
    
def compute_regions():
    full_arc_coords = compute_full_arc_coords()
    center_wing_arc = compute_center_arc(full_arc_coords)
    left_wing_arc, right_wing_arc = compute_wing_arcs(full_arc_coords)
    close_range_arc = compute_close_range_arc()

    return {
        "CENTER_THREE": Polygon(
            [(0, Y_MIN + CORNER_THREE_DISTANCE_TO_SIDELINE)]
            + center_wing_arc
            + [(0, Y_MAX - CORNER_THREE_DISTANCE_TO_SIDELINE)]
        ),
        "LEFT_WING_THREE": Polygon(left_wing_arc),
        "RIGHT_WING_THREE": Polygon(right_wing_arc),
        "CLOSE_RANGE": Polygon(close_range_arc),
        "RIGHT_CORNER_THREE": Polygon(
            [
                (
                    X_MAX - THREE_POINT_CURVE_START,
                    -COURT_WIDTH_HALF,
                ),  # Bottom right corner of the court
                (
                    X_MAX - THREE_POINT_CURVE_START,
                    -COURT_WIDTH_HALF + CORNER_THREE_DISTANCE_TO_SIDELINE,
                ),  # Start of the arc from the right sideline
                (
                    X_MAX,
                    -COURT_WIDTH_HALF + CORNER_THREE_DISTANCE_TO_SIDELINE,
                ),  # Start of the arc from the baseline
                (X_MAX, -COURT_WIDTH_HALF),  # Baseline
            ]
        ),
        "LEFT_CORNER_THREE": Polygon(
            [
                (
                    X_MAX - THREE_POINT_CURVE_START,
                    COURT_WIDTH_HALF,
                ),  # Top left corner of the court
                (
                    X_MAX - THREE_POINT_CURVE_START,
                    COURT_WIDTH_HALF - CORNER_THREE_DISTANCE_TO_SIDELINE,
                ),  # Start of the arc from the left sideline
                (
                    X_MAX,
                    COURT_WIDTH_HALF - CORNER_THREE_DISTANCE_TO_SIDELINE,
                ),  # Start of the arc from the baseline
                (X_MAX, COURT_WIDTH_HALF),  # Baseline
            ]
        ),
        "BEYOND_HALFCOURT": Polygon(
            [
                (X_MIN, Y_MIN),
                (X_MIN, Y_MAX),
                (-X_MAX, Y_MAX),
                (-X_MAX, Y_MIN),
            ]
        ),
        "RIGHT_BASELINE_MID": Polygon(
            [
                (BASKET_X, -THREE_POINT_CURVE_START),
                (BASKET_X, Y_MIN),
                (BASKET_X - FREE_THROW_LINE_DISTANCE, Y_MIN),
                (BASKET_X - FREE_THROW_LINE_DISTANCE, -THREE_POINT_CURVE_START),
            ]
        ),
        "RIGHT_ELBOW_MID": Polygon(
            [
                (BASKET_X, -THREE_POINT_CURVE_START),
                (BASKET_X - FREE_THROW_LINE_DISTANCE, -THREE_POINT_CURVE_START),
                (BASKET_X - FREE_THROW_LINE_DISTANCE, -ELBOW_DISTANCE_FROM_CENTER),
                (BASKET_X, -ELBOW_DISTANCE_FROM_CENTER),
            ]
        ),
        "LEFT_BASELINE_MID": Polygon(
            [
                (BASKET_X, Y_MAX),
                (BASKET_X - FREE_THROW_LINE_DISTANCE, Y_MAX),
                (BASKET_X - FREE_THROW_LINE_DISTANCE, THREE_POINT_CURVE_START),
                (BASKET_X, THREE_POINT_CURVE_START),
            ]
        ),
        "LEFT_ELBOW_MID": Polygon(
            [
                (BASKET_X, ELBOW_DISTANCE_FROM_CENTER),
                (BASKET_X - FREE_THROW_LINE_DISTANCE, ELBOW_DISTANCE_FROM_CENTER),
                (BASKET_X - FREE_THROW_LINE_DISTANCE, THREE_POINT_CURVE_START),
                (BASKET_X, THREE_POINT_CURVE_START),
            ]
        ),
    }

class ShotRegionUtil:
    region_colors = {
        "CLOSE_RANGE": "#FF0000",  # Red
        "LEFT_CORNER_THREE": "#00FF00",  # Green
        "RIGHT_CORNER_THREE": "#0000FF",  # Blue
        "LEFT_WING_THREE": "#FFFF00",  # Yellow
        "RIGHT_WING_THREE": "#FF00FF",  # Magenta
        "LEFT_BASELINE_MID": "#00FFFF",  # Cyan
        "RIGHT_BASELINE_MID": "#FFA500",  # Orange
        "LEFT_ELBOW_MID": "#800080",  # Purple
        "RIGHT_ELBOW_MID": "#808080",  # Gray
        "CENTER_THREE": "#000000",  # Black
        "BEYOND_HALFCOURT": "#8B4513",  # SaddleBrown
    }

    regions = compute_regions()
