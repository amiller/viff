# -*- coding: utf-8 -*-
#
# Copyright 2007, 2008 VIFF Development Team.
#
# This file is part of VIFF, the Virtual Ideal Functionality Framework.
#
# VIFF is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License (LGPL) as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# VIFF is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with VIFF. If not, see <http://www.gnu.org/licenses/>.

u"""Methods for pseudo-random secret sharing. Normal Shamir sharing
(see the :mod:`viff.shamir` module) requires secure channels between
the players for distributing shares. With pseudo-random secret sharing
one can share a secret using a single broadcast instead.

PRSS relies on each player having access to a set of previously
distributed pseudo-random functions (PRFs) --- or rather the seeds for
such functions. In VIFF, such seeds are generated by
:func:`viff.config.generate_configs`. The
:meth:`viff.config.Player.prfs` and
:meth:`viff.config.Player.dealer_prfs` methods give access to the
PRFs.

In this module the function :func:`prss` is used to calculate shares
for a pseudo-random number. The :func:`generate_subsets` function is a
general utility for generating subsets of a specific size.

The code is based on the paper "Share Conversion, Pseudorandom
Secret-Sharing and Applications to Secure Computation" by Ronald
Cramer, Ivan Damgård, and Yuval Ishai in Proc. of TCC 2005, LNCS 3378.
`Download <http://www.cs.technion.ac.il/~yuvali/pubs/CDI05.ps>`__.
"""

__docformat__ = "restructuredtext"


import sha
from math import ceil
from binascii import hexlify

from gmpy import numdigits

from viff import shamir
from viff.field import GF256
from viff.util import fake

def random_replicated_sharing(j, prfs, key):
    """Return a replicated sharing of a random number.

    The shares are for player *j* based on the pseudo-random functions
    given in *prfs* (a mapping from subsets of players to :class:`PRF`
    instances). The *key* is used when evaluating the PRFs. The result
    is a list of ``(subset, share)`` pairs.
    """
    # The PRFs contain the subsets we need, plus some extra in the
    # case of dealer_keys. That is why we have to check that j is in
    # the subset before using it.
    return [(s, prf(key)) for (s, prf) in prfs.iteritems() if j in s]

#: Cache the coefficients used to construct the share. They depend on the field,
#: the player concerned, the total number of players, and the subset.
_f_in_j_cache = {}

def convert_replicated_shamir(n, j, field, rep_shares):
    """Convert a set of replicated shares to a Shamir share.

    The conversion is done for player *j* (out of *n*) and will be
    done over *field*.
    """
    global _f_in_j_cache
    result = 0
    all = frozenset(range(1, n+1))
    for subset, share in rep_shares:
        # TODO: should we cache the f_in_j values?
        # Yes, we probably should.
        if ((field, n, j, subset) in _f_in_j_cache):
            f_in_j = _f_in_j_cache[(field, n, j, subset)]
        else:
            points = [(field(x), 0) for x in all-subset]
            points.append((0, 1))
            f_in_j = shamir.recombine(points, j)
            _f_in_j_cache[(field, n, j, subset)] = f_in_j
        result += share * f_in_j
    return result

@fake(lambda n, j, field, prfs, key: field(7))
def prss(n, j, field, prfs, key):
    """Return a pseudo-random secret share for a random number.

    The share is for player *j* based on the pseudo-random functions
    given in *prfs* (a mapping from subsets of players to :class:`PRF`
    instances). The *key* is used when evaluating the PRFs.

    An example with (n,t) = (3,1) and a modulus of 31:

    >>> from field import GF
    >>> Zp = GF(31)
    >>> prfs = {frozenset([1,2]): PRF("a", 31),
    ...         frozenset([1,3]): PRF("b", 31),
    ...         frozenset([2,3]): PRF("c", 31)}
    >>> prss(3, 1, Zp, prfs, "key")
    {22}
    >>> prss(3, 2, Zp, prfs, "key")
    {20}
    >>> prss(3, 3, Zp, prfs, "key")
    {18}

    We see that the sharing is consistent because each subset of two
    players will recombine their shares to ``{24}``.
    """
    rep_shares = random_replicated_sharing(j, prfs, key)
    return convert_replicated_shamir(n, j, field, rep_shares)

