#!/usr/bin/env python3
"""verify_tube.py -- EXACT-RATIONAL stdlib checker for CONTRACTION-TUBE basin
certificates (A83, 2026-09-03; format `contraction-tube-certificate-v1`).

THE CLAIM (docs/proofs/contraction_tube.md, Theorem T1).  Let z-hat be A22's jam
(34 coordinates: (cx_i, cy_i, theta_i) for squares 0..10 and s last), z0 the rational
centre of krawczyk_cert.json (|z-hat - z0|_inf <= r0 = 1e-50), and v a CENTRE-ONLY
direction (v_theta = 0, v_s = 1, all v_i >= 0; the certificate stores v as 34 exact
rationals).  The tube

    Tube_v(T, r) = { z-hat - t*v + w : 0 <= t <= T, |w_i| <= r_i }

(r_i = r_c on centre coordinates, r_theta on tilts, r_s on s) contains, for every
side m = s-hat - t in [s-hat - T, s-hat], the configurations obtained by CONTRACTING
z-hat to side m along v and perturbing by w.  Theorem T1: every FEASIBLE z in
Tube_v(T, r) (11 closed unit squares with pairwise disjoint interiors inside
[0, z_s]^2) has  z_s >= s-hat, with equality only at z = z-hat.  Since z_s = s-hat
- t + w_s, a feasible point at depth t > r_s does not exist at all.

THE CHAIN (A36's (V') dichotomy re-based on the anisotropic tube box, A36 sec 3.1 /
RigidBasinMain.lean, with the max-form pinning; every quantity below is an exact
rational interval enclosure over the tube box B = hull of the tube widened by r0):

  W(z)   = sum_k omega_k g_k(z),  omega >= 0 on the universal rows (A22 rows 0..35 and
           the two aux dist rows 44, 45), omega > 0 on the 34 pin rows P = A22's S.
           Every loaded row is >= 0 at every feasible point of B (walls/dists globally,
           edge rows by the [V] margins checked on B), so W(z) >= 0 for feasible z.
  d = z - z-hat = -t v + w,  x = |d|_inf.  Taylor along the segment [z-hat, z] c B:
           W(z) = W(z-hat) + grad W(z-hat).d + (1/2) d^T H(xi) d,
           grad W(z-hat) = e_s + rho,  ||rho||_1 <= eps_w,  |W(z-hat)| <= eps_0,
     so    z_s - s-hat = d_s = W(z) - W(z-hat) - rho.d - (1/2) d^T H d
                             >= W(z) - E,
     with  E(x) = eps_0 + eps_w x + (1/2) tb^2 q_vv + tb * sum_i |Hv|_i wb_i
                        + (1/2) sum_ij |H_ij| wb_i wb_j,
           tb = min(T, x + r_s) >= t,  wb_i = min(r_i, x + tb |v_i|) >= |w_i|,
           q_vv >= sup |v^T H v| (interval sum THEN magnitude: the ray is nearly a
           straight line for every contact row -- only the two dist rows curve),
           |Hv|_i = (sup|(v^T H)_i| + sup|(H v)_i|)/2 (column and row sums kept
           separately, so no symmetry of the interval Hessian is assumed),
           |H_ij| >= sup |H_ij|.
  CASE 1  W(z) > E(x):  z_s > s-hat.
  CASE 2  W(z) <= E(x): the pin rows satisfy 0 <= g_k(z), sum_P omega_k g_k <= E, so
           |Y F_P(z)|_inf <= kappa_eff E (max-form, kappa_eff = max_P c_k/omega_k),
           |Y F_P(z-hat)|_inf <= kappa g_max, and the mean-value identity on the pins
           over B gives  x <= beta x + kappa_eff E(x) + kappa g_max,  beta =
           sup_B ||I - Y A_P||_inf < 1,  i.e.  x <= psi(x).
           psi is MONOTONE in x, so from x <= X_max := max_i (T|v_i| + r_i + 2 r0)
           the downward iterates x_{n+1} = psi(x_n) (rounded UP) satisfy x <= x_n for
           every n (induction: x <= psi(x) <= psi(x_n) = x_{n+1}).  The checker stops
           at the first n with x_n + r0 <= r_N = A22's radius: then z lies in A22's
           box N and A22's strict local optimality (a22_optimal, checked by
           attempts/A70-lean-wave4/code/a22_recheck_exact.py and Lean checkA22)
           gives z_s >= s-hat with equality iff z = z-hat.
  With T = 0 and r = h this is EXACTLY A36's chain (E = eps_0 + eps_w x + Hbar x^2);
  the checker reproduces a36_check_exact's constants on G3_UNIVERSAL (regression).

WHAT IS CHECKED, per certificate.  LOAD-BEARING for Theorem T1: [F] (shape of v only),
[S] (incl. the row-kind layout, the sha256 binding to krawczyk_cert.json and the
pair-relative translation self-test), [V], [Z], [G], [H], [K], [E], [P].  STRUCTURAL /
informational (they gate the exit code but the proof of T1 does not use them): [N], [C],
[CANARY], the direction_spec match, the claims comparison, the regression targets.
TRUSTED INPUTS (not re-verified here): krawczyk_cert.json's z0, r_0 (|z-hat - z0| <= r0),
r_N, S, Y, the 38 rows; A22's strict local optimality on box(z0, r_N) (a22_recheck_exact.py
/ Lean checkA22 + a22_optimal); the wall/dist global validity lemmas and the edge validity
lemma (A22 notes sec. 1, RigidGeom.lean).
  [F]  format / direction: v_theta = 0, v_s = 1, v >= 0; T >= 0, r_c, r_theta > 0, r_s >= 0.
       (W is exactly affine in s, so r_s is free and is NOT a reach lever; shipped certs
       use r_s = 0, the natural value for the seam consumer whose side is exactly s-hat - t.)
  [S]  pins = A22's S mapped into the 70-row table; omega >= 0; omega = 0 off the
       universal rows; omega > 0 on every pin; rows 0..35 are wall/edge and 44/45 dist;
       a22_sha256 present and equal to the loaded krawczyk_cert.json; the pair-relative
       self-test (absolute vs translated frame agree on value/grad/Hessian at a point).
  [N]  every loaded row is ACTIVE at z-hat (|g| < 1e-40 over box(z0, r0)).
  [C]  COMPRESSION LEMMA: gamma_k = grad g_k(z-hat).v >= 0 for every loaded row and
       sum_k omega_k gamma_k = 1 +- eps_w |v|_inf (the Farkas identity along the ray); the
       certificate declares which rows are STRICTLY compressed (gamma > 0) and the
       checker verifies the declared ones; g_k < 0 over box(z-hat - T v, r0) for them.
  [CANARY] some loaded WALL row with gamma > 0 has sup g < 0 over box(z-hat - T v, r0):
       the contracted Trump configuration provably violates containment, i.e. the tube's
       axis is NOT a packing for t = T (and, wall rows being affine in t, for every
       t in (0, T]).
  [V]  A22 edge rows 0..35 valid on the tube (tangential |t| < 1/2, depth > -1/2); tilts
       on B inside the Taylor kernel's domain |theta| <= 1.
  PAIR-RELATIVE EVALUATION: edge and dist rows depend on the centres only through
       c_i - c_j -- values, gradients AND Hessians (translation invariance) -- so they are
       enclosed on the box of RELATIVE centres, c_i - c_j in (z0_i - z0_j) - t(v_i - v_j)
       + (w_i - w_j) (width T|v_i - v_j| + 2 r_c + 2 r0), instead of the hull box B, where
       the two centres would vary independently (width T(v_i + v_j) + 2 r_c + 2 r0).
       Sound because the tube is convex (every mean-value point of the chain lies in it)
       and sharp: on the hull box the [V] margins degrade at ~0.8 per unit T (an
       artifact), on the tube at 0.39 (slot) / 0.10 (scale) per unit T.

CORRUPTION GATES (each MUST make the checker fail):
  omega-sign  negate omega on one pin row          drop-pin   zero omega on one pin row
  T-big       T x 100 without re-deriving          r-big      every r x 8
  drop-aux    zero omega on rows 44, 45            wrong-ray  negate the centre part of v
  omega-sign-free  negate a loaded non-pin omega   v-tilt     a tilt component in v
  false-strict  declare a gamma = 0 row strict     no-sha     drop the A22 sha256 binding
  [Z][G] eps_0, g_max, eps_w over box(z0, r0).
  [H]  the interval Hessian of W over B -> q_vv, |Hv|_i, |H_ij|.
  [K][E] beta(B) < 1, kappa, kappa_eff.
  [P]  the monotone iteration from X_max reaches x_n + r0 <= r_N within n_max steps.
  Claims in the JSON are INFORMATIONAL (compared, never gating), as in A76.

Usage:  python certs/verify_tube.py certs/tube_*.json [--a22 PATH]
                                     [--corrupt MODE] [--report PATH] [--nmax N]
Exit 0 = all PASS (or, under --corrupt, failed as required); 1 = FAIL; 2 = malformed.

stdlib only: fractions + json + hashlib + os + sys + time + glob.  The exact
interval kernel (dyadic 2^-PREC outward rounding, alternating-Taylor cos/sin, order-2
jets) and the 70-row v3 table are transcribed from attempts/A70-lean-wave4/code/
a36_check_exact.py (A70; itself from A36/A35), which is NOT imported.
"""
import glob
import hashlib
import json
import os
import sys
import time
from fractions import Fraction

