import numpy as np
import math
from geomdl import BSpline, helpers, linalg
from vedo import pointcloud


def compensatecontrolpoints(targetcontrolpoints, toolcontrolpoints, iterationcontrolpoints, beta_arr, weight, normals):
    print(len(targetcontrolpoints))
    print(len(toolcontrolpoints))
    print(len(iterationcontrolpoints))
    print(len(beta_arr))
    differencevectors = np.subtract(iterationcontrolpoints, targetcontrolpoints)
    if normals:
        iterationPc = pointcloud.Points(iterationcontrolpoints)
        iterationPc.computeNormalsWithPCA()

        diffNormalComponents = list()
        for i in range(len(iterationcontrolpoints)):
            normalvec = iterationPc.normalAt(i)
            norm = np.sqrt(sum(np.array(normalvec) ** 2))
            normalComponent = (np.dot(differencevectors[i], normalvec) / norm ** 2) * normalvec
            diffNormalComponents.append(normalComponent)

        compensationvectors = -weight * np.array(diffNormalComponents)
        for i in range(len(compensationvectors)):
            compensationvectors[i] = compensationvectors[i] * beta_arr[i]
        compensatedcontrolpoints = np.add(toolcontrolpoints, compensationvectors)
        return compensatedcontrolpoints, compensationvectors, differencevectors
    else:
        compensationvectors = -weight * differencevectors
        for i in range(len(compensationvectors)):
            compensationvectors[i] = compensationvectors[i] * beta_arr[i]
        compensatedcontrolpoints = np.add(toolcontrolpoints, compensationvectors)
        return compensatedcontrolpoints, compensationvectors, differencevectors


