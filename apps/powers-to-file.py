from optparse import OptionParser
import viff.reactor
viff.reactor.install()
from twisted.internet import reactor
from viff.active import ActiveRuntime
from viff.field import GF
import time
from viff.runtime import create_runtime, gather_shares, make_runtime_class, Share
from viff.comparison import Toft05Runtime
from viff.config import load_config
from viff.util import rand, find_prime
from viff.active import BasicActiveRuntime, TriplesHyperinvertibleMatricesMixin
import random
import sys

def k_powers_of(b, k):
    bs = [b] * k
    for i in range(1,len(bs)):
        bs[i] = bs[i-1] * b
    return bs

class Protocol:

    def __init__(self, runtime, field, read_mode):
        self.runtime = runtime
        self.field = field

        if not read_mode:
            # Number of powers to compute
            modulus = field.modulus
            # a = random.randint(1, field.modulus - 1)
            a = 5
            k = 8
            b = 2
            if runtime.id == 1:
                a_share = runtime.shamir_share([1], field, a)
                b_share = runtime.shamir_share([1], field, b)
            else:
                a_share = runtime.shamir_share([1], field)
                b_share = runtime.shamir_share([1], field)

            bs_shares = [b_share] * k
            for i in range(1, k):
                bs_shares[i] = bs_shares[i-1] * b
            a_minus_b = a_share - b_share
            a_minus_b = runtime.open(a_minus_b)
            all_shares = [a_share, a_minus_b] + bs_shares

            # all_shares = map(runtime.open, all_shares)
            all_shares = gather_shares(all_shares)
            # all_shares.addCallback(self.view)
            all_shares.addCallback(self.write_to_file, modulus, k)
        else:
            all_shares = self.read_from_file()
            all_shares = map(runtime.open, all_shares)
            all_shares = gather_shares(all_shares)
            all_shares.addCallback(self.view)

        runtime.schedule_callback(all_shares, lambda _: runtime.synchronize())
        runtime.schedule_callback(all_shares, lambda _: runtime.shutdown())

    def view(self, results):
        print results

    def read_from_file(self):
        with open("shares-"+str(self.runtime.id)+".output", "r") as handle:
            elements = handle.readlines()
            elements = map(field, [int(i.strip()) for i in elements])
            # print elements
            return [Share(self.runtime, self.field, i) for i in elements]

    def write_to_file(self, shares, modulus, k):
        # print shares
        lines = [modulus, shares[0].value, shares[1].value, k] + [i.value for i in shares[2:]]
        # print lines
        with open("shares-"+str(self.runtime.id)+".input", "w") as handle:
            for line in lines:
                handle.write("{}\n".format(line))

def errorHandler(failure):
    print("Error: %s" % failure)

# Parse command line arguments.
parser = OptionParser()
Toft05Runtime.add_options(parser)
options, args = parser.parse_args()

if len(args) == 0:
    parser.error("you must specify a config file")
else:
    id, players = load_config(args[0])

# Create a deferred Runtime and ask it to run our protocol when ready.
runtime_class = make_runtime_class(runtime_class=BasicActiveRuntime,
    mixins=[TriplesHyperinvertibleMatricesMixin])
pre_runtime = create_runtime(id, players, 1, options, runtime_class=runtime_class)
# Order of MNT224
field = GF(15028799613985034465755506450771561352583254744125520639296541195021)
read_mode = True if sys.argv[3] == "0" else False
pre_runtime.addCallback(Protocol, field, read_mode)
pre_runtime.addErrback(errorHandler)

# Start the Twisted event loop.
reactor.run()