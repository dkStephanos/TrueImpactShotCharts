import pandas as pd
class FeatureUtil:
    def is_position_in_paint(x, y):
        """
        Determine if a position (x, y) is in the paint of an NBA basketball court centered at (0, 0).
        The paint is 16 feet wide and extends from the baseline up to 19 feet towards the center.
        
        Args:
        x (float): The x-coordinate of the position (horizontal distance from the centerline in feet).
        y (float): The y-coordinate of the position (vertical distance from the centerline in feet).

        Returns:
        bool: True if the position is in the paint, otherwise False.
        """
        # Dimensions of the paint area
        PAINT_WIDTH_HALF = 8  # Half the width of the paint (16 feet total)
        PAINT_LENGTH = 19  # Length of the paint from the baseline towards the center

        # Adjust for the paint being vertically centered on the y-axis
        # The paint extends from the baseline to 19 feet towards the center
        in_vertical_bounds = abs(y) <= PAINT_LENGTH

        # The paint is horizontally centered around the basket (which is centered at x=0)
        in_horizontal_bounds = -PAINT_WIDTH_HALF <= x <= PAINT_WIDTH_HALF

        return in_vertical_bounds and in_horizontal_bounds
    
    def is_past_halfcourt(x, basket_x):
        """
        Determine if a position is past the half-court relative to a given basket location on the x-axis.

        Args:
        x (float): The x-coordinate of the position.
        basket_x (float): The x-coordinate of the basket, either 41.75 or -41.75.

        Returns:
        bool: True if the position is past the half-court towards the opposing basket, otherwise False.
        """
        return (basket_x > 0 and x < 0) or (basket_x < 0 and x > 0)
    
    def is_past_far_three_point_line(x, y, basket_x):
        """
        Determine if a position is past the far three-point line relative to a given basket location on the x-axis.

        Args:
        x (float): The x-coordinate of the position.
        y (float): The y-coordinate of the position.
        basket_x (float): The x-coordinate of the basket, either 41.75 or -41.75.

        Returns:
        bool: True if the position is past the far three-point line towards the opposing basket, otherwise False.
        """
        # Calculate the far 3-point line from the opposite basket
        far_three_point_line = -basket_x - (23.75 if abs(basket_x) > 23.75 else abs(basket_x))

        # Check if the x position has crossed this line (assuming half-court offense to defense transition)
        return (basket_x > 0 and x < far_three_point_line) or (basket_x < 0 and x > far_three_point_line)