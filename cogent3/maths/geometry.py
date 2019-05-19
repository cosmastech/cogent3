#!/usr/bin/env python
"""Code for geometric operations, e.g. distances and center of mass."""

from numpy import array, take, newaxis, sqrt, sin, cos, pi, c_, \
    vstack, dot, ones, exp, sum, log, linalg, delete, insert, append, min, mean,\
    nonzero, allclose, identity, minimum, any
from numpy.linalg import norm

__author__ = "Sandra Smit"
__copyright__ = "Copyright 2007-2016, The Cogent Project"
__credits__ = ["Sandra Smit", "Gavin Huttley", "Rob Knight", "Daniel McDonald",
               "Marcin Cieslik", "Helmut Simon"]
__license__ = "GPL"
__version__ = "3.0a2"
__maintainer__ = "Sandra Smit"
__email__ = "sandra.smit@colorado.edu"
__status__ = "Production"


def center_of_mass(coordinates, weights=-1):
    """Calculates the center of mass for a dataset.

    coordinates, weights can be two things:
    either: coordinates = array of coordinates, where one column contains
        weights, weights = index of column that contains the weights
    or: coordinates = array of coordinates, weights = array of weights

    weights = -1 by default, because the simplest case is one dataset, where
        the last column contains the weights.
    If weights is given as a vector, it can be passed in as row or column.
    """
    if isinstance(weights, int):
        return center_of_mass_one_array(coordinates, weights)
    else:
        return center_of_mass_two_array(coordinates, weights)


def center_of_mass_one_array(data, weight_idx=-1):
    """Calculates the center of mass for a dataset

    data should be an array of x1,...,xn,r coordinates, where r is the
        weight of the point
    """
    data = array(data)
    coord_idx = list(range(data.shape[1]))
    del coord_idx[weight_idx]
    coordinates = take(data, (coord_idx), 1)
    weights = take(data, (weight_idx,), 1)
    return sum(coordinates * weights, 0) / sum(weights, 0)


def center_of_mass_two_array(coordinates, weights):
    """Calculates the center of mass for a set of weighted coordinates

    coordinates should be an array of coordinates
    weights should be an array of weights. Should have same number of items
        as the coordinates. Can be either row or column.
    """
    coordinates = array(coordinates)
    weights = array(weights)
    try:
        return sum(coordinates * weights, 0) / sum(weights, 0)
    except ValueError:
        weights = weights[:, newaxis]
        return sum(coordinates * weights, 0) / sum(weights, 0)


def distance(first, second):
    """Calculates Euclideas distance between two vectors (or arrays).

    WARNING: Vectors have to be the same dimension.
    """
    return sqrt(sum(((first - second) ** 2).ravel()))


def sphere_points(n):
    """Calculates uniformly distributed points on a unit sphere using the
    Golden Section Spiral algorithm.

    Arguments:

        -n: number of points
    """
    points = []
    inc = pi * (3 - sqrt(5))
    offset = 2 / float(n)
    for k in range(int(n)):
        y = k * offset - 1 + (offset / 2)
        r = sqrt(1 - y * y)
        phi = k * inc
        points.append([cos(phi) * r, y, sin(phi) * r])
    return array(points)


def coords_to_symmetry(coords, fmx, omx, mxs, mode):
    """Applies symmetry transformation matrices on coordinates. This is used to
    create a crystallographic unit cell or a biological molecule, requires
    orthogonal coordinates, a fractionalization matrix (fmx),
    an orthogonalization matrix (omx) and rotation matrices (mxs).

    Returns all coordinates with included identity, which should be the first
    matrix in mxs.

    Arguments:

        - coords: an array of orthogonal coordinates
        - fmx: fractionalization matrix
        - omx: orthogonalization matrix
        - mxs: a sequence of 4x4 rotation matrices
        - mode: if mode 'table' assumes rotation matrices operate on
          fractional coordinates (like in crystallographic tables).
    """
    all_coords = [coords]  # the first matrix is identity
    if mode == 'fractional':  # working with fractional matrices
        coords = dot(coords, fmx.transpose())
    # add column of 1.
    coords4 = c_[coords, array([ones(len(coords))]).transpose()]
    for i in range(1, len(mxs)):  # skip identity
        rot_mx = mxs[i].transpose()
        # rotate and translate, remove
        new_coords = dot(coords4, rot_mx)[:, :3]
        if mode == 'fractional':                 # ones column
            new_coords = dot(new_coords, omx.transpose()
                             )  # return to orthogonal
        all_coords.append(new_coords)
    # a vstack(arrays) with a following reshape is faster then
    # the equivalent creation of a new array via array(arrays).
    return vstack(all_coords).reshape((len(all_coords), coords.shape[0], 3))


def coords_to_crystal(coords, fmx, omx, n=1):
    """Applies primitive lattice translations to produce a crystal from the
    contents of a unit cell.

    Returns all coordinates with included zero translation (0, 0, 0).

    Arguments:
        - coords: an array of orthogonal coordinates
        - fmx: fractionalization matrix
        - omx: orthogonalization matrix
        - n: number of layers of unit-cells == (2*n+1)^2 unit-cells
    """
    rng = list(range(-n, n + 1))  # a range like -2, -1, 0, 1, 2
    fcoords = dot(coords, fmx.transpose())  # fractionalize
    vectors = [(x, y, z) for x in rng for y in rng for z in rng]
    # looking for the center Thickened cube numbers:
    # a(n)=n*(n^2+(n-1)^2)+(n-1)*2*n*(n-1) ;)
    all_coords = []
    for primitive_vector in vectors:
        all_coords.append(fcoords + primitive_vector)
    # a vstack(arrays) with a following reshape is faster then
    # the equivalent creation of a new array via array(arrays)
    all_coords = vstack(all_coords).reshape((len(all_coords),
                                             coords.shape[0], coords.shape[1], 3))
    all_coords = dot(all_coords, omx.transpose())  # orthogonalize
    return all_coords


