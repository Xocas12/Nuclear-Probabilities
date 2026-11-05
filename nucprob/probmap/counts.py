"""How the report and the viewer print a simulated count of warheads or cells."""


def count(x: float) -> str:
    """Whole below 100, to the nearest ten from 100. The theatre shares behind these counts have no
    source (configs/scenarios.yaml), so a third digit would be precision they do not have."""
    x = float(x)
    return f"{x:.0f}" if abs(x) < 100 else f"{round(x, -1):.0f}"