PREC = 330                     # dyadic grid 2^-PREC for outward rounding
GRID = 1 << PREC
NV = 34
S_IDX = 33
HALF = [(Fraction(-1, 2), Fraction(-1, 2)), (Fraction(1, 2), Fraction(-1, 2)),
        (Fraction(1, 2), Fraction(1, 2)), (Fraction(-1, 2), Fraction(1, 2))]
NHAT = [(0, -1), (1, 0), (0, 1), (-1, 0)]      # outward normal of edge k
FORMAT = 'contraction-tube-certificate-v1'

# ------------------------------------------------- BASIS v3 spec (transcribed, A36)
AXES = [
    ('A01a',  0, 1, 1, 3, 36),
    ('A01b',  1, 3, 0, 2, 37),
    ('A03a',  0, 2, 3, 0, 38),
    ('A03b',  3, 0, 0, 3, 39),
    ('B13x',  1, 3, 3, 1, 40),
    ("B13x'", 3, 1, 1, 3, 42),
    ('B13y',  3, 0, 1, 3, 41),
    ("B13y'", 1, 2, 3, 1, 43),
]
AUX_POS = (44, 45)
EXTRA0 = 46
NEXT3 = 70
UNIVERSAL_ROWS = sorted(set(range(36)) | set(AUX_POS))


def axis_corner_positions(ax):
    _, o, e, p, kc, base = AXES[ax]
    out = {kc: base}
    for j, k in enumerate([k for k in range(4) if k != kc]):
        out[k] = EXTRA0 + 3 * ax + j
    return out


def build_constraints(K):
    out = [dict(c) for c in K['constraints'][:36]] + [None] * 34
    for ax, (nm, o, e, p, kc, base) in enumerate(AXES):
        for k, pos in axis_corner_positions(ax).items():
            out[pos] = {'kind': 'edge', 'i': p, 'corner': k, 'j': o,
                        'edge': e, 'name': '%s[k%d]' % (nm, k)}
    out[44] = dict(K['constraints'][36])
    out[45] = dict(K['constraints'][37])
    assert all(c is not None for c in out) and len(out) == NEXT3
    return out


# --------------------------------------------------------------- exact numerics
def frac(s):
    if isinstance(s, str) and '/' in s:
        n, d = s.split('/')
        return Fraction(int(n), int(d))
    if isinstance(s, float):
        raise ValueError('JSON floats are not accepted for load-bearing fields')
    return Fraction(s)


def fs(x):
    return '%d/%d' % (x.numerator, x.denominator)


