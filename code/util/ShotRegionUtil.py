import numpy as np
from shapely.geometry import Polygon, Point, LineString, GeometryCollection
from shapely.ops import split

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
SIDELINE_INBOUNDS_TICK = 28
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

    # Add points to connect the semicircle to the out-of-bounds line precisely
    arc += [
        (
            45,
            -11,
        ),  # Lower left point at the baseline, matching expected end of mid-range
        (47, -11),  # Rightmost lower point at the baseline
        (47, 11),  # Rightmost upper point at the baseline
        (45, 11),  # Upper left point, back to start, completing the semicircle
    ]

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
    # Assuming three_point_arc includes the whole arc from one side to the other
    # Add points to close the polygon correctly around the three-point line
    extended_arc = three_point_arc + [
        (
            X_MAX - THREE_POINT_CURVE_START,
            COURT_WIDTH_HALF - CORNER_THREE_DISTANCE_TO_SIDELINE,
        ),
        (
            X_MAX,
            COURT_WIDTH_HALF - CORNER_THREE_DISTANCE_TO_SIDELINE,
        ),  # Right sideline top
        (
            X_MAX,
            -COURT_WIDTH_HALF + CORNER_THREE_DISTANCE_TO_SIDELINE,
        ),  # Right sideline bottom
        (
            X_MAX - THREE_POINT_CURVE_START,
            -COURT_WIDTH_HALF + CORNER_THREE_DISTANCE_TO_SIDELINE,
        ),
        three_point_arc[0],  # Close the polygon by connecting back to the start
    ]

    return Polygon(extended_arc)


def compute_mid_range_region(three_point_arc, close_range_arc):
    three_point_poly = compute_full_three_point_area(three_point_arc)
    close_range_poly = Polygon(close_range_arc)

    # Validate and correct geometries
    if not three_point_poly.is_valid:
        three_point_poly = three_point_poly.buffer(0)  # Correct minor geometric issues
    if not close_range_poly.is_valid:
        close_range_poly = close_range_poly.buffer(0)

    # Calculate the mid-range area
    mid_range_region = three_point_poly.difference(close_range_poly)

    # Handle possible GeometryCollection results
    if isinstance(mid_range_region, GeometryCollection):
        mid_range_region = [
            geom for geom in mid_range_region.geoms if isinstance(geom, Polygon)
        ]

    return mid_range_region


def compute_midrange_quadrants(mid_range_region):
    # Define a horizontal line at the free throw line distance (aligned with y=0 for demonstration)
    horizontal_line = LineString([(X_MIN, 0), (X_MAX, 0)])
    
    # Perform the split
    split_result = split(mid_range_region, horizontal_line)
    if len(split_result.geoms) != 2:
        raise ValueError("Expected exactly two geometries from the split but got {}".format(len(split_result.geoms)))
    
    lower_half = split_result.geoms[0]
    upper_half = split_result.geoms[1]

    # Define extended angled lines passing through the basket and the midpoints
    upper_angled_line = LineString([
        (BASKET_X, 0), 
        (X_MAX - SIDELINE_INBOUNDS_TICK, Y_MAX),
    ])
    lower_angled_line = LineString([
        (BASKET_X, 0), 
        (X_MAX - SIDELINE_INBOUNDS_TICK, Y_MIN),
    ])

    # Split each half by its angled line
    upper_split = split(upper_half, upper_angled_line)
    lower_split = split(lower_half, lower_angled_line)

    # Unpack the geometries correctly
    upper_left = upper_split.geoms[0]
    upper_right = upper_split.geoms[1]
    lower_left = lower_split.geoms[0]
    lower_right = lower_split.geoms[1]

    return upper_left, upper_right, lower_left, lower_right


def compute_regions():
    three_point_arc = compute_three_point_arc()
    center_wing_arc = compute_center_arc(three_point_arc)
    left_wing_arc, right_wing_arc = compute_wing_arcs(three_point_arc)
    close_range_arc = compute_close_range_arc()

    left_corner, right_corner = compute_corner_three_regions()
    mid_range_region = compute_mid_range_region(three_point_arc, close_range_arc)

    upper_left, upper_right, lower_left, lower_right = compute_midrange_quadrants(mid_range_region)
    return {
        "LEFT_BASELINE_MID": upper_left,
        "LEFT_ELBOW_MID": upper_right,
        "RIGHT_ELBOW_MID": lower_left,
        "RIGHT_BASELINE_MID": lower_right,
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
    }


class ShotRegionUtil:
    # Definition of colors and other properties remain the same.
    
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

    _regions = None  # Private class-level attribute to store the regions once computed.

    @classmethod
    def compute_regions(cls):
        if cls._regions is None:
            # Compute the regions only once.
            cls._regions = cls._compute_regions_internal()
        return cls._regions

    @classmethod
    def _compute_regions_internal(cls):
        # This internal method computes the regions.
        # This method should contain all the computation logic that was previously directly in compute_regions().
        # Return the dictionary of regions here.
        return compute_regions()

    @classmethod
    @property
    def regions(cls):
        return cls.compute_regions()
