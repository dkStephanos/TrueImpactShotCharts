import numpy as np
from shapely.geometry import Point, Polygon, LineString

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


class ShotRegionUtil:

    # Calculate theta for the three-point arc segment
    # Adjusted for half-court width minus distance to the sideline to form the arc start
    theta = np.arccos(
        (THREE_POINT_RADIUS - (COURT_WIDTH_HALF - CORNER_THREE_DISTANCE_TO_SIDELINE))
        / THREE_POINT_RADIUS
    )

    # Generate points for the arc segment
    arc_coords = []
    for angle in np.linspace(theta, -theta, 360):
        x = BASKET_X - THREE_POINT_RADIUS * np.cos(
            angle
        )  # Adjusted for the right basket
        y = THREE_POINT_RADIUS * np.sin(angle)
        if (
            -FREE_THROW_LINE_WIDTH_HALF <= y <= FREE_THROW_LINE_WIDTH_HALF
        ):  # Filter points to be within the -8 to 8 y-range
            arc_coords.append((x, y))

    # Angle at which the three-point line intersects the sidelines
    theta_sideline = np.arctan(
        (COURT_WIDTH_HALF - CORNER_THREE_DISTANCE_TO_SIDELINE) / THREE_POINT_CURVE_START
    )

    # Generate points for the full arc segment
    full_arc_coords = [
        (
            BASKET_X - THREE_POINT_RADIUS * np.cos(angle),
            THREE_POINT_RADIUS * np.sin(angle),
        )
        for angle in np.linspace(-theta_sideline, theta_sideline, 360)
    ]

    # Filter out the center part to get only the wing sections of the arc
    wing_arc_coords = [
        point for point in full_arc_coords if abs(point[1]) > FREE_THROW_LINE_WIDTH_HALF
    ]

    # Get the coordinates for the corners where the arc meets the sidelines
    corner_left = (BASKET_X - THREE_POINT_CURVE_START, COURT_WIDTH_HALF)
    corner_right = (BASKET_X - THREE_POINT_CURVE_START, -COURT_WIDTH_HALF)

    # Split the arc coordinates into left and right wings based on the y-coordinate
    left_wing_arc = [point for point in wing_arc_coords if point[1] > 0]
    right_wing_arc = [point for point in wing_arc_coords if point[1] < 0]

    # Add the backcourt corners to the list of points for the wings
    left_wing_arc += [(0, COURT_WIDTH_HALF)]
    right_wing_arc += [(0, -COURT_WIDTH_HALF)]

    # The last point on the wing arcs should be the basket point on the respective side
    left_wing_arc += [(BASKET_X, FREE_THROW_LINE_WIDTH_HALF)]
    right_wing_arc += [(BASKET_X, -FREE_THROW_LINE_WIDTH_HALF)]

    # Create the polygons for the left and right wing three sections
    LEFT_WING_THREE = Polygon(left_wing_arc)
    RIGHT_WING_THREE = Polygon(right_wing_arc)

    # Create the restricted area polygon
    restricted_area = (
        Point(BASKET_X, 0)
        .buffer(RESTRICTED_AREA_RADIUS)
        .difference(Point(BASKET_X, 0).buffer(RESTRICTED_AREA_RADIUS).boundary)
    )

    regions = {
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
        "RESTRICTED_AREA": restricted_area,
        "RIGHT_WING_THREE": RIGHT_WING_THREE,
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
        "LEFT_WING_THREE": LEFT_WING_THREE,
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
        "CENTER_THREE": Polygon(
            [
                (0, FREE_THROW_LINE_WIDTH_HALF),  # Top left corner (center court)
                *arc_coords,  # Arc from top to bottom
                (0, -FREE_THROW_LINE_WIDTH_HALF),  # Bottom left corner (center court)
            ]
        ),
    }

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

    @classmethod
    def get_region(cls, region_name):
        return cls.regions.get(region_name)

    @classmethod
    def list_regions(cls):
        return cls.regions.keys()
