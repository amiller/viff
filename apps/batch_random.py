from optparse import OptionParser
import viff.reactor
viff.reactor.install()
from twisted.internet import reactor

from viff.field import GF
from viff.runtime import (Runtime, create_runtime, make_runtime_class,
                          gather_shares)
from viff.config import load_config
from viff.util import dprint, find_prime, rand

def polynomial_divide(numerator, denominator):
    temp = numerator
    factors = []
    while len(temp) >= len(denominator):
        diff = len(temp) - len(denominator)
        factor = temp[len(temp) - 1] / denominator[len(denominator) - 1]
        factors.insert(0, factor)
        for i in range(len(denominator)):
            temp[i+diff] = temp[i+diff] - (factor * denominator[i])
        temp = temp[:len(temp)-1]
    return factors

def polynomial_multiply_constant(poly1, c):
    #myzero will be appropriate whether we are in ZR or G
    #myzero = poly1[0] - poly1[0]
    product = [None] * len(poly1)
    for i in range(len(product)):
        product[i] = poly1[i] * c
    return product

def polynomial_add(poly1, poly2):
    #if group == None:
    #myzero = poly2[0] - poly2[0]
    if len(poly1) >= len(poly2):
        bigger = poly1
        smaller = poly2
    else:
        bigger = poly2
        smaller = poly1
    polysum = [None] * len(bigger)
    for i in range(len(bigger)):
        polysum[i] = bigger[i]
        if i < len(smaller):
            polysum[i] = polysum[i] + smaller[i]
    return polysum

def polynomial_multiply(poly1, poly2):
    #if group == None:
    myzero = poly1[0] - poly1[0]
    #myzero = group.random(ZR)*0
    product = [myzero] * (len(poly1) + len(poly2) -1)
    for i in range(len(poly1)):
        temp = polynomial_multiply_constant(poly2, poly1[i])
        while i > 0:
            temp.insert(0,myzero)
            i -= 1
        product = polynomial_add(product, temp)
    return product


def interpolate_poly(coords):
        myone = 1
        myzero = 0
        poly = [myzero] * len(coords)
        for i in range(len(coords)):
            temp = [myone]
            for j in range(len(coords)):
                if i == j:
                    continue
                temp = polynomial_multiply(temp, [ -1 * (coords[j][0] * myone), myone])
                temp = polynomial_divide(temp, [myone * coords[i][0] - myone * coords[j][0]])
            poly = polynomial_add(poly, polynomial_multiply_constant(temp,coords[i][1]))
        return poly


class Protocol:

    def __init__(self, runtime, field, b):
        print("Connected to all parties.")
        self.runtime = runtime
        self.field = field
        self.b = b
        
        players = self.runtime.players.keys()
        random_values = self.__generate_initial_random_values()

        print random_values
        random_value_shares = []
        for random_value in random_values:
            random_value_shares.extend(runtime.shamir_share(
                players, field, random_value))
        
        coords = zip(range(1, len(random_value_shares) + 1), random_value_shares)
        final_triples = interpolate_poly(coords)
        # final_triples = lagrange(range(1, len(random_value_shares)+1), random_value_shares)
        # dprint("Printing %s", runtime.open(final_triples))
        # print coords
        p = map(runtime.open, final_triples)
        shares = gather_shares(p)
        shares.addCallback(self.view_shares)


        # # # print coords
        # final_triples = interpolate_at_x(coords, 1)
        # final_triples = map(runtime.open, final_triples)
        # shares = gather_shares(final_triples)
        # shares.addCallback(self.view_shares)

        runtime.schedule_callback(shares, lambda _: runtime.synchronize())
        runtime.schedule_callback(shares, lambda _: runtime.shutdown())

    def __generate_initial_random_values(self):
        # return [rand.randint(0, self.field.modulus - 1) for _ in range(self.b)]
        return [self.runtime.id**2]

    def view_shares(self, triples):
        print("FINAL SHARES: ", triples)

   

        
def errorHandler(failure):
    print("Error: %s" % failure)

if __name__ == "__main__":
    # Parse command line arguments.
    parser = OptionParser(usage=__doc__)

    parser.set_defaults(modulus=2**100, number=None)

    Runtime.add_options(parser)

    options, args = parser.parse_args()

    if len(args) == 0:
        parser.error("You must specify a config file.")

    Zp = GF(find_prime(options.modulus, blum=True))

    # Load configuration file.
    id, players = load_config(args[0])

    b = 1

    pre_runtime = create_runtime(id, players, options.threshold, options)
    pre_runtime.addCallback(Protocol, Zp, b)
    pre_runtime.addErrback(errorHandler)

    # Start the Twisted event loop.
    reactor.run()
