import numpy as np
from numpy.typing import ArrayLike, NDArray


def periodic_linear_interp(
    x: ArrayLike, xp: ArrayLike, fp: ArrayLike, period: float
) -> NDArray[float]:
    # TODO: do we need to do an explicit sorting?
    x = x % period

    xp = np.asarray(xp)
    fp = np.asarray(fp)

    # Duplicates the first knot point at position xp[0] + period (with its
    # corresponding value fp[0]), so np.interp can linearly interpolate across
    # the periodic boundary between the last and first knot points.
    xp2 = np.concatenate([xp, [xp[0] + period]])
    fp2 = np.concatenate([fp, [fp[0]]])

    # if x smaller than first control point, move to next period,
    # so it is surrounded by knots
    x2 = np.where(x < xp[0], x + period, x)

    return np.interp(x2, xp2, fp2)