class SimplexTransform:
    def __init__(self):
        """regular tetrahedron with one vertex at origin, one edge on x axis and 
        one face (base) in x-y plane."""
        q = array([[0, 0, 0], 
                   [sqrt(2), 0, 0],
                   [1/sqrt(2), sqrt(3/2), 0], 
                   [1/sqrt(2), 1/sqrt(6), 2 * sqrt(1/3)]])
        self.q = q

    def __array__(self, dtype=None):
        q = self.q
        if dtype is not None:
            q = q.astype(dtype)
        return q


def alr(x, col=-1):
    r"""
    Additive log ratio (alr) Aitchison transformation.
    Parameters
    ----------
    x: numpy.ndarray
       A composition (sum = 1)
    col: int
       The index of the position (vector) of x used in the
       denominator for alr transformations. Defaults to -1,
       i.e. last component of composition as is conventional.
    Returns
    -------
    numpy.ndarray
         alr-transformed data projected into R^(n-1)."""
    x = x.squeeze()
    if x.ndim != 1:
        raise ValueError("Input array must be 1D")
    if any(x <= 0):
        raise ValueError("Cannot have negative or zero proportions")
    logx = log(x)
    logx_short = delete(logx, col)
    return (logx_short - logx[col]).squeeze()


def clr(x):
    r"""
    Perform centre log ratio (clr) Aitchison transformation.
    Parameters
    ----------
    x: numpy.ndarray
       A composition (sum = 1)
    Returns
    -------
    numpy.ndarray
         clr-transformed data projected to hyperplane x1 + ... + xn=0."""

    x = x.squeeze()
    if x.ndim != 1:
        raise ValueError("Input array must be 1D")
    if any(x <= 0):
        raise ValueError("Cannot have negative or zero proportions")
    logx = log(x)
    gx = mean(logx)
    return (logx - gx).squeeze()


def clr_inv(x):
    r"""
    Inverse of clr. Also known as softmax
    Parameters
    ----------
    x: numpy.ndarray
       A real vector which is a transformed compositions.
    Returns
    -------
    numpy.ndarray
       A composition (sum = 1)."""

    x = x.squeeze()
    if x.ndim != 1:
        raise ValueError("Input array must be 1D")
    ex = exp(x)
    sumexp = sum(ex)
    return ex / sumexp


def alr_inv(x, col=-1):
    r"""
    Inverse of alr.
    Parameters
    ----------
    x: numpy.ndarray
       A real vector which is a transformed compositions.
    col: int
       The index of the position (vector) of x used in the
       denominator for alr transformations. Defaults to -1,
       i.e. last component of composition as is conventional.
    Returns
    -------
    numpy.ndarray
         A composition (sum = 1)."""
    x = x.squeeze()
    if x.ndim != 1:
        raise ValueError("Input array must be 1D")
    if col == -1:
        x = append(x, 0)
    else:
        x = insert(x, col, 0)
    ex = exp(x)
    sumexp = sum(ex)
    return ex / sumexp


def aitchison_distance(x, y):
    r"""
    Aitchison distance between two compositions.
    Parameters
    ----------
    x, y: numpy.ndarrays
       Compositions
    Returns
    -------
    numpy.float64
         A real value of this distance metric >= 0."""
    if any(x <= 0):
        raise ValueError("Cannot have negative \
                or zero proportions - parameter 0.")
    if any(y <= 0):
        raise ValueError("Cannot have negative \
                or zero proportions - parameter 1.")
    return linalg.norm(clr(x / y))


def multiplicative_replacement(x, eps=.01):
    r"""
    Perturbs a composition with zero proportions
    to one with no zero proportions.
    Parameters
    ----------
    x: numpy.ndarray
       Composition
    eps: float
        zeros will be altered to lowest non-zero
        value of array times eps before normalising.
    Returns
    -------
    numpy.ndarray
         Composition with no zero proportions."""
    if sum(x) == 0:
        raise ValueError("Input vector cannot total zero.")
    delta = min(x[nonzero(x)]) * eps
    if delta < 0:
        raise ValueError("Cannot have negative proportions.")
    shape_zeros = x < delta
    y = x + shape_zeros * delta
    return y / sum(y)


def tight_simplex(x):
    """Input is an array whose rows are points in the unit simplex in R^4 (compositions).
    Output is vertices of a smaller regular simplex also aligned within unit simplex
    containing the points of input.
    To be precise, it returns a regular simplex whose insphere is the smallest
    sphere centred on the centre of mass of the points in the set x
    that contains all the points."""
    x = x.squeeze()
    if x.ndim != 2:
        raise ValueError("Input array must be 2D.")
    if x.shape[1] != 4:
        raise ValueError("Input rows must have length 4.")
    if any(x <= 0):
        raise ValueError("Input cannot have negative or zero elements.")
    if not allclose(sum(x, axis=1), ones(x.shape[0])):
        raise ValueError("Input rows do not total to one.")
    cent = ones(4) / 4
    centx = mean(x, axis=0)
    trans_vertices = identity(4) + cent - centx
    radius = max(norm(x - centx, axis=1))
    radratio = minimum(radius * sqrt(12), 1.0)
    newvertices = centx + radratio * (trans_vertices - centx)
    return newvertices