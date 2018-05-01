from optparse import OptionParser
import viff.reactor
viff.reactor.install()
from twisted.internet import reactor

from viff.field import GF
from viff.runtime import (Runtime, create_runtime, make_runtime_class,
                          gather_shares)
from viff.config import load_config
from viff.util import dprint, find_prime, rand
from fft import fft
import sys
from helperfunctions import interpolate_poly

class Protocol:

    def __init__(self, runtime, field, b):
        print("Connected to all parties.")

        players = runtime.players.keys()
        random_values = self.__generate_initial_random_values(field, b)

        random_value_shares = []
        for random_value in random_values:
            random_value_shares.extend(runtime.shamir_share(players, field,
                                                                random_value))

        xpoints = map(field, range(1, len(random_value_shares) + 1))
        coordinates = zip(xpoints, random_value_shares)
        coefficients = interpolate_poly(coordinates, myone=1)

        fft_output = fft(coefficients, Zp=field, n = 256, seed = 1041)

        shares = map(runtime.open, fft_output)
        shares = gather_shares(shares)
        shares.addCallback(self.__view_shares)

        runtime.schedule_callback(shares, lambda _: runtime.synchronize())
        runtime.schedule_callback(shares, lambda _: runtime.shutdown())

    def __generate_initial_random_values(self, field, b):
        return [rand.randint(0, field.modulus - 1) for _ in range(b)]

    def __view_shares(self, output):
        print output

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

    # Load configuration file.
    id, players = load_config(args[0])

    pre_runtime = create_runtime(id, players, options.threshold, options)

    Zp = GF(0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001)
    b = int(sys.argv[3])

    pre_runtime.addCallback(Protocol, Zp, b)
    pre_runtime.addErrback(errorHandler)

    # Start the Twisted event loop.
    reactor.run()