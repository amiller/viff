"""
Offline Phase for the Powermix protocol.
Input: a secret share [b]
Output: powers of the share [b^2],...,[b^k]
"""

from optparse import OptionParser
import viff.reactor
viff.reactor.install()
from twisted.internet import reactor
from viff.active import ActiveRuntime
from viff.field import GF
import time
from viff.runtime import create_runtime, gather_shares, make_runtime_class, Share
from viff.config import load_config
from viff.util import rand, find_prime
from viff.active import BasicActiveRuntime, TriplesHyperinvertibleMatricesMixin
import random
import sys
sys.setrecursionlimit(2000000)

# Benchmarking
start = 0
def record_start():
    global start
    start = time.time()
    print "*" * 64
    print "Started"

def record_stop():

    stop = time.time()
    print
    print "Total time used: %.3f sec" % (stop-start)
    '''
    if runtime.id == 1:
        f = open('time.txt', 'w')
        f.write(stop-start)
        f.close()
    '''
    print "*" * 64
    #return x

def k_powers_of(b, k):
    bs = [b] + [None] * (k-1)
    for i in range(1,len(bs)):
        bs[i] = bs[i-1] * b
    return bs


# MNT224
#prime = 15028799613985034465755506450771561352583254744125520639296541195021L
# JubJub
#prime = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001L
prime = find_prime(2**256, blum=True)
Zp = GF(prime)



class Protocol:

    def __init__(self, runtime, field, k, B):
        self.runtime = runtime
        self.field = field
        self.k = k
        self.B = B
        print 'k=', k
        print 'batch=', B

        # TODO: fix
        assert B==1, "TODO: B>1 seems to hang..."
        

	    n = self.runtime.num_players
	    t = self.runtime.threshold
        T = n - 2*t

        record_start()

        self.output_shares = [Share(None,field) for _ in range(k * B)]

        # Generate k random values
	for i in range(self.B):
            # Generate a random power
	    r = self.runtime.single_share_random(T,t,field)

            def _random_ready(r,i):
                # Compute all powers
                rs = k_powers_of(r[0], self.k)
                for j,power in enumerate(rs):
                    power.addCallback(self.output_shares[i*self.k+j].callback)
            r.addCallback(_random_ready, i)

        # Wait for all the shares then write to file
	result = gather_shares(self.output_shares)        
	result.addCallback(self.write_to_file, field.modulus, k)
        runtime.schedule_callback(result, lambda _: runtime.synchronize())
        runtime.schedule_callback(result, lambda _: runtime.shutdown())

    def view(self, results):
        print results


    def write_to_file(self, shares, modulus, k):
	record_stop()
        print 'Done!'#, shares
        lines = [modulus, k] + [i.value for i in shares[:]]
        # print lines
	filename = "precompute-party%d.share" % (self.runtime.id)
        with open(filename, "w") as handle:
            for line in lines:
                handle.write("{}\n".format(line))

def errorHandler(failure):
    print("Error: %s" % failure)

# Parse command line arguments.
parser = OptionParser()
BasicActiveRuntime.add_options(parser)
options, args = parser.parse_args()

if len(args) == 0:
    parser.error("you must specify a config file")
else:
    id, players = load_config(args[0])
k = int(sys.argv[3])
print k
# Create a deferred Runtime and ask it to run our protocol when ready.
runtime_class = make_runtime_class(runtime_class=BasicActiveRuntime,
    mixins=[TriplesHyperinvertibleMatricesMixin])
pre_runtime = create_runtime(id, players, 1, options, runtime_class=runtime_class)

pre_runtime.addCallback(Protocol, Zp, k, B=1)
pre_runtime.addErrback(errorHandler)

# Start the Twisted event loop.
reactor.run()
