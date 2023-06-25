from m23.norm import get_cluster_angle_to_normalize_to


def test_choose_intranight_ref_cluster_angle_1():
    candidates = [(19.1, 1), (19.2, 2), (20.1, 3), (22.5, 7), (22.8, 9), (22.9, 10)]
    expected = 23
    result = get_cluster_angle_to_normalize_to(candidates)
    assert expected == result


def test_choose_intranight_ref_cluster_angle_2():
    candidates = [
        (19.1, 1),
        (19.2, 2),
        (22.3, 8),
        (19.5, 9),
    ]
    expected = 19
    result = get_cluster_angle_to_normalize_to(candidates)
    assert expected == result


def test_choose_intranight_ref_cluster_angle_3():
    candidates = [
        (19.1, 1),
        (19.2, 2),
        (22.3, 4),
        (22.5, 6),
    ]
    expected = 19
    result = get_cluster_angle_to_normalize_to(candidates)
    assert expected == result


def test_choose_intranight_ref_cluster_angle_4():
    candidates = [
        (19.1, 1),
        (19.2, 2),
        (22.3, 4),
        (22.4, 6),
    ]
    expected = 22
    result = get_cluster_angle_to_normalize_to(candidates)
    assert expected == result


def test_choose_intranight_ref_cluster_angle_5():
    candidates = [
        (19.1, 1),
        (19.2, 2),
        (22.3, 4),
        (22.4, 5),
        (23, 8),
    ]
    expected = 22
    result = get_cluster_angle_to_normalize_to(candidates)
    assert expected == result
