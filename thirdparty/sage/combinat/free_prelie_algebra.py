# -*- coding: utf-8 -*-
r"""
Free Pre-Lie Algebras

AUTHORS:

- Florent Hivert, Frédéric Chapoton (2011)
"""

#*****************************************************************************
#       Copyright (C) 2010-2015 Florent Hivert <Florent.Hivert@lri.fr>,
#
#  Distributed under the terms of the GNU General Public License (GPL)
#  as published by the Free Software Foundation; either version 2 of
#  the License, or (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************
from six import iteritems

from sage.categories.magmatic_algebras import MagmaticAlgebras
from sage.categories.lie_algebras import LieAlgebras
from sage.categories.magmas import Magmas
from sage.categories.pushout import (ConstructionFunctor,
                                     CompositeConstructionFunctor,
                                     IdentityConstructionFunctor)
from sage.categories.rings import Rings
from sage.categories.functor import Functor

from sage.combinat.free_module import CombinatorialFreeModule
from sage.combinat.words.alphabet import Alphabet
from sage.combinat.rooted_tree import (RootedTrees, RootedTree,
                                       LabelledRootedTrees,
                                       LabelledRootedTree)

from sage.misc.lazy_import import lazy_import
from sage.misc.lazy_attribute import lazy_attribute
from sage.misc.cachefunc import cached_method

from sage.sets.family import Family
lazy_import('sage.structure.parent', 'CoercionException')