def approximate_surface_with_knotvector(points, size_u, size_v, degree_u, degree_v, knotvector_u, knotvector_v,
                                        **kwargs):
    """ Surface approximation using least squares method with fixed number of control points.
    This algorithm interpolates the corner control points and approximates the remaining control points. Please refer to
    Algorithm A9.7 of The NURBS Book (2nd Edition), pp.422-423 for details.
    Keyword Arguments:
        * ``centripetal``: activates centripetal parametrization method. *Default: False*
        * ``ctrlpts_size_u``: number of control points on the u-direction. *Default: size_u - 1*
        * ``ctrlpts_size_v``: number of control points on the v-direction. *Default: size_v - 1*
    :param points: data points
    :type points: list, tuple
    :param size_u: number of data points on the u-direction, :math:`r`
    :type size_u: int
    :param size_v: number of data points on the v-direction, :math:`s`
    :type size_v: int
    :param degree_u: degree of the output surface for the u-direction
    :type degree_u: int
    :param degree_v: degree of the output surface for the v-direction
    :type degree_v: int
    :param knotvector_u: knotvector in u direction
    :type knotvector_u: list, tuple
    :param knotvector_v: knotvector in v direction
    :type knotvector_v: ist, tuple
    :return: approximated B-Spline surface
    :rtype: BSpline.Surface
    """
    # Keyword arguments
    use_centripetal = kwargs.get('centripetal', False)
    num_cpts_u = kwargs.get('ctrlpts_size_u', size_u - 1)  # number of datapts, r + 1 > number of ctrlpts, n + 1
    num_cpts_v = kwargs.get('ctrlpts_size_v', size_v - 1)  # number of datapts, s + 1 > number of ctrlpts, m + 1

    # Dimension
    dim = len(points[0])

    # Get uk and vl
    uk, vl = compute_params_surface(points, size_u, size_v, use_centripetal)

    # Compute knot vectors
    kv_u = knotvector_u
    kv_v = knotvector_v

    # Construct matrix Nu
    matrix_nu = []
    for i in range(1, size_u - 1):
        m_temp = []
        for j in range(1, num_cpts_u - 1):
            m_temp.append(helpers.basis_function_one(degree_u, kv_u, j, uk[i]))
        matrix_nu.append(m_temp)
    # Compute Nu transpose
    matrix_ntu = linalg.matrix_transpose(matrix_nu)
    # Compute NTNu matrix
    matrix_ntnu = linalg.matrix_multiply(matrix_ntu, matrix_nu)
    # Compute LU-decomposition of NTNu matrix
    matrix_ntnul, matrix_ntnuu = linalg.lu_decomposition(matrix_ntnu)

    # Fit u-direction
    ctrlpts_tmp = [[0.0 for _ in range(dim)] for _ in range(num_cpts_u * size_v)]
    for j in range(size_v):
        ctrlpts_tmp[j + (size_v * 0)] = list(points[j + (size_v * 0)])
        ctrlpts_tmp[j + (size_v * (num_cpts_u - 1))] = list(points[j + (size_v * (size_u - 1))])
        # Compute Rku - Eqn. 9.63
        pt0 = points[j + (size_v * 0)]  # Qzero
        ptm = points[j + (size_v * (size_u - 1))]  # Qm
        rku = []
        for i in range(1, size_u - 1):
            ptk = points[j + (size_v * i)]
            n0p = helpers.basis_function_one(degree_u, kv_u, 0, uk[i])
            nnp = helpers.basis_function_one(degree_u, kv_u, num_cpts_u - 1, uk[i])
            elem2 = [c * n0p for c in pt0]
            elem3 = [c * nnp for c in ptm]
            rku.append([a - b - c for a, b, c in zip(ptk, elem2, elem3)])
        # Compute Ru - Eqn. 9.67
        ru = [[0.0 for _ in range(dim)] for _ in range(num_cpts_u - 2)]
        for i in range(1, num_cpts_u - 1):
            ru_tmp = []
            for idx, pt in enumerate(rku):
                ru_tmp.append([p * helpers.basis_function_one(degree_u, kv_u, i, uk[idx + 1]) for p in pt])
            for d in range(dim):
                for idx in range(len(ru_tmp)):
                    ru[i - 1][d] += ru_tmp[idx][d]
        # Get intermediate control points
        for d in range(dim):
            b = [pt[d] for pt in ru]
            y = linalg.forward_substitution(matrix_ntnul, b)
            x = linalg.backward_substitution(matrix_ntnuu, y)
            for i in range(1, num_cpts_u - 1):
                ctrlpts_tmp[j + (size_v * i)][d] = x[i - 1]

    # Construct matrix Nv
    matrix_nv = []
    for i in range(1, size_v - 1):
        m_temp = []
        for j in range(1, num_cpts_v - 1):
            m_temp.append(helpers.basis_function_one(degree_v, kv_v, j, vl[i]))
        matrix_nv.append(m_temp)
    # Compute Nv transpose
    matrix_ntv = linalg.matrix_transpose(matrix_nv)
    # Compute NTNv matrix
    matrix_ntnv = linalg.matrix_multiply(matrix_ntv, matrix_nv)
    # Compute LU-decomposition of NTNv matrix
    matrix_ntnvl, matrix_ntnvu = linalg.lu_decomposition(matrix_ntnv)

    # Fit v-direction
    ctrlpts = [[0.0 for _ in range(dim)] for _ in range(num_cpts_u * num_cpts_v)]
    for i in range(num_cpts_u):
        ctrlpts[0 + (num_cpts_v * i)] = list(ctrlpts_tmp[0 + (size_v * i)])
        ctrlpts[num_cpts_v - 1 + (num_cpts_v * i)] = list(ctrlpts_tmp[size_v - 1 + (size_v * i)])
        # Compute Rkv - Eqs. 9.63
        pt0 = ctrlpts_tmp[0 + (size_v * i)]  # Qzero
        ptm = ctrlpts_tmp[size_v - 1 + (size_v * i)]  # Qm
        rkv = []
        for j in range(1, size_v - 1):
            ptk = ctrlpts_tmp[j + (size_v * i)]
            n0p = helpers.basis_function_one(degree_v, kv_v, 0, vl[j])
            nnp = helpers.basis_function_one(degree_v, kv_v, num_cpts_v - 1, vl[j])
            elem2 = [c * n0p for c in pt0]
            elem3 = [c * nnp for c in ptm]
            rkv.append([a - b - c for a, b, c in zip(ptk, elem2, elem3)])
        # Compute Rv - Eqn. 9.67
        rv = [[0.0 for _ in range(dim)] for _ in range(num_cpts_v - 2)]
        for j in range(1, num_cpts_v - 1):
            rv_tmp = []
            for idx, pt in enumerate(rkv):
                rv_tmp.append([p * helpers.basis_function_one(degree_v, kv_v, j, vl[idx + 1]) for p in pt])
            for d in range(dim):
                for idx in range(len(rv_tmp)):
                    rv[j - 1][d] += rv_tmp[idx][d]
        # Get intermediate control points
        for d in range(dim):
            b = [pt[d] for pt in rv]
            y = linalg.forward_substitution(matrix_ntnvl, b)
            x = linalg.backward_substitution(matrix_ntnvu, y)
            for j in range(1, num_cpts_v - 1):
                ctrlpts[j + (num_cpts_v * i)][d] = x[j - 1]

    # Generate B-spline surface
    surf = BSpline.Surface()
    surf.degree_u = degree_u
    surf.degree_v = degree_v
    surf.ctrlpts_size_u = num_cpts_u
    surf.ctrlpts_size_v = num_cpts_v
    surf.ctrlpts = ctrlpts
    surf.knotvector_u = kv_u
    surf.knotvector_v = kv_v

    return surf


