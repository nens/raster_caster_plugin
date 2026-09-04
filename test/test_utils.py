import numpy as np
from numpy.testing import assert_allclose

from algorithms.utils import periodic_linear_interp


class TestPeriodicLinearInterp:
    """Tests for periodic_linear_interp."""

    def setup_method(self) -> None:
        self.xp = [90, 180, 270]
        self.fp = [1.0, 3.0, 2.0]
        self.period = 360

    def test_at_knot_points(self) -> None:
        result = periodic_linear_interp(
            np.array([90, 180, 270]), self.xp, self.fp, self.period
        )
        assert_allclose(result, [1.0, 3.0, 2.0])

    def test_between_knots(self) -> None:
        result = periodic_linear_interp(np.array([135]), self.xp, self.fp, self.period)
        assert_allclose(result, [2.0])

    def test_wrap_around_after_last_knot(self) -> None:
        result = periodic_linear_interp(np.array([360]), self.xp, self.fp, self.period)
        assert_allclose(result, [1.5])

    def test_wrap_around_before_first_knot(self) -> None:
        # x=45 is before xp[0]=90, shifted to 405
        # interp between (270, 2.0) and (450, 1.0): at 405 -> 2.0 - 135/180 = 1.25
        result = periodic_linear_interp(np.array([45]), self.xp, self.fp, self.period)
        assert_allclose(result, [1.25])

    def test_x_beyond_period(self) -> None:
        # x=450 should behave same as x=90
        result = periodic_linear_interp(np.array([450]), self.xp, self.fp, self.period)
        assert_allclose(result, [1.0])

    def test_negative_x(self) -> None:
        # x=-270 % 360 = 90
        result = periodic_linear_interp(np.array([-270]), self.xp, self.fp, self.period)
        assert_allclose(result, [1.0])

    def test_scalar_input(self) -> None:
        result = periodic_linear_interp(135, self.xp, self.fp, self.period)
        assert_allclose(result, 2.0)

    def test_array_input(self) -> None:
        x = np.array([90, 135, 180, 270, 360])
        result = periodic_linear_interp(x, self.xp, self.fp, self.period)
        assert_allclose(result, [1.0, 2.0, 3.0, 2.0, 1.5])

    def test_two_knot_points(self) -> None:
        xp = [0, 180]
        fp = [0.0, 10.0]
        result = periodic_linear_interp(np.array([90, 270]), xp, fp, 360)
        assert_allclose(result, [5.0, 5.0])

    def test_single_knot_point(self) -> None:
        # With one knot, the value is constant everywhere
        result = periodic_linear_interp(np.array([0, 90, 180]), [0], [5.0], 360)
        assert_allclose(result, [5.0, 5.0, 5.0])
