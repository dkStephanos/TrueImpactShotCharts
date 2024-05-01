import numpy as np
from shapely.geometry import Polygon, Point, LineString, box, GeometryCollection

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


def compute_three_point_arc():
    # Calculate the angle where the three-point arc needs to intersect the sideline.
    # The hypotenuse in this case is directly the three-point radius.
    delta_x = (
        COURT_WIDTH_HALF - CORNER_THREE_DISTANCE_TO_SIDELINE
    )  # Horizontal distance from the sideline inside the arc

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
        (x, y)
        for (x, y) in full_arc_coords
        if -FREE_THROW_LINE_WIDTH_HALF <= y <= FREE_THROW_LINE_WIDTH_HALF
    ]
    return (
        [(0, Y_MIN + CORNER_THREE_DISTANCE_TO_SIDELINE)]
        + center_arc_coords
        + [(0, Y_MAX - CORNER_THREE_DISTANCE_TO_SIDELINE)]
    )


def compute_wing_arcs(full_arc_coords):
    # Define the wing arc sections by filtering out the center part
    wing_arc_coords = [
        point for point in full_arc_coords if abs(point[1]) > FREE_THROW_LINE_WIDTH_HALF
    ]

    # Extending and finalizing left wing arc
    left_wing_arc = (
        [
            (
                0,
                Y_MAX - CORNER_THREE_DISTANCE_TO_SIDELINE,
            )  # Starting at the top sideline intersection
        ]
        + [point for point in wing_arc_coords if point[1] > 0]
        + [
            (
                33,
                COURT_WIDTH_HALF,
            ),  # Additional point at the bottom of the corner three, at the court edge
            (0, COURT_WIDTH_HALF),  # Endpoint at the sideline at half-court width
        ]
    )
    left_wing_arc.append(
        (0, Y_MAX - CORNER_THREE_DISTANCE_TO_SIDELINE)
    )  # Close the polygon by returning to the starting point

    # Extending and finalizing right wing arc
    right_wing_arc = (
        [
            (
                0,
                Y_MIN + CORNER_THREE_DISTANCE_TO_SIDELINE,
            )  # Start at the lower sideline intersection
        ]
        + list(reversed([point for point in wing_arc_coords if point[1] < 0]))
        + [
            (
                33,
                -COURT_WIDTH_HALF,
            ),  # Additional point at the bottom of the corner three, at the court edge
            (
                0,
                -COURT_WIDTH_HALF,
            ),  # Existing endpoint at the sideline at half-court width (negative)
        ]
    )
    right_wing_arc.append(
        (0, Y_MIN + CORNER_THREE_DISTANCE_TO_SIDELINE)
    )  # Close the polygon by returning to the starting point

    return left_wing_arc, right_wing_arc


def compute_close_range_arc():
    # Define the center and radius
    center_point = Point(45, 0)
    radius = 11  # Adjusted radius to match the desired coverage

    # Generate points for the left half-circle
    arc = [
        (
            center_point.x + radius * np.cos(angle),
            center_point.y + radius * np.sin(angle),
        )
        for angle in np.linspace(
            np.pi / 2, 3 * np.pi / 2, 180
        )  # Generate left half-circle from 90 to 270 degrees
    ]

    # Add points to connect the semicircle to the out-of-bounds line
    arc += [(45, -11), (47, -11), (47, 11)]

    # Complete the arc by connecting back to the start
    arc.append(
        (45, 11)
    )  # Closing the shape by connecting to the start of the semicircle

    return arc


def compute_corner_three_regions():
    left_corner = [
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

    right_corner = [
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

    return left_corner, right_corner

def compute_full_three_point_area(three_point_arc):
    # Assuming the three_point_arc provided is just the curved part of the arc
    # Extend this arc to include the lines down to the baseline
    # Points need to connect with the court corners at the baseline
    extended_arc = three_point_arc + [
        (X_MAX, -COURT_WIDTH_HALF + CORNER_THREE_DISTANCE_TO_SIDELINE),  # Right corner
        (X_MAX, -COURT_WIDTH_HALF),  # Right baseline
        (X_MIN, -COURT_WIDTH_HALF),  # Left baseline
        (X_MIN, COURT_WIDTH_HALF),  # Left baseline top
        (X_MAX, COURT_WIDTH_HALF),  # Right baseline top
        (X_MAX, COURT_WIDTH_HALF - CORNER_THREE_DISTANCE_TO_SIDELINE)  # Left corner
    ] + [three_point_arc[0]]  # Close the polygon by connecting back to the start

    # Create the polygon
    three_point_polygon = Polygon(extended_arc)

    return three_point_polygon


def compute_mid_range_region(three_point_arc, close_range_arc):
    # Ensure arcs are closed and valid as polygons
    close_range_line = LineString(close_range_arc)

    # Convert lines to polygons and check validity
    three_point_poly = compute_full_three_point_area(three_point_arc)
    close_range_poly = Polygon(close_range_line)
    if not three_point_poly.is_valid:
        three_point_poly = three_point_poly.buffer(0)
    if not close_range_poly.is_valid:
        close_range_poly = close_range_poly.buffer(0)

    # Compute the basic mid-range area
    mid_range_region = three_point_poly.difference(close_range_poly)

    # Handle GeometryCollection
    if isinstance(mid_range_region, GeometryCollection):
        # Filter only polygons from the collection
        mid_range_region = [geom for geom in mid_range_region.geoms if isinstance(geom, Polygon)]

    return mid_range_region


def compute_regions():
    three_point_arc = compute_three_point_arc()
    center_wing_arc = compute_center_arc(three_point_arc)
    left_wing_arc, right_wing_arc = compute_wing_arcs(three_point_arc)
    close_range_arc = compute_close_range_arc()

    left_corner, right_corner = compute_corner_three_regions()
    mid_range_region = compute_mid_range_region(three_point_arc, close_range_arc)

    return {
        "midrange": mid_range_region,
        "CENTER_THREE": Polygon(center_wing_arc),
        "LEFT_WING_THREE": Polygon(left_wing_arc),
        "RIGHT_WING_THREE": Polygon(right_wing_arc),
        "CLOSE_RANGE": Polygon(close_range_arc),
        "RIGHT_CORNER_THREE": Polygon(right_corner),
        "LEFT_CORNER_THREE": Polygon(left_corner),
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