def compute_params_surface(points, size_u, size_v, centripetal=False):
    """ Computes :math:`\\overline{u}_{k}` and :math:`\\overline{u}_{l}` for surfaces.
    The data points array has a row size of ``size_v`` and column size of ``size_u`` and it is 1-dimensional. Please
    refer to The NURBS Book (2nd Edition), pp.366-367 for details on how to compute :math:`\\overline{u}_{k}` and
    :math:`\\overline{u}_{l}` arrays for global surface interpolation.
    Please note that this function is not a direct implementation of Algorithm A9.3 which can be found on The NURBS Book
    (2nd Edition), pp.377-378. However, the output is the same.
    :param points: data points
    :type points: list, tuple
    :param size_u: number of points on the u-direction
    :type size_u: int
    :param size_v: number of points on the v-direction
    :type size_v: int
    :param centripetal: activates centripetal parametrization method
    :type centripetal: bool
    :return: :math:`\\overline{u}_{k}` and :math:`\\overline{u}_{l}` parameter arrays as a tuple
    :rtype: tuple
    """
    # Compute uk
    uk = [0.0 for _ in range(size_u)]

    # Compute for each curve on the v-direction
    uk_temp = []
    for v in range(size_v):
        pts_u = [points[v + (size_v * u)] for u in range(size_u)]
        uk_temp += compute_params_curve(pts_u, centripetal)

    # Do averaging on the u-direction
    for u in range(size_u):
        knots_v = [uk_temp[u + (size_u * v)] for v in range(size_v)]
        uk[u] = sum(knots_v) / size_v

    # Compute vl
    vl = [0.0 for _ in range(size_v)]

    # Compute for each curve on the u-direction
    vl_temp = []
    for u in range(size_u):
        pts_v = [points[v + (size_v * u)] for v in range(size_v)]
        vl_temp += compute_params_curve(pts_v, centripetal)

    # Do averaging on the v-direction
    for v in range(size_v):
        knots_u = [vl_temp[v + (size_v * u)] for u in range(size_u)]
        vl[v] = sum(knots_u) / size_u

    return uk, vl


def compute_params_curve(points, centripetal=False):
    """ Computes :math:`\\overline{u}_{k}` for curves.
    Please refer to the Equations 9.4 and 9.5 for chord length parametrization, and Equation 9.6 for centripetal method
    on The NURBS Book (2nd Edition), pp.364-365.
    :param points: data points
    :type points: list, tuple
    :param centripetal: activates centripetal parametrization method
    :type centripetal: bool
    :return: parameter array, :math:`\\overline{u}_{k}`
    :rtype: list
    """
    if not isinstance(points, (list, tuple)):
        raise TypeError("Data points must be a list or a tuple")

    # Length of the points array
    num_points = len(points)

    # Calculate chord lengths
    cds = [0.0 for _ in range(num_points + 1)]
    cds[-1] = 1.0
    for i in range(1, num_points):
        distance = linalg.point_distance(points[i], points[i - 1])
        cds[i] = math.sqrt(distance) if centripetal else distance

    # Find the total chord length
    d = sum(cds[1:-1])

    # Divide individual chord lengths by the total chord length
    uk = [0.0 for _ in range(num_points)]
    for i in range(num_points):
        uk[i] = sum(cds[0:i + 1]) / d

    return uk