@fake(lambda n, j, field, prfs, key: (field(7), GF256(1)))
def prss_lsb(n, j, field, prfs, key):
    """Share a pseudo-random number and its least significant bit.

    The random number is shared over *field* and its least significant
    bit is shared over :class:`viff.field.GF256`. It is important the
    *prfs* generate numbers much less than the size of *field* -- we
    must be able to do an addition for each PRF without overflow in
    *field*.

    >>> from field import GF
    >>> Zp = GF(23)
    >>> prfs = {frozenset([1,2]): PRF("a", 7),
    ...         frozenset([1,3]): PRF("b", 7),
    ...         frozenset([2,3]): PRF("c", 7)}
    >>> prss_lsb(3, 1, Zp, prfs, "key")
    ({0}, [140])
    >>> prss_lsb(3, 2, Zp, prfs, "key")
    ({15}, [3])
    >>> prss_lsb(3, 3, Zp, prfs, "key")
    ({7}, [143])

    We see that the random value must be ``{8}`` and so the least
    significant bit must be ``[0]``. We can check this by recombining
    any two of the three shares:

    >>> from shamir import recombine
    >>> recombine([(GF256(1), GF256(140)), (GF256(2), GF256(3))])
    [0]
    >>> recombine([(GF256(2), GF256(3)),   (GF256(3), GF256(143))])
    [0]
    >>> recombine([(GF256(3), GF256(143)), (GF256(1), GF256(140))])
    [0]
    """
    rep_shares = random_replicated_sharing(j, prfs, key)
    lsb_shares = [(s, r & 1) for (s, r) in rep_shares]
    return (convert_replicated_shamir(n, j, field, rep_shares),
            convert_replicated_shamir(n, j, GF256, lsb_shares))

@fake(lambda n, t, j, field, prfs, key: field(0))
def prss_zero(n, t, j, field, prfs, key):
    """Return a pseudo-random secret zero-sharing of degree 2t.

    >>> from field import GF
    >>> Zp = GF(23)
    >>> prfs = {frozenset([1,2]): PRF("a", 7),
    ...         frozenset([1,3]): PRF("b", 7),
    ...         frozenset([2,3]): PRF("c", 7)}
    >>> prss_zero(3, 1, 1, Zp, prfs, "key")
    {16}
    >>> prss_zero(3, 1, 2, Zp, prfs, "key")
    {13}
    >>> prss_zero(3, 1, 3, Zp, prfs, "key")
    {14}

    If we recombine 2t + 1 = 3 shares we can verify that this is
    indeed a zero-sharing:

    >>> from shamir import recombine
    >>> recombine([(Zp(1), Zp(4)), (Zp(2), Zp(0)), (Zp(3), Zp(11))])
    {0}
    """
    # We start by generating t random numbers for each subset. This is
    # very similar to calling random_replicated_sharing t times, but
    # by doing it like this we immediatedly get the nesting we want.
    rep_shares = [(s, [(i+1, prf((key, i))) for i in range(t)])
                  for (s, prf) in prfs.iteritems() if j in s]

    # We then proceed with the zero-sharing. The first part is like in
    # a normal PRSS.
    result = 0
    all = frozenset(range(1, n+1))
    for subset, shares in rep_shares:
        points = [(field(x), 0) for x in all-subset]
        points.append((0, 1))
        f_in_j = shamir.recombine(points, j)
        # Unlike a normal PRSS we have an inner sum where we use a
        # degree 2t polynomial g_i which we choose as
        #
        #   g_i(x) = f(x) * x**j
        #
        # since we already have the degree t polynomial f at hand. The
        # g_i are all linearly independent as required by the protocol
        # and can thus be used for the zero-sharing.
        for i, share in shares:
            g_i_in_j = f_in_j * j**i
            result += share * g_i_in_j
    return result

def generate_subsets(orig_set, size):
    """Generates the set of all subsets of a specific size.

    >>> generate_subsets(frozenset('abc'), 2)
    frozenset([frozenset(['c', 'b']), frozenset(['a', 'c']), frozenset(['a', 'b'])])

    Generating subsets larger than the initial set return the empty
    set:

    >>> generate_subsets(frozenset('a'), 2)
    frozenset([])
    """
    if len(orig_set) > size:
        result = set()
        for element in orig_set:
            result.update(generate_subsets(orig_set - set([element]), size))
        return frozenset(result)
    elif len(orig_set) == size:
        return frozenset([orig_set])
    else:
        return frozenset()

