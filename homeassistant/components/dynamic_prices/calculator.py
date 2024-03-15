"""Helper class to calculate intersections."""


class Calculator:
    """Helper class to calculate intersections."""

    def find_intersection_points(
        self, curve_points: list[float], line_y: float
    ) -> list[tuple[float, str]]:
        """Find Intercections between curve and line."""
        intersections = []
        for i in range(len(curve_points) - 1):
            current: float = curve_points[i]
            next_item: float = curve_points[i + 1]
            if (current - line_y) * (next_item - line_y) <= 0:
                interpolation_factor = (line_y - current) / (next_item - current)
                intersection_x = i + interpolation_factor
                area = str("above" if current < line_y else "below")
                t: tuple[float, str] = (intersection_x, area)
                intersections.append(t)
        return intersections
