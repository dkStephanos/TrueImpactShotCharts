import numpy as np
from shapely.geometry import Point, Polygon

# Constants for court dimensions
BASKET_X = 41.75
THREE_POINT_RADIUS = 23.75
THREE_POINT_SIDELINE_DISTANCE = 14
CORNER_THREE_DISTANCE = 22
RESTRICTED_AREA_RADIUS = 4
COURT_WIDTH_HALF = 25
FREE_THROW_LINE_DISTANCE = 19
ELBOW_DISTANCE_FROM_CENTER = 19

# Generate the three-point arc segments
ARC_START_ANGLE = -70  # Start angle for the three-point arc
ARC_END_ANGLE = 70  # End angle for the three-point arc
arc = [
    Point(
        BASKET_X + THREE_POINT_RADIUS * np.cos(np.radians(angle)),
        THREE_POINT_RADIUS * np.sin(np.radians(angle)),
    )
    for angle in np.linspace(ARC_START_ANGLE, ARC_END_ANGLE, num=100)
]
left_arc = [
    Point(p.x - 2 * BASKET_X, p.y) for p in arc
]  # Mirror the arc to the left side

basket_center = Point(BASKET_X, 0)
restricted_area_circle = basket_center.buffer(RESTRICTED_AREA_RADIUS)
class ShotRegionUtil:
    regions = {
        'RESTRICTED_AREA': Polygon(restricted_area_circle.exterior.coords),
        'LEFT_CORNER_THREE': Polygon([
            (-BASKET_X, -COURT_WIDTH_HALF),
            (-BASKET_X, CORNER_THREE_DISTANCE - COURT_WIDTH_HALF),
            tuple(left_arc[0].coords[0]),
            tuple(left_arc[-1].coords[0]),
            (-BASKET_X + THREE_POINT_SIDELINE_DISTANCE, CORNER_THREE_DISTANCE - COURT_WIDTH_HALF),
            (-BASKET_X + THREE_POINT_SIDELINE_DISTANCE, -COURT_WIDTH_HALF),
        ]),
        'RIGHT_CORNER_THREE': Polygon([
            (BASKET_X, -COURT_WIDTH_HALF),
            (BASKET_X, CORNER_THREE_DISTANCE - COURT_WIDTH_HALF),
            tuple(arc[0].coords[0]),
            tuple(arc[-1].coords[0]),
            (BASKET_X - THREE_POINT_SIDELINE_DISTANCE, CORNER_THREE_DISTANCE - COURT_WIDTH_HALF),
            (BASKET_X - THREE_POINT_SIDELINE_DISTANCE, -COURT_WIDTH_HALF),
        ]),
        'LEFT_WING_THREE': Polygon(
        [
            (BASKET_X - THREE_POINT_SIDELINE_DISTANCE, -FREE_THROW_LINE_DISTANCE),
            (BASKET_X - THREE_POINT_SIDELINE_DISTANCE, -COURT_WIDTH_HALF),
            tuple(left_arc[-1].coords[0]),
            tuple(left_arc[0].coords[0]),
        ]
    ),
    'RIGHT_WING_THREE': Polygon(
        [
            (BASKET_X - THREE_POINT_SIDELINE_DISTANCE, -FREE_THROW_LINE_DISTANCE),
            (BASKET_X - THREE_POINT_SIDELINE_DISTANCE, -COURT_WIDTH_HALF),
            tuple(arc[-1].coords[0]),
            tuple(arc[0].coords[0]),
        ]
    ),
    'LEFT_BASELINE_MID': Polygon(
        [
            (-BASKET_X, -COURT_WIDTH_HALF),
            (-BASKET_X, -FREE_THROW_LINE_DISTANCE),
            (-BASKET_X + THREE_POINT_SIDELINE_DISTANCE, -FREE_THROW_LINE_DISTANCE),
            (-BASKET_X + THREE_POINT_SIDELINE_DISTANCE, -COURT_WIDTH_HALF),
        ]
    ),
    'RIGHT_BASELINE_MID': Polygon(
        [
            (BASKET_X, -COURT_WIDTH_HALF),
            (BASKET_X, -FREE_THROW_LINE_DISTANCE),
            (BASKET_X - THREE_POINT_SIDELINE_DISTANCE, -FREE_THROW_LINE_DISTANCE),
            (BASKET_X - THREE_POINT_SIDELINE_DISTANCE, -COURT_WIDTH_HALF),
        ]
    ),
    'LEFT_ELBOW_MID': Polygon(
        [
            (-BASKET_X + THREE_POINT_SIDELINE_DISTANCE, -FREE_THROW_LINE_DISTANCE),
            (-BASKET_X + THREE_POINT_SIDELINE_DISTANCE, -ELBOW_DISTANCE_FROM_CENTER),
            (-BASKET_X, -ELBOW_DISTANCE_FROM_CENTER),
            (-BASKET_X, -FREE_THROW_LINE_DISTANCE),
        ]
    ),
    'RIGHT_ELBOW_MID': Polygon(
        [
            (BASKET_X - THREE_POINT_SIDELINE_DISTANCE, -FREE_THROW_LINE_DISTANCE),
            (BASKET_X - THREE_POINT_SIDELINE_DISTANCE, -ELBOW_DISTANCE_FROM_CENTER),
            (BASKET_X, -ELBOW_DISTANCE_FROM_CENTER),
            (BASKET_X, -FREE_THROW_LINE_DISTANCE),
        ]
    ),
    'CENTER_THREE': Polygon(arc),
    'BEYOND_HALFCOURT': Polygon(
        [
            (-BASKET_X, -COURT_WIDTH_HALF),
            (-BASKET_X, COURT_WIDTH_HALF),
            (BASKET_X, COURT_WIDTH_HALF),
            (BASKET_X, -COURT_WIDTH_HALF),
        ]
    )
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