# Generating 100,000 bytes like this:
#
# x = PRF("a", 256)
# for i in xrange(100000):
#     sys.stdout.write(chr(x(i)))
#
# and piping them into ent (http://www.fourmilab.ch/random/) gives:
#
# Entropy = 7.998124 bits per byte.
#
# Optimum compression would reduce the size
# of this 100000 byte file by 0 percent.
#
# Chi square distribution for 100000 samples is 260.10, and randomly
# would exceed this value 50.00 percent of the times.
#
# Arithmetic mean value of data bytes is 127.6850 (127.5 = random).
# Monte Carlo value for Pi is 3.156846274 (error 0.49 percent).
# Serial correlation coefficient is 0.000919 (totally uncorrelated = 0.0).
class PRF(object):
    """Models a pseudo random function (a PRF).

    The numbers are based on a SHA1 hash of the initial key.

    Each PRF is created based on a key (which should be random and
    secret) and a maximum (which may be public):

    >>> f = PRF("some random key", 256)

    Calling f return values between zero and the given maximum:

    >>> f(1)
    26L
    >>> f(2)
    69L
    >>> f(3)
    217L
    """

    def __init__(self, key, max):
        """Create a PRF keyed with the given key and max.

        The key must be a string whereas the max must be a number.
        Output value will be in the range zero to max, with zero
        included and max excluded.

        To make a PRF what generates numbers less than 1000 do:

        >>> f = PRF("key", 1000)

        The PRF can be evaluated by calling it on some input:

        >>> f("input")
        327L

        Creating another PRF with the same key gives identical results
        since f and g are deterministic functions, depending only on
        the key:

        >>> g = PRF("key", 1000)
        >>> g("input")
        327L

        We can test that f and g behave the same on many inputs:

        >>> [f(i) for i in range(100)] == [g(i) for i in range(100)]
        True

        Both the key and the max is used when the PRF is keyed. This
        means that

        >>> f = PRF("key", 1000)
        >>> g = PRF("key", 10000)
        >>> [f(i) for i in range(100)] == [g(i) for i in range(100)]
        False
        """
        self.max = max

        # Number of bits needed for a number in the range [0, max-1].
        bit_length = numdigits(max-1, 2)

        # Number of whole digest blocks needed.
        blocks = int(ceil(bit_length / 8.0 / sha.digest_size))

        # Number of whole bytes needed.
        self.bytes = int(ceil(bit_length / 8.0))
        # Number of bits needed from the final byte.
        self.bits = bit_length % 8

        self.sha1s = []
        for i in range(blocks):
            # TODO: this construction is completely ad-hoc and not
            # known to be secure...

            # Initial seed is key + str(max). The maximum is included
            # since we want PRF("input", 100) and PRF("input", 1000)
            # to generate different output.
            seed = key + str(max)

            # The i'th generator is seeded with H^i(key + str(max))
            # where H^i means repeated hashing i times.
            for _ in range(i):
                seed = sha.new(seed).digest()
            self.sha1s.append(sha.new(seed))

    def __call__(self, input):
        """Return a number based on input.

        If the input is not already a string, it is hashed (using the
        normal Python hash built-in) and the hash value is used
        instead. The hash value is a 32 bit value, so a string should
        be given if one wants to evaluate the PRF on more that 2**32
        different values.

        >>> prf = PRF("key", 1000)
        >>> prf(1), prf(2), prf(3)
        (501L, 432L, 133L)

        Since prf is a function we can of course evaluate the same
        input to get the same output:

        >>> prf(1)
        501L

        The prf can take arbitrary input:

        >>> prf(("input", 123))
        284L

        Non-string input will be converted with ``str``, which means
        that the input must have a deterministic ``__str__``
        method. This means that hashable instances are probably best.
        """
        # We can only feed str data to sha1 instance, so we must
        # convert the input.
        if not isinstance(input, str):
            input = str(input)

        # There is a chance that we generate a number that is too big,
        # so we must keep trying until we succeed.
        while True:
            # We collect a digest for each keyed sha1 instance.
            digests = []
            for sha1 in self.sha1s:
                # Must work on a copy of the keyed sha1 instance.
                copy = sha1.copy()
                copy.update(input)
                digests.append(copy.digest())

            digest = ''.join(digests)
            random_bytes = digest[:self.bytes]

            # Convert the random bytes to a long by converting it to
            # hexadecimal representation first.
            result = long(hexlify(random_bytes), 16)

            # Shift to get rid of the surplus bits (if needed).
            if self.bits:
                result >>= (8 - self.bits)

            if result < self.max:
                return result
            else:
                # TODO: is this safe? The first idea was to append a
                # fixed string (".") every time, but that makes f("a")
                # and f("a.") return the same number.
                #
                # The final byte of the digest depends on the key
                # which means that it should not be possible to
                # predict it and so it should be hard to find pairs of
                # inputs which give the same output value.
                input += digest[-1]

if __name__ == "__main__":
    import doctest    #pragma NO COVER
    doctest.testmod() #pragma NO COVER
