from optparse import OptionParser
import viff.reactor
viff.reactor.install()
from twisted.internet import reactor

from viff.field import GF
from viff.runtime import (Runtime, create_runtime, make_runtime_class,
                          gather_shares)
from viff.config import load_config
from viff.util import dprint, find_prime, rand

def _generate_triple(field):
    a = rand.randint(0, field.modulus - 1)
    b = rand.randint(0, field.modulus - 1)
    c = a * b
    return a,b,c

#TODO These are temporary and are starting triples for the TripleRefinement
# process. Only for testing.
precomputed_triples = [[2, 3, 6],
                       [2, 2, 4],
                       [3, 8, 24],
                       [4, 6, 24],
                       [5, 7, 35],
                       [2, 8, 16],
                       [2, 9, 18]]

class Protocol:

    def __init__(self, runtime, field):
        print("Connected to all parties.")
        self.runtime = runtime
        self.field = field

        m, t, k, d = self.get_initial_parameters()

        #a, b, c = precomputed_triples[runtime.id - 1]
        a, b, c = _generate_triple(field)

        # Step 1
        a, b, c, x, y, z = self.rename_and_unpack_inputs(a, b, c, d)

        # Step 2
        alpha = self.get_alpha(a, b, c)

        # Step 3
        a_remaining, b_remaining, a_alpha_values, b_alpha_values = (self.
                get_extrapolated_values(a, b, d, alpha, k))

        # Step 4
        c_remaining = self.batch_beaver(a_remaining, b_remaining, x, y, z)

        # Step 5
        c.extend(c_remaining)
        c_alpha_values = self.interpolate_and_evaluate_at_multiple(range(1,
            2*d+2), c, range(alpha, alpha+k))

        # Collect final output
        final_triples = []
        final_triples.extend(a_alpha_values)
        final_triples.extend(b_alpha_values)
        final_triples.extend(c_alpha_values)

        final_triples = map(runtime.open, final_triples)
        shares = gather_shares(final_triples)
        shares.addCallback(self.verify_triples)

        runtime.schedule_callback(shares, lambda _: runtime.synchronize())
        runtime.schedule_callback(shares, lambda _: runtime.shutdown())

    def verify_triples(self, triples):
        print("FINAL TRIPLES: ", triples)
        k = len(triples)/3
        for i in range(k):
            assert triples[i] * triples[i+k] == triples[i+2*k]

    def get_initial_parameters(self):
        # List of all participating players
        players = self.runtime.players.keys()

        # Initialize the parameters
        m = len(players)
        t = self.runtime.options.threshold
        k = (m+1)//2 - t
        d = (k+t-1)
        return m, t, k, d

    def rename_and_unpack_inputs(self, a, b, c, d):
        a = self.runtime.shamir_share(players, self.field, a)
        b = self.runtime.shamir_share(players, self.field, b)
        c = self.runtime.shamir_share(players, self.field, c)

        x, y, z = a[d+1:], b[d+1:], c[d+1:]
        a, b, c = a[:d+1], b[:d+1], c[:d+1]

        return a, b, c, x, y, z

    def get_alpha(self, a, b, c):
        #TODO Change this to hash of a, b, c
        return 219

    def get_extrapolated_values(self, a, b, d, alpha, k):
        a_remaining = (self.interpolate_and_evaluate_at_multiple(range(1, d+2),
            a, range(d+2, 2*d+2)))
        b_remaining = (self.interpolate_and_evaluate_at_multiple(range(1, d+2),
            b, range(d+2, 2*d+2)))

        a_alpha_values = (self.interpolate_and_evaluate_at_multiple(range(1,
            d+2), a, range(alpha, alpha+k)))
        b_alpha_values = (self.interpolate_and_evaluate_at_multiple(range(1,
            d+2),b, range(alpha, alpha+k)))

        return a_remaining, b_remaining, a_alpha_values, b_alpha_values

    def batch_beaver(self, a_values, b_values, x_values, y_values, z_values):
        c_values = []
        for a, b, x, y, z in zip(a_values, b_values, x_values, y_values,
                                 z_values):
            d = a - x
            e = b - y

            d = self.runtime.open(d)
            e = self.runtime.open(e)

            c = d*e + d*y + e*x + z
            c_values.append(c)

        return c_values

    def interpolate_and_evaluate_at_multiple(self, x_values, y_values,
                                             k_values):
        # print("d+2 to 2*d+1 =>", k_values)
        # print("X LEN:", len(x_values))

        results = []
        for k in k_values:
            results.append(self.__interpolate_and_evaluate_at_k(x_values,
                                                                y_values, k))
        return results

    def __interpolate_and_evaluate_at_k(self, x_values, y_values, k):
        # print("X", x_values)
        # print("Y", len(y_values))

        assert len(x_values) == len(y_values)
        n = len(x_values)
        y = 0
        for i in range(n):
            product = 1
            for j in range(n):
                if i != j:
                    product *= (self.field(k - x_values[j]) /
                                (x_values[i] - x_values[j]))

            # print("Product", product)
            # print(y_values[i])
            y = y + (y_values[i] * product)

        # dprint("Y VALUE: %s", self.runtime.output(y))
        return y


def errorHandler(failure):
    print("Error: %s" % failure)


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

pre_runtime = create_runtime(id, players, options.threshold, options)
pre_runtime.addCallback(Protocol, Zp)
pre_runtime.addErrback(errorHandler)

# Start the Twisted event loop.
reactor.run()