class FreePreLieAlgebra(CombinatorialFreeModule):
    r"""
    The free pre-Lie algebra.

    Pre-Lie algebras are non-associative algebras, where the product `*`
    satisfies

    .. MATH::

        (x * y) * z - x * (y * z) = (x * z) * y - x * (z * y).

    We use here the convention where the associator

    .. MATH::

        (x, y, z) := (x * y) * z - x * (y * z)

    is symmetric in its two rightmost arguments. This is sometimes called
    a right pre-Lie algebra.

    They have appeared in numerical analysis and deformation theory.

    The free Pre-Lie algebra on a given set `E` has an explicit
    description using rooted trees, just as the free associative algebra
    can be described using words. The underlying vector space has a basis
    indexed by finite rooted trees endowed with a map from their vertices
    to `E`. In this basis, the product of two (decorated) rooted trees `S
    * T` is the sum over vertices of `S` of the rooted tree obtained by
    adding one edge from the root of `T` to the given vertex of `S`. The
    root of these trees is taken to be the root of `S`. The free pre-Lie
    algebra can also be considered as the free algebra over the PreLie operad.

    .. WARNING::

        The usual binary operator ``*`` can be used for the pre-Lie product.
        Beware that it but must be parenthesized properly, as the pre-Lie
        product is not associative. By default, a multiple product will be
        taken with left parentheses.

    EXAMPLES::

        sage: F = algebras.FreePreLie(ZZ, 'xyz')
        sage: x,y,z = F.gens()
        sage: (x * y) * z
        B[x[y[z[]]]] + B[x[y[], z[]]]
        sage: (x * y) * z - x * (y * z) == (x * z) * y - x * (z * y)
        True

    The free pre-Lie algebra is non-associative::

        sage: x * (y * z) == (x * y) * z
        False

    The default product is with left parentheses::

        sage: x * y * z == (x * y) * z
        True
        sage: x * y * z * x == ((x * y) * z) * x
        True

    The NAP product as defined in [Liv2006]_ is also implemented on the same
    vector space::

        sage: N = F.nap_product
        sage: N(x*y,z*z)
        B[x[y[], z[z[]]]]

    When ``None`` is given as input, unlabelled trees are used instead::

        sage: F1 = algebras.FreePreLie(QQ, None)
        sage: w = F1.gen(0); w
        B[[]]
        sage: w * w * w * w
        B[[[[[]]]]] + B[[[[], []]]] + 3*B[[[], [[]]]] + B[[[], [], []]]

    However, it is equally possible to use labelled trees instead::

        sage: F1 = algebras.FreePreLie(QQ, 'q')
        sage: w = F1.gen(0); w
        B[q[]]
        sage: w * w * w * w
        B[q[q[q[q[]]]]] + B[q[q[q[], q[]]]] + 3*B[q[q[], q[q[]]]] + B[q[q[], q[], q[]]]

    The set `E` can be infinite::

        sage: F = algebras.FreePreLie(QQ, ZZ)
        sage: w = F.gen(1); w
        B[1[]]
        sage: x = F.gen(2); x
        B[-1[]]
        sage: y = F.gen(3); y
        B[2[]]
        sage: w*x
        B[1[-1[]]]
        sage: (w*x)*y
        B[1[-1[2[]]]] + B[1[-1[], 2[]]]
        sage: w*(x*y)
        B[1[-1[2[]]]]

    .. NOTE::

        Variables names can be ``None``, a list of strings, a string
        or an integer. When ``None`` is given, unlabelled rooted
        trees are used. When a single string is given, each letter is taken
        as a variable. See
        :func:`sage.combinat.words.alphabet.build_alphabet`.

    .. WARNING::

        Beware that the underlying combinatorial free module is based
        either on ``RootedTrees`` or on ``LabelledRootedTrees``, with no
        restriction on the labellings. This means that all code calling
        the :meth:`basis` method would not give meaningful results, since
        :meth:`basis` returns many "chaff" elements that do not belong to
        the algebra.

    REFERENCES:

    - [ChLi]_

    - [Liv2006]_
    """
    @staticmethod
    def __classcall_private__(cls, R, names=None):
        """
        Normalize input to ensure a unique representation.

        EXAMPLES::

            sage: F1 = algebras.FreePreLie(QQ, 'xyz')
            sage: F2 = algebras.FreePreLie(QQ, 'x,y,z')
            sage: F3 = algebras.FreePreLie(QQ, ['x','y','z'])
            sage: F4 = algebras.FreePreLie(QQ, Alphabet('xyz'))
            sage: F1 is F2 and F1 is F3 and F1 is F4
            True
        """
        if names is not None:
            if ',' in names:
                names = [u for u in names if u != ',']
            names = Alphabet(names)

        if R not in Rings():
            raise TypeError("argument R must be a ring")

        return super(FreePreLieAlgebra, cls).__classcall__(cls, R, names)

    def __init__(self, R, names=None):
        """
        Initialize ``self``.

        TESTS::

            sage: A = algebras.FreePreLie(QQ, '@'); A
            Free PreLie algebra on one generator ['@'] over Rational Field
            sage: TestSuite(A).run()

            sage: A = algebras.FreePreLie(QQ, None); A
            Free PreLie algebra on one generator ['o'] over Rational Field

            sage: F = algebras.FreePreLie(QQ, 'xy')
            sage: TestSuite(F).run() # long time
        """
        if names is None:
            Trees = RootedTrees()
            key = RootedTree.sort_key
            self._alphabet = Alphabet(['o'])
        else:
            Trees = LabelledRootedTrees()
            key = LabelledRootedTree.sort_key
            self._alphabet = names
        # Here one would need LabelledRootedTrees(names)
        # so that one can restrict the labels to some fixed set

        cat = MagmaticAlgebras(R).WithBasis().Graded() & LieAlgebras(R).WithBasis().Graded()
        CombinatorialFreeModule.__init__(self, R, Trees,
                                         latex_prefix="",
                                         sorting_key=key,
                                         category=cat)

    def variable_names(self):
        r"""
        Return the names of the variables.

        EXAMPLES::

            sage: R = algebras.FreePreLie(QQ, 'xy')
            sage: R.variable_names()
            {'x', 'y'}

            sage: R = algebras.FreePreLie(QQ, None)
            sage: R.variable_names()
            {'o'}
        """
        return self._alphabet

    def _repr_(self):
        """
        Return the string representation of ``self``.

        EXAMPLES::

            sage: algebras.FreePreLie(QQ, '@')  # indirect doctest
            Free PreLie algebra on one generator ['@'] over Rational Field
        """
        n = self.algebra_generators().cardinality()
        if n == 1:
            gen = "one generator"
        else:
            gen = "{} generators".format(n)
        s = "Free PreLie algebra on {} {} over {}"
        try:
            return s.format(gen, self._alphabet.list(), self.base_ring())
        except NotImplementedError:
            return s.format(gen, self._alphabet, self.base_ring())

    def gen(self, i):
        r"""
        Return the ``i``-th generator of the algebra.

        INPUT:

        - ``i`` -- an integer

        EXAMPLES::

            sage: F = algebras.FreePreLie(ZZ, 'xyz')
            sage: F.gen(0)
            B[x[]]

            sage: F.gen(4)
            Traceback (most recent call last):
            ...
            IndexError: argument i (= 4) must be between 0 and 2
        """
        G = self.algebra_generators()
        n = G.cardinality()
        if i < 0 or not i < n:
            m = "argument i (= {}) must be between 0 and {}".format(i, n - 1)
            raise IndexError(m)
        return G[G.keys().unrank(i)]

    @cached_method
    def algebra_generators(self):
        r"""
        Return the generators of this algebra.

        These are the rooted trees with just one vertex.

        EXAMPLES::

            sage: A = algebras.FreePreLie(ZZ, 'fgh'); A
            Free PreLie algebra on 3 generators ['f', 'g', 'h']
             over Integer Ring
            sage: list(A.algebra_generators())
            [B[f[]], B[g[]], B[h[]]]

            sage: A = algebras.FreePreLie(QQ, ['x1','x2'])
            sage: list(A.algebra_generators())
            [B[x1[]], B[x2[]]]
        """
        Trees = self.basis().keys()
        return Family(self._alphabet, lambda a: self.monomial(Trees([], a)))

    def change_ring(self, R):
        """
        Return the free pre-Lie algebra in the same variables over `R`.

        INPUT:

        - `R` -- a ring

        EXAMPLES::

            sage: A = algebras.FreePreLie(ZZ, 'fgh')
            sage: A.change_ring(QQ)
            Free PreLie algebra on 3 generators ['f', 'g', 'h'] over
            Rational Field
        """
        return FreePreLieAlgebra(R, names=self.variable_names())

    def gens(self):
        """
        Return the generators of ``self`` (as an algebra).

        EXAMPLES::

            sage: A = algebras.FreePreLie(ZZ, 'fgh')
            sage: A.gens()
            (B[f[]], B[g[]], B[h[]])
        """
        return tuple(self.algebra_generators())

    def degree_on_basis(self, t):
        """
        Return the degree of a rooted tree in the free Pre-Lie algebra.

        This is the number of vertices.

        EXAMPLES::

            sage: A = algebras.FreePreLie(QQ, None)
            sage: RT = A.basis().keys()
            sage: A.degree_on_basis(RT([RT([])]))
            2
        """
        return t.node_number()

    @cached_method
    def an_element(self):
        """
        Return an element of ``self``.

        EXAMPLES::

            sage: A = algebras.FreePreLie(QQ, 'xy')
            sage: A.an_element()
            B[x[x[x[x[]]]]] + B[x[x[], x[x[]]]]
        """
        o = self.gen(0)
        return (o * o) * (o * o)

    def some_elements(self):
        """
        Return some elements of the free pre-Lie algebra.

        EXAMPLES::

            sage: A = algebras.FreePreLie(QQ, None)
            sage: A.some_elements()
            [B[[]], B[[[]]], B[[[[[]]]]] + B[[[], [[]]]], B[[[[]]]] + B[[[], []]], B[[[]]]]

        With several generators::

            sage: A = algebras.FreePreLie(QQ, 'xy')
            sage: A.some_elements()
            [B[x[]],
             B[x[x[]]],
             B[x[x[x[x[]]]]] + B[x[x[], x[x[]]]],
             B[x[x[x[]]]] + B[x[x[], x[]]],
             B[x[x[y[]]]] + B[x[x[], y[]]]]
        """
        o = self.gen(0)
        x = o * o
        y = o
        G = self.algebra_generators()
        # Take only the first 3 generators, otherwise the final element is too big
        if G.cardinality() < 3:
            for w in G:
                y = y * w
        else:
            K = G.keys()
            for i in range(3):
                y = y * G[K.unrank(i)]
        return [o, x, x * x, x * o, y]

    def product_on_basis(self, x, y):
        """
        Return the pre-Lie product of two trees.

        This is the sum over all graftings of the root of `y` over a vertex
        of `x`. The root of the resulting trees is the root of `x`.

        .. SEEALSO::

            :meth:`pre_Lie_product`

        EXAMPLES::

            sage: A = algebras.FreePreLie(QQ, None)
            sage: RT = A.basis().keys()
            sage: x = RT([RT([])])
            sage: A.product_on_basis(x, x)
            B[[[[[]]]]] + B[[[], [[]]]]
        """
        return self.sum(self.basis()[u] for u in x.graft_list(y))

    pre_Lie_product_on_basis = product_on_basis

    @lazy_attribute
    def pre_Lie_product(self):
        """
        Return the pre-Lie product.

        .. SEEALSO::

            :meth:`pre_Lie_product_on_basis`

        EXAMPLES::

            sage: A = algebras.FreePreLie(QQ, None)
            sage: RT = A.basis().keys()
            sage: x = A(RT([RT([])]))
            sage: A.pre_Lie_product(x, x)
            B[[[[[]]]]] + B[[[], [[]]]]
        """
        plb = self.pre_Lie_product_on_basis
        return self._module_morphism(self._module_morphism(plb, position=0,
                                                           codomain=self),
                                     position=1)

    def bracket_on_basis(self, x, y):
        r"""
        Return the Lie bracket of two trees.

        This is the commutator `[x, y] = x * y - y * x` of the pre-Lie product.

        .. SEEALSO::

            :meth:`pre_Lie_product_on_basis`

        EXAMPLES::

            sage: A = algebras.FreePreLie(QQ, None)
            sage: RT = A.basis().keys()
            sage: x = RT([RT([])])
            sage: y = RT([x])
            sage: A.bracket_on_basis(x, y)
            -B[[[[], [[]]]]] + B[[[], [[[]]]]] - B[[[[]], [[]]]]
        """
        return self.product_on_basis(x, y) - self.product_on_basis(y, x)

    def nap_product_on_basis(self, x, y):
        """
        Return the NAP product of two trees.

        This is the grafting of the root of `y` over the root
        of `x`. The root of the resulting tree is the root of `x`.

        .. SEEALSO::

            :meth:`nap_product`

        EXAMPLES::

            sage: A = algebras.FreePreLie(QQ, None)
            sage: RT = A.basis().keys()
            sage: x = RT([RT([])])
            sage: A.nap_product_on_basis(x, x)
            B[[[], [[]]]]
        """
        return self.basis()[x.graft_on_root(y)]

    @lazy_attribute
    def nap_product(self):
        """
        Return the NAP product.

        .. SEEALSO::

            :meth:`nap_product_on_basis`

        EXAMPLES::

            sage: A = algebras.FreePreLie(QQ, None)
            sage: RT = A.basis().keys()
            sage: x = A(RT([RT([])]))
            sage: A.nap_product(x, x)
            B[[[], [[]]]]
        """
        npb = self.nap_product_on_basis
        return self._module_morphism(self._module_morphism(npb,
                                                           position=0,
                                                           codomain=self),
                                     position=1)

    def _element_constructor_(self, x):
        r"""
        Convert ``x`` into ``self``.

        EXAMPLES::

            sage: R = algebras.FreePreLie(QQ, 'xy')
            sage: x, y = R.gens()
            sage: R(x)
            B[x[]]
            sage: R(x+4*y)
            B[x[]] + 4*B[y[]]

            sage: Trees = R.basis().keys()
            sage: R(Trees([],'x'))
            B[x[]]
            sage: D = algebras.FreePreLie(ZZ, 'xy')
            sage: X, Y = D.gens()
            sage: R(X-Y).parent()
            Free PreLie algebra on 2 generators ['x', 'y'] over Rational Field

        TESTS::

            sage: R.<x,y> = algebras.FreePreLie(QQ)
            sage: S.<z> = algebras.FreePreLie(GF(3))
            sage: R(z)
            Traceback (most recent call last):
            ...
            TypeError: not able to convert this to this algebra
        """
        if (isinstance(x, (RootedTree, LabelledRootedTree)) and
                x in self.basis().keys()):
            return self.monomial(x)
        try:
            P = x.parent()
            if isinstance(P, FreePreLieAlgebra):
                if P is self:
                    return x
                if self._coerce_map_from_(P):
                    return self.element_class(self, x.monomial_coefficients())
        except AttributeError:
            raise TypeError('not able to convert this to this algebra')
        else:
            raise TypeError('not able to convert this to this algebra')
        # Ok, not a pre-Lie algebra element (or should not be viewed as one).

    def _coerce_map_from_(self, R):
        r"""
        Return ``True`` if there is a coercion from ``R`` into ``self``
        and ``False`` otherwise.

        The things that coerce into ``self`` are

        - free pre-Lie algebras whose set `E` of labels is
          a subset of the corresponding self of ``set`, and whose base
          ring has a coercion map into ``self.base_ring()``

        EXAMPLES::

            sage: F = algebras.FreePreLie(GF(7), 'xyz'); F
            Free PreLie algebra on 3 generators ['x', 'y', 'z']
             over Finite Field of size 7

        Elements of the free pre-Lie algebra canonically coerce in::

            sage: x, y, z = F.gens()
            sage: F.coerce(x+y) == x+y
            True

        The free pre-Lie algebra over `\ZZ` on `x, y, z` coerces in, since
        `\ZZ` coerces to `\GF{7}`::

            sage: G = algebras.FreePreLie(ZZ, 'xyz')
            sage: Gx,Gy,Gz = G.gens()
            sage: z = F.coerce(Gx+Gy); z
            B[x[]] + B[y[]]
            sage: z.parent() is F
            True

        However, `\GF{7}` does not coerce to `\ZZ`, so the free pre-Lie
        algebra over `\GF{7}` does not coerce to the one over `\ZZ`::

            sage: G.coerce(y)
            Traceback (most recent call last):
            ...
            TypeError: no canonical coercion from Free PreLie algebra
             on 3 generators ['x', 'y', 'z'] over Finite Field of size
             7 to Free PreLie algebra on 3 generators ['x', 'y', 'z']
             over Integer Ring

        TESTS::

            sage: F = algebras.FreePreLie(ZZ, 'xyz')
            sage: G = algebras.FreePreLie(QQ, 'xyz')
            sage: H = algebras.FreePreLie(ZZ, 'y')
            sage: F._coerce_map_from_(G)
            False
            sage: G._coerce_map_from_(F)
            True
            sage: F._coerce_map_from_(H)
            True
            sage: F._coerce_map_from_(QQ)
            False
            sage: G._coerce_map_from_(QQ)
            False
            sage: F.has_coerce_map_from(PolynomialRing(ZZ, 3, 'x,y,z'))
            False
        """
        # free prelie algebras in a subset of variables
        # over any base that coerces in:
        if isinstance(R, FreePreLieAlgebra):
            if all(x in self.variable_names() for x in R.variable_names()):
                if self.base_ring().has_coerce_map_from(R.base_ring()):
                    return True
        return False

    def construction(self):
        """
        Return a pair ``(F, R)``, where ``F`` is a :class:`PreLieFunctor`
        and `R` is a ring, such that ``F(R)`` returns ``self``.

        EXAMPLES::

            sage: P = algebras.FreePreLie(ZZ, 'x,y')
            sage: x,y = P.gens()
            sage: F, R = P.construction()
            sage: F
            PreLie[x,y]
            sage: R
            Integer Ring
            sage: F(ZZ) is P
            True
            sage: F(QQ)
            Free PreLie algebra on 2 generators ['x', 'y'] over Rational Field
        """
        return PreLieFunctor(self.variable_names()), self.base_ring()


