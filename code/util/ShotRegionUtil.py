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

def compute_arc_coords():
    # Calculate theta for the center three-point arc segment
    theta = np.arccos(
        (
            THREE_POINT_RADIUS
            - (COURT_WIDTH_HALF - CORNER_THREE_DISTANCE_TO_SIDELINE)
        )
        / THREE_POINT_RADIUS
    )

    # Generate points for the center three-point arc segment
    arc_coords = []
    for angle in np.linspace(theta, -theta, 360):
        x = BASKET_X - THREE_POINT_RADIUS * np.cos(angle)
        y = THREE_POINT_RADIUS * np.sin(angle)
        if -FREE_THROW_LINE_WIDTH_HALF <= y <= FREE_THROW_LINE_WIDTH_HALF:
            arc_coords.append((x, y))
    return arc_coords

def compute_full_arc_coords():
    # Calculate the angle at which the three-point line intersects the sidelines for the full arc
    theta_sideline = np.arctan(
        (COURT_WIDTH_HALF - CORNER_THREE_DISTANCE_TO_SIDELINE)
        / THREE_POINT_CURVE_START
    )

    # Generate points for the full three-point arc
    return [
        (
            BASKET_X - THREE_POINT_RADIUS * np.cos(angle),
            THREE_POINT_RADIUS * np.sin(angle),
        )
        for angle in np.linspace(-theta_sideline, theta_sideline, 360)
    ]

def compute_regions():
    arc_coords = compute_arc_coords()
    full_arc_coords = compute_full_arc_coords()

    # Define the wing arc sections by filtering out the center part
    wing_arc_coords = [
        point
        for point in full_arc_coords
        if abs(point[1]) > FREE_THROW_LINE_WIDTH_HALF
    ]

    left_wing_arc = [point for point in wing_arc_coords if point[1] > 0] + [
        (0, COURT_WIDTH_HALF)
    ]
    right_wing_arc = [point for point in wing_arc_coords if point[1] < 0] + [
        (0, -COURT_WIDTH_HALF)
    ]

    left_wing_arc.append(left_wing_arc[0])  # Close the polygon
    right_wing_arc.append(right_wing_arc[0])  # Close the polygon

    restricted_area = (
        Point(BASKET_X, 0)
        .buffer(RESTRICTED_AREA_RADIUS)
        .difference(Point(BASKET_X, 0).buffer(RESTRICTED_AREA_RADIUS).boundary)
    )

    return {
        "CENTER_THREE": Polygon(
            [(0, FREE_THROW_LINE_WIDTH_HALF)]
            + arc_coords
            + [(0, -FREE_THROW_LINE_WIDTH_HALF)]
        ),
        "LEFT_WING_THREE": Polygon(left_wing_arc),
        "RIGHT_WING_THREE": Polygon(right_wing_arc),
        "RESTRICTED_AREA": restricted_area,
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
        "RESTRICTED_AREA": "#FF0000",  # Red
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
