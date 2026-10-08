import json

from nucprob.viz.map import east, outline


def test_east_moves_chukotka_past_180():
    assert east(-170.0) == 190.0
    assert east(37.6) == 37.6


def test_outline_shifts_only_rings_wholly_west(tmp_path):
    chukotka = [[-179, 65], [-170, 65], [-170, 68], [-179, 68], [-179, 65]]
    america = [[-160, 60], [-60, 60], [-60, 70], [-160, 70], [-160, 60]]
    europe = [[30, 50], [40, 50], [40, 60], [30, 60], [30, 50]]
    geo = {
        "features": [
            {"geometry": {"type": "Polygon", "coordinates": [r]}}
            for r in (chukotka, america, europe)
        ]
    }
    path = tmp_path / "land.geojson"
    path.write_text(json.dumps(geo))
    rings = outline(path)
    xs = sorted(min(p[0] for p in r) for r in rings)
    assert xs == [30, 181]  # Europe kept, Chukotka moved east, America outside the map


def test_card_values_undo_the_logs():
    from nucprob.viz.map import shown

    assert shown(1.0, "count") == 9
    assert shown(2.0, "km") == 99.0
    assert shown(1, "flag") is True
    assert shown(float("nan"), "km") is None
