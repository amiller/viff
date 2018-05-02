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
from ShareSerilializer import write_to_file

import sys
sys.setrecursionlimit(2000000)

def record_start():
    global start
    start = time.time()
    print "*" * 64
    print "Started"


def record_stop():
    stop = time.time()
    print
    print "Total time used: %.3f sec" % (stop-start)
    print "*" * 64


def get_initial_values(runtime, Zp, k, target):
    initial_random_value = 2
    first_row = [0 for _ in range(k+1)]

    value_to_share = target if runtime.id == 1 else None
    secret = runtime.shamir_share([1], Zp, value_to_share)

    values_to_share = [0, initial_random_value] if runtime.id == 1 else [None]*2
    first_row[0] = runtime.shamir_share([1], Zp, values_to_share[0])
    first_row[1] = runtime.shamir_share([1], Zp, values_to_share[1])

    # Initialize first row with the precomputed powers
    for i in range(2, k + 1):
        first_row[i] = first_row[i - 1] * first_row[1]

    # Consume one beaver triple here
    ab_product = secret * first_row[1]

    prefix = runtime.open(secret - first_row[1])

    shares = [prefix, secret, ab_product] + [first_row[i] for i in range(1, k + 1)]
    return shares

def calculation_ready(results):
    print "Ready to print!"
    print results

class Protocol:

    def __init__(self, runtime):
        self.runtime = runtime
        self.Zp = GF(find_prime(2**64))

        # Number of powers to compute
        k = 64

        # Values of which the powers need to be computed
        targets = range(3, 10)
        self.iterations_completed = 0
        self.total_iterations = len(targets)

        for target in targets:
            initial_values = get_initial_values(runtime, self.Zp, k, target)
            # print "Length of initial values: ", len(initial_values)
            result = gather_shares(initial_values)
            result.addCallback(self.preprocess_ready, k, target)


    def preprocess_ready(self, results, k, target):
        print "Ready for preprocessing for ", target

        prefix = results[0]

        matrix = [[0 for _ in range(k + 1)] for _ in range(k + 1)]
        for i in range(1, k + 1):
            matrix[0][i] = results[i+2]
        matrix[1][0] = results[1]
        matrix[1][1] = results[2]

        # print "First row:", matrix[0]
        # print "Second row:", matrix[1]
        # print "K:", k

        record_start()

        for m in range(2, k + 1):
            for n in range(0, m):
                if m == 2 and n == 1:
                    print "[ab] already calculated!"
                else:
                    if (m - n) != 1 :
                        sum_result = 0
                        for p in range(0, m - n):
                            sum_result = sum_result + matrix[m-n-1-p][n+p]
                        matrix[m-n][n] = prefix * sum_result + matrix[0][m]
                    else:
                        sum_result = 0
                        for p in range(0, n):
                            sum_result = sum_result + matrix[m-n+p][n-1-p]
                        matrix[m-n][n] = (-1) * prefix * sum_result + matrix[m][0]

        print "Calculation finished!"

        record_stop()
        final_field_elements = [matrix[i][0] for i in range(1, k + 1)]
        write_to_file(final_field_elements, self.runtime, self.Zp, suffix=str(target)+"-")
        print "Reconstruction finished for", target
        print "#"*64
        self.iteration_complete()


    def iteration_complete(self):
        self.iterations_completed += 1
        # print "#"*30, self.iterations_completed, self.total_iterations
        if self.iterations_completed == self.total_iterations:
            self.runtime.shutdown()


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
pre_runtime.addCallback(Protocol)
pre_runtime.addErrback(errorHandler)

# Start the Twisted event loop.
reactor.run()