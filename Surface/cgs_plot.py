"""Display-only reconstruction of the two-ellipse curve from Max telemetry.

Max remains authoritative for feature extraction and sound. This module only
turns the selected feature group's values into points for the optional UI plot.
The equations follow the Model A renderer in ``2Ellipse_plotter.py``.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Sequence

from .transport import FeatureGroup


ALLOWED_RATIOS = (1.0, 1.5, 2.0, 3.0, 4.0)


def _cart_to_tau_s(values: Sequence[float]) -> tuple[float, float]:
    """Invert Max's six-value Cartesian shape representation for rendering."""
    if len(values) != 6:
        raise ValueError("ellipse shape needs six Cartesian values")
    s_plus, s_minus, t_h, t_v, t_u, t_d = values
    shape = s_plus - s_minus
    q_hv = t_h - t_v
    q_ud = t_u - t_d
    # tau has no geometric effect for a perfect circle, where atan2(0, 0)
    # would otherwise make it undefined. Use the same neutral angle as Gen.
    tau = 0.0 if abs(q_hv) + abs(q_ud) < 1e-12 else 0.5 * math.atan2(q_ud, q_hv)
    return tau, shape


def curve_points(group: FeatureGroup, sample_count: int = 1200) -> tuple[tuple[float, float], ...]:
    """Return one closed Model A curve from a Max-derived feature group.

    Points are in the renderer's world coordinates. The UI maps them into its
    canvas with equal pixel scale. Empty output means the telemetry is not yet
    sufficient for a meaningful curve.
    """
    if sample_count < 32:
        raise ValueError("sample_count must be at least 32")

    scalars = (group.wr, group.energy, group.w0, group.asum, group.abal, group.phi)
    shapes = (*group.low, *group.high)
    if len(group.low) != 6 or len(group.high) != 6:
        return ()
    if not all(math.isfinite(value) for value in (*scalars, *shapes)):
        return ()
    if group.wr <= 0.0 or group.w0 <= 0.0 or group.asum <= 1e-12:
        return ()
    if not 0.0 <= group.abal <= 1.0:
        return ()

    ratio = group.wr
    canonical = Fraction(ratio).limit_denominator(2)
    if canonical.denominator not in (1, 2) or not any(abs(ratio - allowed) < 1e-3 for allowed in ALLOWED_RATIOS):
        return ()

    tau1, s1 = _cart_to_tau_s(group.low)
    tau2, s2 = _cart_to_tau_s(group.high)

    # Model A parameter mapping used by the plotter.
    omega0 = group.w0 / ratio  # Max's W0 is the higher frequency.
    a_sum = group.asum
    rho2 = group.abal
    a1 = (1.0 - rho2) * a_sum
    a2 = rho2 * a_sum
    ar1, al1 = (a1 / 2.0) * (1.0 - s1), (a1 / 2.0) * (1.0 + s1)
    ar2, al2 = (a2 / 2.0) * (1.0 - s2), (a2 / 2.0) * (1.0 + s2)

    # A rational frequency ratio closes after denominator M periods of omega0.
    period = 2.0 * math.pi * canonical.denominator / omega0
    points: list[tuple[float, float]] = []
    for index in range(sample_count):
        t = period * index / (sample_count - 1)
        theta1r = omega0 * t + tau1
        theta1l = omega0 * t - tau1
        theta2r = ratio * omega0 * t + group.phi + tau2
        theta2l = ratio * omega0 * t + group.phi - tau2

        x = ar1 * math.cos(theta1r) + al1 * math.cos(theta1l)
        x += ar2 * math.cos(theta2r) + al2 * math.cos(theta2l)
        y = -ar1 * math.sin(theta1r) + al1 * math.sin(theta1l)
        y += -ar2 * math.sin(theta2r) + al2 * math.sin(theta2l)
        points.append((x, y))
    return tuple(points)
