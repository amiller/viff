#!/usr/bin/env python

# Copyright 2017   AsycMix team

from optparse import OptionParser
import viff.reactor
viff.reactor.install()
from twisted.internet import reactor

from viff.field import GF
from viff.runtime import create_runtime, gather_shares
from viff.config import load_config
from viff.util import rand
from viff.comparison import ComparisonToft05Mixin, ComparisonToft05Mixin
from viff.active import BasicActiveRuntime, TriplesPRSSMixin, BrachaBroadcastMixin, ActiveRuntime

class MyRuntime(TriplesPRSSMixin, BrachaBroadcastMixin, BasicActiveRuntime):
#class MyRuntime(ActiveRuntime):
    pass

Zp = GF(0xffffffffffffffffffffffffffffffffffffffffffffead2fd381eb509800197L)
#Zp = GF(11)

# Parse command line arguments.
parser = OptionParser()
MyRuntime.add_options(parser)

# The number of transactions to mix
parser.add_option("-K", "--ktx", type="int", default=8,
                  help="number of elements to shuffle")

options, args = parser.parse_args()
k = options.ktx

if len(args) == 0:
    parser.error("you must specify a config file")
else:
    id, players = load_config(args[0])


def protocol(runtime):

    def _swap(in_arr, out_arr, i, j):
        assert i != j
        assert len(in_arr) == len(out_arr)
        assert 0 <= i < len(in_arr)
        r = runtime.prss_share_random(Zp, binary=True) # share of 0/1
        out_arr[i] = (1-r) * in_arr[i] + (  r) * in_arr[j]
        out_arr[j] = (  r) * in_arr[i] + (1-r) * in_arr[j]
        
    def shuffle(arr, stride=1):
        k = len(arr)
        assert k == 1<<(k.bit_length()-1), "arr must be power-of-2"
        if stride == k: return arr # base case
        arr_new = [None] * k
        for strt in range(0, k, 2 * stride):
            for i in range(strt, strt + stride):
                j = i + stride
                _swap(arr, arr_new, i, j)
        return shuffle(arr_new, stride * 2)
        

    # For now only Player 1 is responsible for sharing the transactions
    if runtime.id == 1:
        print 'hi'
        myvalues = [rand.randint(1,100) for _ in range(k)]
        print "I am ", runtime.id, "and my values are:", myvalues
    else:
        myvalues = [None] * k

    # Share the input values
    values = [runtime.shamir_share([1], Zp, myvalue) for myvalue in myvalues]
    # Shuffled
    shuffled_values = shuffle(values)
    #shuffled_values = map(runtime.open,values)
    print "ok"
    print shuffled_values
    results = gather_shares(map(runtime.open,shuffled_values))

    def results_ready(results):
        print 'results:', results

    results.addCallback(results_ready)
    runtime.schedule_callback(results, lambda _: runtime.synchronize())
    runtime.schedule_callback(results, lambda _: runtime.shutdown())


# Create a deferred Runtime and ask it to run our protocol when ready.
pre_runtime = create_runtime(id, players, 1, options, MyRuntime)
pre_runtime.addCallback(protocol)

reactor.run()
