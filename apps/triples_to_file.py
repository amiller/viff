from optparse import OptionParser
import viff.reactor
viff.reactor.install()
from twisted.internet import reactor

from viff.field import GF
from viff.runtime import (Runtime, create_runtime, make_runtime_class,
                          gather_shares, Share)
from viff.config import load_config
from viff.active import BasicActiveRuntime, TriplesHyperinvertibleMatricesMixin

import random
import sys
import cPickle as pickle
import time


class Protocol:
    def __init__(self, runtime, field):
        self.runtime = runtime
        self.field = field

        print("Connected to all parties.")
        
        shares = []
        t1 = time.time()
        for _ in range(1000):
            shares.extend(self.runtime.get_triple(field)[0])
        t2 = time.time()
        shares = map(runtime.open, shares)
        shares = gather_shares(shares)
        t3 = time.time()
        print runtime.id, "Generation time: ", t2-t1
        print runtime.id, "Gathering time: ", t3-t1
        shares.addCallback(self.verify_and_view_triples)

        runtime.schedule_callback(shares, lambda _: runtime.synchronize())
        runtime.schedule_callback(shares, lambda _: runtime.shutdown())

    def verify_and_view_triples(self, triples):
        for i in range(0, len(triples), 3):
            product = triples[i].value * triples[i+1].value
            assert self.field(product) == triples[i+2].value
            # print triples[i], triples[i+1], triples[i+2]

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
    print "THRESHOLD", options.threshold
    id, players = load_config(args[0])
    runtime_class = make_runtime_class(runtime_class=BasicActiveRuntime,
        mixins=[TriplesHyperinvertibleMatricesMixin])
    pre_runtime = create_runtime(id, players, options.threshold, options,
        runtime_class=runtime_class)

    # Jubjub.15
    Zp = GF(0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001)
    # Zp = GF(7)

    pre_runtime.addCallback(Protocol, Zp)
    pre_runtime.addErrback(errorHandler)

    # Start the Twisted event loop.
    reactor.run()