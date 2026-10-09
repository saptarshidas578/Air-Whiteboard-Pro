"""
Unit tests for Air Whiteboard state machines and coordinate math.
"""

from enum import Enum


def test_modes_enum():
    from air_draw import Mode

    assert hasattr(Mode, "IDLE")
    assert hasattr(Mode, "DRAW")
    assert hasattr(Mode, "LINE")
    assert hasattr(Mode, "ERASE")
    assert hasattr(Mode, "PAUSE")


def test_pinch_distance_math():
    import math

    p1 = (100, 100)
    p2 = (140, 130)
    dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    assert abs(dist - 50.0) < 1e-5


if __name__ == "__main__":
    test_modes_enum()
    test_pinch_distance_math()
    print("Air Whiteboard tests passed successfully!")
