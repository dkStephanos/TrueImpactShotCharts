import numpy as np
from shapely.geometry import Point, Polygon

# Constants for court dimensions
BASKET_X = 41.75
THREE_POINT_RADIUS = 23.75
THREE_POINT_SIDELINE_DISTANCE = 14
CORNER_THREE_DISTANCE = 22
RESTRICTED_AREA_RADIUS = 4
COURT_LENGTH = 94
COURT_WIDTH_HALF = 25
FREE_THROW_LINE_DISTANCE = 19
ELBOW_DISTANCE_FROM_CENTER = 19
X_MIN = 0
X_MAX = 47
Y_MIN = -25
Y_MAX = 25

# Generate the three-point arc segments
arc = [
    Point(
        BASKET_X + THREE_POINT_RADIUS * np.cos(np.radians(angle)),
        THREE_POINT_RADIUS * np.sin(np.radians(angle))
    )
    for angle in np.linspace(-70, 70, num=100)
]

# Generate the three-point arc for the right half-court
right_arc = [p for p in arc if p.x >= BASKET_X]

# Create the restricted area polygon
restricted_area = Point(BASKET_X, 0).buffer(RESTRICTED_AREA_RADIUS).difference(Point(BASKET_X, 0).buffer(RESTRICTED_AREA_RADIUS).boundary)

class ShotRegionUtil:
    regions = {
        'RESTRICTED_AREA': restricted_area,
        'RIGHT_CORNER_THREE': Polygon([
            (BASKET_X, Y_MIN),
            (X_MAX, Y_MIN),
            (X_MAX, -THREE_POINT_SIDELINE_DISTANCE),
            tuple(right_arc[0].coords[0]),
        ]),
        'RIGHT_WING_THREE': Polygon([
            tuple(right_arc[0].coords[0]),
            tuple(right_arc[-1].coords[0]),
            (BASKET_X, -THREE_POINT_SIDELINE_DISTANCE),
        ]),
        'RIGHT_BASELINE_MID': Polygon([
            (BASKET_X, -THREE_POINT_SIDELINE_DISTANCE),
            (BASKET_X, Y_MIN),
            (BASKET_X - FREE_THROW_LINE_DISTANCE, Y_MIN),
            (BASKET_X - FREE_THROW_LINE_DISTANCE, -THREE_POINT_SIDELINE_DISTANCE),
        ]),
        'RIGHT_ELBOW_MID': Polygon([
            (BASKET_X, -THREE_POINT_SIDELINE_DISTANCE),
            (BASKET_X - FREE_THROW_LINE_DISTANCE, -THREE_POINT_SIDELINE_DISTANCE),
            (BASKET_X - FREE_THROW_LINE_DISTANCE, -ELBOW_DISTANCE_FROM_CENTER),
            (BASKET_X, -ELBOW_DISTANCE_FROM_CENTER),
        ]),
        'LEFT_CORNER_THREE': Polygon([
            (BASKET_X, THREE_POINT_SIDELINE_DISTANCE),
            (X_MAX, THREE_POINT_SIDELINE_DISTANCE),
            (X_MAX, Y_MAX),
            (BASKET_X, Y_MAX),
        ]),
        'LEFT_WING_THREE': Polygon([
            tuple(right_arc[-1].coords[0]),
            (BASKET_X, THREE_POINT_SIDELINE_DISTANCE),
            (BASKET_X, Y_MAX),
        ]),
        'LEFT_BASELINE_MID': Polygon([
            (BASKET_X, Y_MAX),
            (BASKET_X - FREE_THROW_LINE_DISTANCE, Y_MAX),
            (BASKET_X - FREE_THROW_LINE_DISTANCE, THREE_POINT_SIDELINE_DISTANCE),
            (BASKET_X, THREE_POINT_SIDELINE_DISTANCE),
        ]),
        'LEFT_ELBOW_MID': Polygon([
            (BASKET_X, ELBOW_DISTANCE_FROM_CENTER),
            (BASKET_X - FREE_THROW_LINE_DISTANCE, ELBOW_DISTANCE_FROM_CENTER),
            (BASKET_X - FREE_THROW_LINE_DISTANCE, THREE_POINT_SIDELINE_DISTANCE),
            (BASKET_X, THREE_POINT_SIDELINE_DISTANCE),
        ]),
        'CENTER_THREE': Polygon([
            tuple(right_arc[-1].coords[0]),
            (BASKET_X - FREE_THROW_LINE_DISTANCE, THREE_POINT_SIDELINE_DISTANCE),
            (BASKET_X - FREE_THROW_LINE_DISTANCE, -THREE_POINT_SIDELINE_DISTANCE),
            tuple(right_arc[0].coords[0]),
        ]),
        'BEYOND_HALFCOURT': Polygon([
            (X_MIN, Y_MIN),
            (X_MIN, Y_MAX),
            (BASKET_X, Y_MAX),
            (BASKET_X, Y_MIN),
        ]),
    }

    region_colors = {
        'RESTRICTED_AREA': '#FF0000',  # Red
        'LEFT_CORNER_THREE': '#00FF00',  # Green
        'RIGHT_CORNER_THREE': '#0000FF',  # Blue
        'LEFT_WING_THREE': '#FFFF00',  # Yellow
        'RIGHT_WING_THREE': '#FF00FF',  # Magenta
        'LEFT_BASELINE_MID': '#00FFFF',  # Cyan
        'RIGHT_BASELINE_MID': '#FFA500',  # Orange
        'LEFT_ELBOW_MID': '#800080',  # Purple
        'RIGHT_ELBOW_MID': '#808080',  # Gray
        'CENTER_THREE': '#000000',  # Black
        'BEYOND_HALFCOURT': '#8B4513',  # SaddleBrown
    }


    @classmethod
    def get_region(cls, region_name):
        return cls.regions.get(region_name)

    @classmethod
    def list_regions(cls):
        return cls.regions.keys()