def rdown(x):
    return Fraction((x.numerator * GRID) // x.denominator, GRID)


def rup(x):
    return Fraction(-((-x.numerator * GRID) // x.denominator), GRID)


class IV(object):
    """[lo, hi] with Fraction endpoints, outward-rounded to the 2^-PREC grid."""
    __slots__ = ('lo', 'hi')

    def __init__(self, lo, hi, rnd=True):
        if rnd:
            lo, hi = rdown(lo), rup(hi)
        assert lo <= hi
        self.lo, self.hi = lo, hi

    @staticmethod
    def point(x):
        return IV(x, x)

    def __add__(self, b):
        if not isinstance(b, IV):
            b = IV.point(b)
        return IV(self.lo + b.lo, self.hi + b.hi)

    __radd__ = __add__

    def __sub__(self, b):
        if not isinstance(b, IV):
            b = IV.point(b)
        return IV(self.lo - b.hi, self.hi - b.lo)

    def __rsub__(self, b):
        return IV.point(b) - self

    def __neg__(self):
        return IV(-self.hi, -self.lo, rnd=False)

    def __mul__(self, b):
        if not isinstance(b, IV):
            b = IV.point(b)
        ps = (self.lo * b.lo, self.lo * b.hi, self.hi * b.lo, self.hi * b.hi)
        return IV(min(ps), max(ps))

    __rmul__ = __mul__

    def mag(self):
        return max(abs(self.lo), abs(self.hi))


IZERO = IV.point(Fraction(0))
IONE = IV.point(Fraction(1))


def _cos_pt(x):
    """certified bracket of cos x at a rational point, |x| <= 1 (alternating
    Taylor partial sums with strictly decreasing terms bracket the value)."""
    x = abs(x)
    assert x <= 1
    xx = x * x
    term = Fraction(1)
    s = Fraction(0)
    lo = hi = None
    k = 0
    while True:
        s = s + (term if k % 2 == 0 else -term)
        if k % 2 == 0:
            hi = s
        else:
            lo = s
        k += 1
        term = term * xx / ((2 * k - 1) * (2 * k))
        if lo is not None and hi is not None \
                and term < Fraction(1, 1 << (PREC + 20)):
            break
        if k > 400:
            raise RuntimeError('cos Taylor did not converge')
    return lo, hi


def _sin_pt(x):
    if x < 0:
        lo, hi = _sin_pt(-x)
        return -hi, -lo
    if x == 0:
        return Fraction(0), Fraction(0)
    assert x <= 1
    xx = x * x
    term = Fraction(x)
    s = Fraction(0)
    lo = hi = None
    k = 0
    while True:
        s = s + (term if k % 2 == 0 else -term)
        if k % 2 == 0:
            hi = s
        else:
            lo = s
        k += 1
        term = term * xx / ((2 * k) * (2 * k + 1))
        if lo is not None and hi is not None \
                and term < Fraction(1, 1 << (PREC + 20)):
            break
        if k > 400:
            raise RuntimeError('sin Taylor did not converge')
    return lo, hi


_CPT, _SPT, _CIV, _SIV = {}, {}, {}, {}


def cos_iv(v):
    key = (v.lo, v.hi)
    out = _CIV.get(key)
    if out is not None:
        return out
    a, b = v.lo, v.hi
    if a not in _CPT:
        _CPT[a] = _cos_pt(a)
    if b not in _CPT:
        _CPT[b] = _cos_pt(b)
    ca, cb = _CPT[a], _CPT[b]
    lo = min(ca[0], cb[0])
    hi = Fraction(1) if a <= 0 <= b else max(ca[1], cb[1])
    out = IV(lo, hi)
    _CIV[key] = out
    return out


def sin_iv(v):
    key = (v.lo, v.hi)
    out = _SIV.get(key)
    if out is not None:
        return out
    if v.lo not in _SPT:
        _SPT[v.lo] = _sin_pt(v.lo)
    if v.hi not in _SPT:
        _SPT[v.hi] = _sin_pt(v.hi)
    sa, sb = _SPT[v.lo], _SPT[v.hi]
    out = IV(sa[0], sb[1])
    _SIV[key] = out
    return out


class J(object):
    """order-2 forward jets over exact intervals (structure = a36_check.J)."""
    __slots__ = ('v', 'g', 'h', 'd', 'o')

    def __init__(self, v, g, h, d, o):
        self.v, self.g, self.h, self.d, self.o = v, g, h, d, o

    @staticmethod
    def var(val, k, d, o):
        g = None
        if o >= 1:
            g = [IZERO] * d
            g[k] = IONE
        return J(val, g, [[IZERO] * d for _ in range(d)] if o >= 2 else None,
                 d, o)

    def __add__(self, b):
        if not isinstance(b, J):
            return J(self.v + b, self.g, self.h, self.d, self.o)
        d, o = self.d, self.o
        return J(self.v + b.v,
                 [self.g[i] + b.g[i] for i in range(d)] if o >= 1 else None,
                 [[self.h[i][j] + b.h[i][j] for j in range(d)]
                  for i in range(d)] if o >= 2 else None, d, o)

    def __sub__(self, b):
        if not isinstance(b, J):
            return J(self.v - b, self.g, self.h, self.d, self.o)
        d, o = self.d, self.o
        return J(self.v - b.v,
                 [self.g[i] - b.g[i] for i in range(d)] if o >= 1 else None,
                 [[self.h[i][j] - b.h[i][j] for j in range(d)]
                  for i in range(d)] if o >= 2 else None, d, o)

    def __mul__(self, b):
        d, o = self.d, self.o
        if not isinstance(b, J):
            return J(self.v * b,
                     [self.g[i] * b for i in range(d)] if o >= 1 else None,
                     [[self.h[i][j] * b for j in range(d)]
                      for i in range(d)] if o >= 2 else None, d, o)
        g = [self.g[i] * b.v + self.v * b.g[i]
             for i in range(d)] if o >= 1 else None
        h = None
        if o >= 2:
            h = [[self.h[i][j] * b.v + self.g[i] * b.g[j] + self.g[j] * b.g[i]
                  + self.v * b.h[i][j] for j in range(d)] for i in range(d)]
        return J(self.v * b.v, g, h, d, o)

    __rmul__ = __mul__

    def _ch(self, f, df, d2f):
        d, o = self.d, self.o
        g = [df * self.g[i] for i in range(d)] if o >= 1 else None
        h = None
        if o >= 2:
            h = [[df * self.h[i][j] + d2f * self.g[i] * self.g[j]
                  for j in range(d)] for i in range(d)]
        return J(f, g, h, d, o)

    def cos(self):
        c, s = cos_iv(self.v), sin_iv(self.v)
        return self._ch(c, -s, -c)

    def sin(self):
        c, s = cos_iv(self.v), sin_iv(self.v)
        return self._ch(s, c, -s)


def row_vars(c):
    if c['kind'] == 'wall':
        i = c['i']
        vs = [3 * i, 3 * i + 1, 3 * i + 2]
        if c['wall'] in ('x=s', 'y=s'):
            vs.append(33)
        return vs
    if c['kind'] == 'edge':
        i, j = c['i'], c['j']
        return [3 * i, 3 * i + 1, 3 * i + 2, 3 * j, 3 * j + 1, 3 * j + 2]
    if c['kind'] == 'dist':
        i, j = c['i'], c['j']
        return [3 * i, 3 * i + 1, 3 * j, 3 * j + 1]
    raise ValueError(c['kind'])


def row_jet(box, c, order):
    vs = row_vars(c)
    d = len(vs)
    V = [J.var(box[gi], k, d, order) for k, gi in enumerate(vs)]
    half = Fraction(1, 2)
    if c['kind'] == 'wall':
        cx, cy, th = V[0], V[1], V[2]
        hx, hy = HALF[c['corner']]
        co, si = th.cos(), th.sin()
        qx = cx + (co * hx - si * hy)
        qy = cy + (si * hx + co * hy)
        w = c['wall']
        if w == 'x=0':
            return qx, vs
        if w == 'y=0':
            return qy, vs
        S = V[3]
        return ((S - qx) if w == 'x=s' else (S - qy)), vs
    if c['kind'] == 'edge':
        cix, ciy, thi, cjx, cjy, thj = V
        hx, hy = HALF[c['corner']]
        ci, si = thi.cos(), thi.sin()
        qx = cix + (ci * hx - si * hy)
        qy = ciy + (si * hx + ci * hy)
        nhx, nhy = NHAT[c['edge']]
        cj, sj = thj.cos(), thj.sin()
        nx = cj * nhx - sj * nhy
        ny = sj * nhx + cj * nhy
        return (nx * (qx - cjx) + ny * (qy - cjy)) - half, vs
    if c['kind'] == 'dist':
        dx = V[0] - V[2]
        dy = V[1] - V[3]
        return (dx * dx + dy * dy) - 1, vs
    raise ValueError(c['kind'])


def edge_td(box, c):
    """(tangential, depth) intervals of an edge row's corner in the owner frame."""
    i, j2 = c['i'], c['j']
    hx, hy = HALF[c['corner']]
    ci, si = cos_iv(box[3 * i + 2]), sin_iv(box[3 * i + 2])
    qx = box[3 * i] + (ci * hx - si * hy)
    qy = box[3 * i + 1] + (si * hx + ci * hy)
    nhx, nhy = NHAT[c['edge']]
    cj, sj = cos_iv(box[3 * j2 + 2]), sin_iv(box[3 * j2 + 2])
    nx = cj * nhx - sj * nhy
    ny = sj * nhx + cj * nhy
    wx, wy = qx - box[3 * j2], qy - box[3 * j2 + 1]
    return (-ny * wx + nx * wy), (nx * wx + ny * wy)


# ------------------------------------------------------------------ boxes
def tube_box(z0, v, T, rad, r0):
    """hull of Tube_v(T, r) around z-hat, widened by r0 (z-hat in box(z0, r0)):
    coordinate i in [z0_i - T max(v_i,0) - r_i - r0, z0_i + T max(-v_i,0) + r_i + r0]."""
    out = []
    for i in range(NV):
        lo = z0[i] - T * max(v[i], 0) - rad[i] - r0
        hi = z0[i] + T * max(-v[i], 0) + rad[i] + r0
        out.append(IV(lo, hi))
    return out


def rad_box(z0, r):
    return [IV(x - r, x + r) for x in z0]


# ---------------------------------------------------------------- checking
class Check(object):
    def __init__(self, log):
        self.fails = []
        self.lines = []
        self.n = 0
        self.log = log

    def __call__(self, name, ok, detail=''):
        self.n += 1
        if not ok:
            self.fails.append(name)
            line = '  [FAIL] %s %s' % (name, detail)
            self.lines.append(line)
            self.log(line)
        return ok


def radii_of(cert):
    rc, rt, rs = frac(cert['r_c']), frac(cert['r_theta']), frac(cert['r_s'])
    rad = []
    for i in range(NV):
        if i == S_IDX:
            rad.append(rs)
        elif i % 3 == 2:
            rad.append(rt)
        else:
            rad.append(rc)
    return rad


def check_cert(cert, K, ck, log, nmax=4000, verbose=True):
    t0 = time.time()
    name = cert.get('name', '?')
    z0 = [frac(x) for x in K['z0']]
    Y = [[frac(x) for x in row] for row in K['Y']]
    rN = frac(K['r_N'])
    r0 = frac(K['r_0'])
    cons = build_constraints(K)
    stats = {'name': name}

    # [F] format / direction
    ck('%s format' % name, cert.get('format') == FORMAT, str(cert.get('format')))
    T = frac(cert['T'])
    v = [frac(x) for x in cert['direction_v']]
    rad = radii_of(cert)
    ck('%s T >= 0, r_c, r_theta > 0, r_s >= 0' % name,
       T >= 0 and rad[0] > 0 and rad[2] > 0 and rad[S_IDX] >= 0)
    ck('%s direction centre-only (v_theta = 0, v_s = 1)' % name,
       len(v) == NV and v[S_IDX] == 1 and all(v[3 * i + 2] == 0 for i in range(11)))
    ck('%s direction v >= 0' % name, all(x >= 0 for x in v))
    # the two named direction specs, recomputed from z0 (informational + gate on match)
    spec = cert.get('direction_spec', {})
    mode = spec.get('mode')
    s0 = z0[S_IDX]
    if mode == 'scale':
        vexp = [z0[i] / s0 if i % 3 != 2 else Fraction(0) for i in range(33)] + [Fraction(1)]
        ck('%s direction matches spec scale (v = z0/s0 on centres)' % name, v == vexp)
    elif mode == 'slot':
        pins = spec['pins']            # squares whose centres ride their slot lines
        vexp = []
        for i in range(33):
            sq = i // 3
            if i % 3 == 2:
                vexp.append(Fraction(0))
            elif sq in pins:
                # R-slot (alpha + 1*s) iff the coordinate is within 1e-30 of s0 - alpha
                x = z0[i]
                isR = any(abs(x - (s0 - a)) < Fraction(1, 10 ** 30)
                          for a in (Fraction(1, 2), Fraction(3, 2), Fraction(5, 2)))
                vexp.append(Fraction(1) if isR else Fraction(0))
            else:
                vexp.append(z0[i] / s0)
        vexp.append(Fraction(1))
        ck('%s direction matches spec slot(pins=%s)' % (name, pins), v == vexp)
    else:
        ck('%s direction spec known' % name, False, str(mode))

    # [S] pins, omega support, row-kind layout (what makes "walls/dists globally valid,
    # edges by [V]" and "pair rows get the relative box" theorems rather than observations)
    P_spec = [k if k < 36 else (44 if k == 36 else 45) for k in K['S']]
    P = list(cert['P'])
    ck('%s pin set = A22 S (mapped)' % name, P == P_spec and len(P) == NV)
    om = [frac(x) for x in cert['omega_rational']]
    ck('%s omega has 70 entries' % name, len(om) == NEXT3)
    if len(om) != NEXT3:
        om = (om + [Fraction(0)] * NEXT3)[:NEXT3]
    RV = set(UNIVERSAL_ROWS)
    ck('%s omega >= 0' % name, all(x >= 0 for x in om))
    ck('%s omega = 0 off the universal rows' % name,
       all(om[k] == 0 for k in range(NEXT3) if k not in RV),
       'nonzero: %s' % [k for k in range(NEXT3) if k not in RV and om[k] != 0][:6])
    ck('%s omega > 0 on every pin' % name, all(om[k] > 0 for k in P))
    ck('%s row-kind layout (0..35 wall/edge, 44/45 dist)' % name,
       all(cons[k]['kind'] in ('wall', 'edge') for k in range(36)) and
       all(cons[k]['kind'] == 'dist' for k in AUX_POS))
    loaded = sorted(set(k for k in range(NEXT3) if om[k] != 0) | set(P))
    ck('%s A22 certificate sha256 present and matching' % name,
       cert.get('a22_sha256') == K.get('_sha256'), str(cert.get('a22_sha256'))[:16])

    pbox = rad_box(z0, r0)
    B = tube_box(z0, v, T, rad, r0)

    # PAIR-RELATIVE INVARIANT self-test: at a fixed pseudo-random point of the tube every
    # loaded edge/dist row must give the same value, gradient and Hessian in the absolute
    # frame and in the translated frame (c_i - c_j, 0); this pins the coupling between
    # row_box's kind test and row_jet's expressions (review suggestion 1).
    def _translated_ok():
        worst = Fraction(0)
        seed = 12345
        pt = []
        for i in range(NV):
            seed = (1103515245 * seed + 12345) % (1 << 31)
            u = Fraction(seed, 1 << 31) * 2 - 1
            pt.append(z0[i] - T * v[i] * (u + 1) / 2 + rad[i] * u)
        abs_box = [IV.point(x) for x in pt]
        for k in loaded:
            c = cons[k]
            if c['kind'] not in ('edge', 'dist'):
                continue
            i, j2 = c['i'], c['j']
            rel = list(abs_box)
            for ax in range(2):
                rel[3 * i + ax] = IV.point(pt[3 * i + ax] - pt[3 * j2 + ax])
                rel[3 * j2 + ax] = IZERO
            ja, _ = row_jet(abs_box, c, 2)
            jr, _ = row_jet(rel, c, 2)
            worst = max(worst, abs(ja.v.lo - jr.v.lo), abs(ja.v.hi - jr.v.hi))
            for a in range(ja.d):
                worst = max(worst, abs(ja.g[a].lo - jr.g[a].lo), abs(ja.g[a].hi - jr.g[a].hi))
                for b in range(ja.d):
                    worst = max(worst, abs(ja.h[a][b].lo - jr.h[a][b].lo),
                                abs(ja.h[a][b].hi - jr.h[a][b].hi))
        return worst <= Fraction(8, GRID), worst
    ok_tr, worst_tr = _translated_ok()
    ck('%s pair-relative invariant (translation) self-test' % name, ok_tr,
       'worst %.3e' % float(worst_tr))

    # PAIR-RELATIVE boxes.  Edge and dist rows are translation invariant: they depend on
    # the centres only through c_i - c_j (values, gradients and Hessians alike), and on
    # the tube the two centres move TOGETHER along the ray, so
    #   c_i - c_j  in  (z0_i - z0_j) - t (v_i - v_j) + (w_i - w_j),  t in [0, T],
    # an interval of half-width ~ T|v_i - v_j|/2 + r_c, not T(v_i + v_j)/2 + r_c as the
    # hull box B would give.  Evaluating a pair row with square i's centre slots set to
    # the c_i - c_j interval and square j's to the point 0 is exact translation and is
    # sound for every point of the tube (the tube is convex, so every mean-value point
    # of the chain lies in it).  Wall rows keep B (their derivatives carry no centre).
    def pair_box(i, j2):
        bx = list(B)
        for ax in range(2):
            a, b = 3 * i + ax, 3 * j2 + ax
            dv = v[a] - v[b]
            lo = z0[a] - z0[b] - T * max(dv, 0) - rad[a] - rad[b] - 2 * r0
            hi = z0[a] - z0[b] + T * max(-dv, 0) + rad[a] + rad[b] + 2 * r0
            bx[a] = IV(lo, hi)
            bx[b] = IZERO
        return bx

    def row_box(c):
        if c['kind'] in ('edge', 'dist'):
            return pair_box(c['i'], c['j'])
        return B

    # [N] activity at z-hat
    gz = {}
    for k in loaded:
        gz[k] = row_jet(pbox, cons[k], 0)[0].v
    ck('%s loaded rows active at z-hat (<1e-40)' % name,
       all(gz[k].mag() < Fraction(1, 10 ** 40) for k in loaded),
       'max %.3e' % float(max(gz[k].mag() for k in loaded)))

    # [C] compression lemma: gamma_k = grad g_k(z-hat) . v
    gam = {}
    for k in loaded:
        j, vs = row_jet(pbox, cons[k], 1)
        acc = IZERO
        for loc, gi in enumerate(vs):
            if v[gi] != 0:
                acc = acc + j.g[loc] * v[gi]
        gam[k] = acc
    ck('%s [C] gamma_k >= 0 on every loaded row' % name,
       all(gam[k].hi >= 0 and gam[k].lo > -Fraction(1, 10 ** 30) for k in loaded),
       'min lo %.3e' % float(min(gam[k].lo for k in loaded)))
    strict = list(cert.get('strictly_compressed_rows', []))
    ck('%s [C] declared strictly compressed rows have gamma > 0' % name,
       all(k in gam and gam[k].lo > 0 for k in strict),
       'bad: %s' % [k for k in strict if k not in gam or gam[k].lo <= 0][:6])
    sg = IZERO
    for k in loaded:
        sg = sg + gam[k] * om[k]
    stats['sum_omega_gamma'] = (float(sg.lo), float(sg.hi))
    # eps_w is computed below; the identity check is deferred to there
    # value of the loaded rows at the contracted point z-hat - T v, enclosed over
    # box(z0 - T v, r0) (z-hat is within r0 of z0)
    zc = rad_box([z0[i] - T * v[i] for i in range(NV)], r0)
    gcon = {k: row_jet(zc, cons[k], 0)[0].v for k in loaded}
    ck('%s [C] strictly compressed rows negative at z-hat - T v' % name,
       T == 0 or all(gcon[k].hi < 0 for k in strict),
       'max hi %.3e' % float(max([gcon[k].hi for k in strict] or [0])))
    # a wall row that is STRICTLY compressed (gamma > 0 rigorously) and negative at the
    # contracted point; rows with gamma = 0 sit at z0's 1e-60 residual and do not count
    wall_neg = [k for k in loaded if cons[k]['kind'] == 'wall' and gam[k].lo > 0
                and gcon[k].hi < 0]
    ck('%s [CANARY] a loaded WALL row is violated at z-hat - T v (not a packing)' % name,
       T == 0 or bool(wall_neg), 'none' if not wall_neg else '')
    stats['canary_wall_rows'] = [cons[k].get('name', k) for k in wall_neg]
    stats['min_gamma_loaded'] = float(min(gam[k].lo for k in loaded))
    stats['n_strict'] = len(strict)

    # [V] validity of the A22 edge rows on B; tilt domain
    wt, wd = None, None
    wt_row = None
    for k in range(36):
        c = cons[k]
        if c['kind'] != 'edge':
            continue
        tt, dd = edge_td(row_box(c), c)
        t1 = Fraction(1, 2) - tt.mag()
        d1 = Fraction(1, 2) + dd.lo
        if wt is None or t1 < wt:
            wt, wt_row = t1, c.get('name', k)
        wd = d1 if wd is None else min(wd, d1)
    ck('%s [V] A22 edge rows valid on the tube box' % name, wt > 0 and wd > 0,
       'tangential %.6f (%s), depth+1/2 %.6f' % (float(wt), wt_row, float(wd)))
    ck('%s [V] tilts on the tube box within |theta| <= 1' % name,
       all(B[3 * i + 2].mag() <= 1 for i in range(11)))
    stats.update(min_tangential=float(wt), min_tangential_row=wt_row,
                 min_depth_plus_half=float(wd))

    # [Z] eps_0, g_max over box(z0, r0)
    e0 = sum(abs(om[k]) * gz[k].mag() for k in loaded)
    gmax = max(gz[k].mag() for k in P)
    # [G] eps_w
    acc = [IZERO] * NV
    for k in loaded:
        j, vs = row_jet(pbox, cons[k], 1)
        for loc, gi in enumerate(vs):
            acc[gi] = acc[gi] + om[k] * j.g[loc]
    ew = sum((acc[gi] - (IONE if gi == S_IDX else IZERO)).mag() for gi in range(NV))
    vinf = max(abs(x) for x in v)
    ck('%s [C] Farkas identity sum omega gamma = 1 +- eps_w |v|_inf' % name,
       sg.lo >= 1 - ew * vinf - Fraction(1, 10 ** 30) and
       sg.hi <= 1 + ew * vinf + Fraction(1, 10 ** 30),
       '[%.3e, %.3e]' % (float(sg.lo - 1), float(sg.hi - 1)))
    stats.update(eps_0=float(e0), eps_w=float(ew), g_max=float(gmax))

    # [H] Hessian of W over B
    Hd = {}
    for k in loaded:
        j, vs = row_jet(row_box(cons[k]), cons[k], 2)
        for a, ga in enumerate(vs):
            for b, gb in enumerate(vs):
                key = (ga, gb)
                t = om[k] * j.h[a][b]
                Hd[key] = t if key not in Hd else Hd[key] + t
    Hmag = {key: x.mag() for key, x in Hd.items()}
    Hbar = sum(Hmag.values()) / 2
    # the two cross sums are kept separate (column sums (v^T H)_b and row sums (H v)_a),
    # so the bound below never assumes the interval Hessian to be symmetric
    vHv = IZERO
    Hv_col = [IZERO] * NV          # (v^T H)_b = sum_a v_a H_ab
    Hv_row = [IZERO] * NV          # (H v)_a   = sum_b H_ab v_b
    for (a, b), x in Hd.items():
        if v[a] != 0 and v[b] != 0:
            vHv = vHv + x * (v[a] * v[b])
        if v[a] != 0:
            Hv_col[b] = Hv_col[b] + x * v[a]
        if v[b] != 0:
            Hv_row[a] = Hv_row[a] + x * v[b]
    q_vv = vHv.mag()
    # |d^T H d| <= t^2 |v^T H v| + t |(v^T H) w| + t |w^T (H v)| + |w^T H w|
    Hv_mag = [(Hv_col[i].mag() + Hv_row[i].mag()) / 2 for i in range(NV)]
    stats.update(Hbar=float(Hbar), q_vv=float(q_vv),
                 Hv_l1=float(sum(Hv_mag)),
                 Hv_l1_tilts=float(sum(Hv_mag[3 * i + 2] for i in range(11))))

    # [K] beta over B, kappa;  [E] kappa_eff
    grads = []
    for k in P:
        j, vs = row_jet(row_box(cons[k]), cons[k], 1)
        grads.append({gi: j.g[loc] for loc, gi in enumerate(vs)})
    beta = Fraction(0)
    for i in range(NV):
        rs = Fraction(0)
        for j2 in range(NV):
            ssum = IZERO
            for rr in range(NV):
                x = grads[rr].get(j2)
                if x is not None:
                    ssum = ssum + Y[i][rr] * x
            rs += ((IONE if i == j2 else IZERO) - ssum).mag()
        beta = max(beta, rs)
    kappa = max(sum(abs(Y[i][r]) for r in range(NV)) for i in range(NV))
    cvec = [max(abs(Y[i][r]) for i in range(NV)) for r in range(NV)]
    pins_pos = all(om[P[i]] > 0 for i in range(NV))
    keff = max(cvec[i] / om[P[i]] for i in range(NV)) if pins_pos else None
    ck('%s [E] kappa_eff finite (omega > 0 on pins)' % name, pins_pos)
    if keff is None:
        keff = Fraction(10 ** 30)          # forces [P] to fail; the gate above already fired
    ck('%s [K] beta(B) < 1' % name, beta < 1, 'beta = %.6f' % float(beta))
    stats.update(beta=float(beta), kappa=float(kappa), kappa_eff=float(keff))

    # [P] the monotone iteration
    X_max = max(T * abs(v[i]) + rad[i] + 2 * r0 for i in range(NV))
    rs_ = rad[S_IDX]

    def E_of(x):
        tb = min(T, x + rs_)
        wb = [min(rad[i], x + tb * abs(v[i])) for i in range(NV)]
        e = e0 + ew * x + Fraction(1, 2) * tb * tb * q_vv
        e += tb * sum(Hv_mag[i] * wb[i] for i in range(NV))
        q = Fraction(0)
        for (a, b), m in Hmag.items():
            q += m * wb[a] * wb[b]
        return e + q / 2

    def psi(x):
        return (keff * E_of(x) + kappa * gmax) / (1 - beta) if beta < 1 else x + 1

    x = X_max
    psiX = psi(X_max)
    stats.update(X_max=float(X_max), psi_Xmax=float(psiX),
                 psi_over_Xmax=float(psiX / X_max))
    reached = False
    n_it = 0
    if beta < 1:
        prev = x
        for n_it in range(1, nmax + 1):
            x = rup(psi(prev))
            if x + r0 <= rN:
                reached = True
                break
            if x >= prev:
                break               # stagnation: a fixed point above r_N
            prev = x
    ck('%s [P] monotone iteration reaches x_n + r0 <= r_N (A22 handover)' % name,
       reached, 'stopped at x = %.4e after %d steps (r_N = %.1e)'
       % (float(x), n_it, float(rN)))
    stats.update(x_star=float(x), n_iter=n_it, reached=reached,
                 seconds=round(time.time() - t0, 1))
    if verbose:
        log('  [ok] %-22s T=%-10s rc=%-9s rt=%-9s beta=%.4f Hbar=%.3f q_vv=%.3e '
            'Hv1(tilt)=%.3f keff=%.3f psi/X=%.4f x*=%.2e n=%d tan=%.5f (%s) %.1fs'
            % (name, cert['T'], cert['r_c'], cert['r_theta'], float(beta),
               float(Hbar), float(q_vv), stats['Hv_l1_tilts'], float(keff),
               stats['psi_over_Xmax'], float(x), n_it, float(wt), wt_row,
               stats['seconds']))
    # informational: claims vs recomputation (printed; never gating)
    cl = cert.get('claims', {})
    dev = {}
    for key in ('beta', 'Hbar', 'q_vv', 'kappa_eff', 'x_star', 'psi_over_Xmax',
                'min_tangential'):
        if key in cl and cl[key] not in (None, 0) and stats.get(key) not in (None, 0):
            dev[key] = abs(stats[key] - float(cl[key])) / abs(float(cl[key]))
    stats['claims_max_rel_dev'] = max(dev.values()) if dev else None
    if dev and max(dev.values()) > 1e-6:
        log('  [warn] %s: informational claims deviate from the recomputation by up to '
            '%.2e (%s) -- re-emit' % (name, max(dev.values()), max(dev, key=dev.get)))
    # optional regression targets (the A36 universal certificate as a T = 0 tube): gated
    rt = cert.get('regression_targets')
    if rt:
        bad = {k: (stats.get(k), t) for k, t in rt.items()
               if stats.get(k) is None or abs(stats[k] - float(t)) > 1e-3 * abs(float(t))}
        ck('%s regression targets reproduced (beta, Hbar, kappa_eff, psi/X)' % name,
           not bad, str(bad)[:120])
    return stats


# ------------------------------------------------------------------- corrupt
def apply_corrupt(cert, mode):
    if mode == 'omega-sign':
        r = cert['P'][0]
        cert['omega_rational'][r] = '-' + cert['omega_rational'][r]
    elif mode == 'drop-pin':
        cert['omega_rational'][cert['P'][3]] = '0/1'
    elif mode == 'T-big':
        cert['T'] = fs(frac(cert['T']) * 100 + Fraction(1, 100))
    elif mode == 'r-big':
        for key in ('r_c', 'r_theta', 'r_s'):
            cert[key] = fs(frac(cert[key]) * 8)
    elif mode == 'drop-aux':
        for p in AUX_POS:
            cert['omega_rational'][p] = '0/1'
    elif mode == 'wrong-ray':
        vv = [frac(x) for x in cert['direction_v']]
        cert['direction_v'] = [fs(-x) if i < 33 else fs(x) for i, x in enumerate(vv)]
        cert['direction_spec'] = {'mode': 'scale'} if cert.get(
            'direction_spec', {}).get('mode') == 'scale' else cert.get('direction_spec')
    elif mode == 'omega-sign-free':            # negate a loaded NON-pin row (row 1)
        cert['omega_rational'][1] = '-' + cert['omega_rational'][1]
    elif mode == 'v-tilt':                     # a tilt component in the direction
        cert['direction_v'][2] = '1/1000'
    elif mode == 'false-strict':               # declare a gamma = 0 row strictly compressed
        cert['strictly_compressed_rows'] = sorted(set(cert.get('strictly_compressed_rows', [])) | {0})
    elif mode == 'no-sha':                     # drop the binding to the A22 certificate
        cert.pop('a22_sha256', None)
    else:
        raise SystemExit('unknown corruption mode %s' % mode)


CORRUPTIONS = ('omega-sign', 'drop-pin', 'T-big', 'r-big', 'drop-aux', 'wrong-ray',
               'omega-sign-free', 'v-tilt', 'false-strict', 'no-sha')


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    args = list(sys.argv[1:])
    corrupt = report_path = None
    a22 = os.path.join(here, '..', 'attempts', 'A22-local-rigidity', 'results',
                       'krawczyk_cert.json')
    nmax = 4000
    for flag in ('--corrupt', '--report', '--a22', '--nmax'):
        if flag in args:
            q = args.index(flag)
            val = args[q + 1]
            del args[q:q + 2]
            if flag == '--corrupt':
                corrupt = val
            elif flag == '--report':
                report_path = val
            elif flag == '--a22':
                a22 = val
            else:
                nmax = int(val)
    files = []
    for a in args:
        files += sorted(glob.glob(a))
    if not files:
        print('usage: verify_tube.py certs/tube_*.json [--a22 PATH] [--corrupt MODE]')
        return 2
    if corrupt is not None and corrupt not in CORRUPTIONS:
        print('unknown corruption %s (choose from %s)' % (corrupt, CORRUPTIONS))
        return 2

    def log(s):
        sys.stdout.write(s + '\n')
        sys.stdout.flush()

    K = json.load(open(a22))
    a22_sha = hashlib.sha256(open(a22, 'rb').read()).hexdigest()
    K['_sha256'] = a22_sha
    log('verify_tube: %d certificate(s), A22 cert %s (sha256 %s...), PREC %d, EXACT'
        % (len(files), os.path.basename(a22), a22_sha[:12], PREC))
    if corrupt:
        log('*** CORRUPTION TEST: %s (this run MUST fail) ***' % corrupt)
        files = files[:1]
    ck = Check(log)
    rows = []
    t0 = time.time()
    for fn in files:
        try:
            cert = json.load(open(fn))
        except Exception as e:
            log('malformed %s: %s' % (fn, e))
            return 2
        cert.setdefault('name', os.path.splitext(os.path.basename(fn))[0])
        if corrupt:
            apply_corrupt(cert, corrupt)
        shape_ok = (isinstance(cert.get('direction_v'), list) and len(cert['direction_v']) == NV
                    and isinstance(cert.get('omega_rational'), list)
                    and isinstance(cert.get('P'), list)
                    and all(k in cert for k in ('T', 'r_c', 'r_theta', 'r_s')))
        if not shape_ok:
            log('malformed %s: missing/ill-sized fields' % fn)
            if not corrupt:
                return 2
            ck('%s well-formed' % cert['name'], False, 'shape')
            continue
        try:
            rows.append(check_cert(cert, K, ck, log, nmax=nmax))
        except (KeyError, ValueError, AssertionError, IndexError, TypeError,
                ZeroDivisionError) as e:
            ck('%s well-formed' % cert['name'], False, repr(e))
    wall = time.time() - t0
    rc = 0
    if corrupt:
        ok = bool(ck.fails)
        verdict = 'corruption %s: checker %s => %s' % (
            corrupt, 'FAILED as required' if ok else 'passed (BAD)', 'PASS' if ok else 'FAIL')
        log(verdict)
        rc = 0 if ok else 1
    else:
        verdict = 'ALL CHECKS PASS' if not ck.fails else 'FAILURES: %s' % sorted(set(ck.fails))[:6]
        log('  %d certificates, %d checks, %d failures, %.1f s' % (len(rows), ck.n, len(ck.fails), wall))
        log('=> %s' % verdict)
        rc = 0 if not ck.fails else 1
    if report_path:
        rep = {'n_certs': len(rows), 'n_checks': ck.n, 'n_failures': len(ck.fails),
               'failure_lines': ck.lines[:200], 'exact': True, 'PREC': PREC,
               'wall_seconds': round(wall, 1), 'verdict': verdict, 'corrupt': corrupt,
               'a22_sha256': a22_sha, 'certificates': rows}
        with open(report_path, 'w') as fh:
            json.dump(rep, fh, indent=1)
    return rc


if __name__ == '__main__':
    sys.exit(main())
