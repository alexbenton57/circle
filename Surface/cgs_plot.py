"""Display-only reconstruction of the two-ellipse curve from Max telemetry.

Max remains authoritative for feature extraction and sound. This module only
turns the selected feature group's values into points for the optional UI plot.
The equations follow the Model A renderer in ``2Ellipse_plotter.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from .transport import FeatureGroup


ALLOWED_RATIOS = (1.0, 1.5, 2.0, 3.0, 4.0)


@dataclass(frozen=True)
class PlotterParameters:
    """Model A parameters mapped from one Max feature group."""

    numerator: int
    denominator: int
    omega0: float
    a0: float
    ar: float
    s1: float
    tau1: float
    s2: float
    tau2: float
    phi: float
    energy: float


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


def plotter_parameters(group: FeatureGroup) -> PlotterParameters | None:
    """Map a valid Max feature group to the controls used by Model A."""
    scalars = (group.wr, group.energy, group.w0, group.asum, group.abal, group.phi)
    if len(group.low) != 6 or len(group.high) != 6:
        return None
    if not all(math.isfinite(value) for value in (*scalars, *group.low, *group.high)):
        return None
    if group.wr <= 0.0 or group.w0 <= 0.0 or not 0.0 <= group.abal <= 1.0:
        return None

    ratio = group.wr
    canonical = Fraction(ratio).limit_denominator(2)
    if canonical.denominator not in (1, 2) or not any(
        abs(ratio - allowed) < 1e-3 for allowed in ALLOWED_RATIOS
    ):
        return None

    tau1, s1 = _cart_to_tau_s(group.low)
    tau2, s2 = _cart_to_tau_s(group.high)
    return PlotterParameters(
        numerator=canonical.numerator,
        denominator=canonical.denominator,
        omega0=group.w0 / ratio,
        a0=group.asum / 2.0,
        ar=2.0 * group.abal - 1.0,
        s1=s1,
        tau1=tau1,
        s2=s2,
        tau2=tau2,
        # Keep the readout within the plotter's [-pi, pi] slider convention.
        phi=math.atan2(math.sin(group.phi), math.cos(group.phi)),
        energy=group.energy,
    )


def canvas_curve_points(
    points: Sequence[tuple[float, float]], width: int, height: int
) -> tuple[tuple[float, float], ...]:
    """Map centered Model A points to pixels using the Surface input scale.

    Surface sends X in canvas-width units and aspect-compensates Y by width as
    well. The plotter's vertical axis is opposite the Surface screen trace, so
    invert Y while mapping. Do not fit each curve to the viewport independently.
    """
    if not points or width <= 0 or height <= 0:
        return ()
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    center_x = (min(xs) + max(xs)) / 2.0
    center_y = (min(ys) + max(ys)) / 2.0
    return tuple(
        (
            width * 0.5 + (x - center_x) * width,
            height * 0.5 + (y - center_y) * width,
        )
        for x, y in points
    )


def curve_points(group: FeatureGroup, sample_count: int = 1200) -> tuple[tuple[float, float], ...]:
    """Return one closed Model A curve from a Max-derived feature group.

    Points are in the renderer's world coordinates. Empty output means the
    telemetry is not yet sufficient for a meaningful curve.
    """
    if sample_count < 32:
        raise ValueError("sample_count must be at least 32")

    params = plotter_parameters(group)
    if params is None or group.asum <= 1e-12:
        return ()

    # Model A parameter mapping used by the plotter.
    ratio = group.wr
    omega0 = params.omega0  # Max's W0 is the higher frequency.
    a_sum = group.asum
    rho2 = group.abal
    a1 = (1.0 - rho2) * a_sum
    a2 = rho2 * a_sum
    ar1, al1 = (a1 / 2.0) * (1.0 - params.s1), (a1 / 2.0) * (1.0 + params.s1)
    ar2, al2 = (a2 / 2.0) * (1.0 - params.s2), (a2 / 2.0) * (1.0 + params.s2)

    # A rational frequency ratio closes after denominator M periods of omega0.
    period = 2.0 * math.pi * params.denominator / omega0
    points: list[tuple[float, float]] = []
    for index in range(sample_count):
        t = period * index / (sample_count - 1)
        theta1r = omega0 * t + params.tau1
        theta1l = omega0 * t - params.tau1
        theta2r = ratio * omega0 * t + group.phi + params.tau2
        theta2l = ratio * omega0 * t + group.phi - params.tau2

        x = ar1 * math.cos(theta1r) + al1 * math.cos(theta1l)
        x += ar2 * math.cos(theta2r) + al2 * math.cos(theta2l)
        y = -ar1 * math.sin(theta1r) + al1 * math.sin(theta1l)
        y += -ar2 * math.sin(theta2r) + al2 * math.sin(theta2l)
        points.append((x, y))
    return tuple(points)
