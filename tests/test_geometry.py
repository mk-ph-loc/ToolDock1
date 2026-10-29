from tooldock.core.geometry import clamp_rect, dock_rect, float_size, thickness_for, with_thickness

S1 = (0, 0, 1920, 1040)
S2 = (1920, 0, 1600, 860)  # δεύτερη οθόνη δεξιά


def test_dock_right_stays_on_its_screen():
    assert dock_rect(S1, "right", 400) == (1520, 0, 400, 1040)
    x, y, w, h = dock_rect(S2, "right", 400)
    assert (x, w) == (3120, 400) and x + w == 3520


def test_dock_left_on_second_screen_starts_at_its_edge():
    assert dock_rect(S2, "left", 300)[0] == 1920


def test_margins():
    assert dock_rect(S1, "right", 500, 100, 100) == (1420, 100, 500, 840)
    assert dock_rect(S1, "top", 200, 50, 70) == (50, 0, 1800, 200)
    assert dock_rect(S1, "bottom", 200) == (0, 840, 1920, 200)


def test_min_thickness_and_bad_side():
    assert dock_rect(S1, "left", 10)[2] == 60
    try:
        dock_rect(S1, "x", 100)
        assert False
    except ValueError:
        pass


def test_clamp():
    assert clamp_rect((1800, 900, 400, 300), S1) == (1520, 740, 400, 300)
    assert clamp_rect((-50, -50, 5000, 5000), S1) == (0, 0, 1920, 1040)
    assert clamp_rect((100, 100, 300, 200), S1) == (100, 100, 300, 200)


def test_thickness_modes_and_legacy():
    assert thickness_for(500, "full") == 500
    assert thickness_for({"compact": 300, "full": 450}, "full") == 450
    assert thickness_for({"compact": 300}, "full") == 300
    assert thickness_for(None, "full") == 360
    assert with_thickness(500, "full", 600) == {"compact": 500, "full": 600}
    assert with_thickness({"compact": 1}, "compact", 10)["compact"] == 60


def test_float_size():
    f = {"w": 380, "h": 320, "sizes": {"full": {"w": 600, "h": 500}}}
    assert float_size(f, "full") == (600, 500)
    assert float_size(f, "compact") == (380, 320)
    assert float_size({"w": 380, "h": 320}, "full") == (380, 320)
