import math
import unittest

from Surface.cgs_plot import curve_points, plotter_parameters
from Surface.transport import (
    FeatureAssembler,
    FeatureGroup,
    decode_osc,
    encode_osc,
    parse_telemetry,
)


def tau_s_to_cart(tau: float, shape: float) -> tuple[float, ...]:
    """Build the six Max Cartesian values from a known ellipse shape."""
    q_hv = math.cos(2.0 * tau)
    q_ud = math.sin(2.0 * tau)
    remainder = 1.0 - abs(shape)
    normalizer = abs(q_hv) + abs(q_ud)
    return (
        max(0.0, shape),
        max(0.0, -shape),
        remainder * max(0.0, q_hv / normalizer),
        remainder * max(0.0, -q_hv / normalizer),
        remainder * max(0.0, q_ud / normalizer),
        remainder * max(0.0, -q_ud / normalizer),
    )


def max_feature_values(
    energy: float,
    wr: float,
    w0: float,
    asum: float,
    abal: float,
    phi: float,
    low: tuple[float, ...] = (0.0,) * 6,
    high: tuple[float, ...] = (0.0,) * 6,
) -> tuple[float, ...]:
    return (energy, wr, w0, asum, abal, phi, *low, *high)


class FeatureAssemblyTests(unittest.TestCase):
    def test_feature_message_uses_scalar_channel_then_value(self) -> None:
        address, args = decode_osc(encode_osc("/circle/feature", 90, 0.125))
        self.assertEqual(address, "/circle/feature")
        self.assertEqual(args[0], 90)
        self.assertIs(type(args[0]), int)
        self.assertAlmostEqual(args[1], 0.125)
        self.assertIs(type(args[1]), float)

    def test_shuffled_channels_preserve_max_field_order_and_select_energy(self) -> None:
        groups = [
            max_feature_values(float(index), wr, 4.0, 2.0, 0.5, 0.25)
            for index, wr in enumerate((1.0, 1.5, 2.0, 3.0, 4.0), start=1)
        ]
        values = tuple(value for group in groups for value in group)
        assembler = FeatureAssembler()
        result = None
        for channel in range(90, 0, -1):
            result = assembler.add(channel, values[channel - 1])

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(len(result.groups), 5)
        self.assertEqual(result.groups[1].energy, 2.0)
        self.assertEqual(result.groups[1].wr, 1.5)
        self.assertEqual(result.active_group, result.groups[4])
        self.assertEqual(result.active_group.energy, 5.0)
        self.assertEqual(result.active_group.wr, 4.0)

    def test_repeated_channel_discards_partial_frame(self) -> None:
        values = max_feature_values(1.0, 1.5, 3.0, 2.0, 0.5, 0.25) * 5
        assembler = FeatureAssembler()
        for channel in range(1, 21):
            self.assertIsNone(assembler.add(channel, values[channel - 1]))

        self.assertIsNone(assembler.add(1, values[0]))
        result = None
        for channel in range(2, 91):
            result = assembler.add(channel, values[channel - 1])
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.groups[0].wr, 1.5)
        self.assertEqual(result.groups[0].energy, 1.0)

    def test_flat_telemetry_parser_maps_energy_before_ratio(self) -> None:
        values = max_feature_values(0.75, 1.5, 3.0, 2.0, 0.4, -0.5)
        telemetry = parse_telemetry("/circle/features", (1, *values))
        self.assertEqual(telemetry.groups[0].energy, 0.75)
        self.assertEqual(telemetry.groups[0].wr, 1.5)


class CurveReconstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tau1, self.s1 = 0.37, 0.25
        self.tau2, self.s2 = -0.62, -0.4
        self.group = FeatureGroup(
            wr=1.5,
            energy=0.9,
            w0=3.0,
            asum=2.0,
            abal=0.4,
            phi=0.6,
            low=tau_s_to_cart(self.tau1, self.s1),
            high=tau_s_to_cart(self.tau2, self.s2),
        )

    def test_plotter_parameter_mapping_matches_spec(self) -> None:
        params = plotter_parameters(self.group)
        self.assertIsNotNone(params)
        assert params is not None
        self.assertEqual((params.numerator, params.denominator), (3, 2))
        self.assertAlmostEqual(params.omega0, 2.0)
        self.assertAlmostEqual(params.a0, 1.0)
        self.assertAlmostEqual(params.ar, -0.2)
        self.assertAlmostEqual(params.s1, self.s1)
        self.assertAlmostEqual(params.tau1, self.tau1)
        self.assertAlmostEqual(params.s2, self.s2)
        self.assertAlmostEqual(params.tau2, self.tau2)
        self.assertAlmostEqual(params.phi, 0.6)

    def test_curve_matches_model_a_equations(self) -> None:
        points = curve_points(self.group, sample_count=257)
        self.assertEqual(len(points), 257)
        self.assertAlmostEqual(points[0][0], points[-1][0], places=12)
        self.assertAlmostEqual(points[0][1], points[-1][1], places=12)

        # Independent Model A calculation, using the source plotter's amplitude,
        # phase and frequency formulas rather than cgs_plot's implementation.
        ratio = 1.5
        omega0 = 2.0
        phi = 0.6
        a1, a2 = (1.0 - 0.4) * 2.0, 0.4 * 2.0
        ar1, al1 = (a1 / 2.0) * (1.0 - self.s1), (a1 / 2.0) * (1.0 + self.s1)
        ar2, al2 = (a2 / 2.0) * (1.0 - self.s2), (a2 / 2.0) * (1.0 + self.s2)
        period = 2.0 * math.pi * 2.0 / omega0
        for index in (0, 17, 93, 256):
            t = period * index / 256
            theta1r, theta1l = omega0 * t + self.tau1, omega0 * t - self.tau1
            theta2r = ratio * omega0 * t + phi + self.tau2
            theta2l = ratio * omega0 * t + phi - self.tau2
            expected_x = ar1 * math.cos(theta1r) + al1 * math.cos(theta1l)
            expected_x += ar2 * math.cos(theta2r) + al2 * math.cos(theta2l)
            expected_y = -ar1 * math.sin(theta1r) + al1 * math.sin(theta1l)
            expected_y += -ar2 * math.sin(theta2r) + al2 * math.sin(theta2l)
            self.assertAlmostEqual(points[index][0], expected_x, places=12)
            self.assertAlmostEqual(points[index][1], expected_y, places=12)


if __name__ == "__main__":
    unittest.main()