class PreLieFunctor(ConstructionFunctor):
    """
    A constructor for pre-Lie algebras.

    EXAMPLES::

        sage: P = algebras.FreePreLie(ZZ, 'x,y')
        sage: x,y = P.gens()
        sage: F = P.construction()[0]; F
        PreLie[x,y]

        sage: A = GF(5)['a,b']
        sage: a, b = A.gens()
        sage: F(A)
        Free PreLie algebra on 2 generators ['x', 'y'] over Multivariate Polynomial Ring in a, b over Finite Field of size 5

        sage: f = A.hom([a+b,a-b],A)
        sage: F(f)
        Generic endomorphism of Free PreLie algebra on 2 generators ['x', 'y']
        over Multivariate Polynomial Ring in a, b over Finite Field of size 5

        sage: F(f)(a * F(A)(x))
        (a+b)*B[x[]]
    """
    rank = 9

    def __init__(self, vars):
        """
        EXAMPLES::

            sage: F = sage.combinat.free_prelie_algebra.PreLieFunctor(['x','y'])
            sage: F
            PreLie[x,y]
            sage: F(ZZ)
            Free PreLie algebra on 2 generators ['x', 'y']  over Integer Ring
        """
        Functor.__init__(self, Rings(), Magmas())
        self.vars = vars

    def _apply_functor(self, R):
        """
        Apply the functor to an object of ``self``'s domain.

        EXAMPLES::

            sage: R = algebras.FreePreLie(ZZ, 'x,y,z')
            sage: F = R.construction()[0]; F
            PreLie[x,y,z]
            sage: type(F)
            <class 'sage.combinat.free_prelie_algebra.PreLieFunctor'>
            sage: F(ZZ)          # indirect doctest
            Free PreLie algebra on 3 generators ['x', 'y', 'z'] over Integer Ring
        """
        return FreePreLieAlgebra(R, self.vars)

    def _apply_functor_to_morphism(self, f):
        """
        Apply the functor ``self`` to the ring morphism `f`.

        TESTS::

            sage: R = algebras.FreePreLie(ZZ, 'x').construction()[0]
            sage: R(ZZ.hom(GF(3)))  # indirect doctest
            Generic morphism:
              From: Free PreLie algebra on one generator ['x'] over Integer Ring
              To:   Free PreLie algebra on one generator ['x'] over Finite Field of size 3
        """
        dom = self(f.domain())
        codom = self(f.codomain())

        def action(x):
            return codom._from_dict({a: f(b)
                                     for a, b in iteritems(x.monomial_coefficients())})
        return dom.module_morphism(function=action, codomain=codom)

    def __eq__(self, other):
        """
        EXAMPLES::

            sage: F = algebras.FreePreLie(ZZ, 'x,y,z').construction()[0]
            sage: G = algebras.FreePreLie(QQ, 'x,y,z').construction()[0]
            sage: F == G
            True
            sage: G == loads(dumps(G))
            True
            sage: G = algebras.FreePreLie(QQ, 'x,y').construction()[0]
            sage: F == G
            False
        """
        if not isinstance(other, PreLieFunctor):
            return False
        return self.vars == other.vars

    def __mul__(self, other):
        """
        If two PreLie functors are given in a row, form a single PreLie functor
        with all of the variables.

        EXAMPLES::

            sage: F = sage.combinat.free_prelie_algebra.PreLieFunctor(['x','y'])
            sage: G = sage.combinat.free_prelie_algebra.PreLieFunctor(['t'])
            sage: G * F
            PreLie[x,y,t]
        """
        if isinstance(other, IdentityConstructionFunctor):
            return self
        if isinstance(other, PreLieFunctor):
            if set(self.vars).intersection(other.vars):
                raise CoercionException("Overlapping variables (%s,%s)" %
                                        (self.vars, other.vars))
            return PreLieFunctor(other.vars + self.vars)
        elif (isinstance(other, CompositeConstructionFunctor) and
              isinstance(other.all[-1], PreLieFunctor)):
            return CompositeConstructionFunctor(other.all[:-1],
                                                self * other.all[-1])
        else:
            return CompositeConstructionFunctor(other, self)

    def merge(self, other):
        """
        Merge ``self`` with another construction functor, or return None.

        EXAMPLES::

            sage: F = sage.combinat.free_prelie_algebra.PreLieFunctor(['x','y'])
            sage: G = sage.combinat.free_prelie_algebra.PreLieFunctor(['t'])
            sage: F.merge(G)
            PreLie[x,y,t]
            sage: F.merge(F)
            PreLie[x,y]

        Now some actual use cases::

            sage: R = algebras.FreePreLie(ZZ, 'xyz')
            sage: x,y,z = R.gens()
            sage: 1/2 * x
            1/2*B[x[]]
            sage: parent(1/2 * x)
            Free PreLie algebra on 3 generators ['x', 'y', 'z'] over Rational Field

            sage: S = algebras.FreePreLie(QQ, 'zt')
            sage: z,t = S.gens()
            sage: x + t
            B[t[]] + B[x[]]
            sage: parent(x + t)
            Free PreLie algebra on 4 generators ['z', 't', 'x', 'y'] over Rational Field
        """
        if isinstance(other, PreLieFunctor):
            if self.vars == other.vars:
                return self
            ret = list(self.vars)
            cur_vars = set(ret)
            for v in other.vars:
                if v not in cur_vars:
                    ret.append(v)
            return PreLieFunctor(Alphabet(ret))
        else:
            return None

    def _repr_(self):
        """
        TESTS::

            sage: algebras.FreePreLie(QQ,'x,y,z,t').construction()[0]
            PreLie[x,y,z,t]
        """
        return "PreLie[%s]" % ','.join(self.vars)