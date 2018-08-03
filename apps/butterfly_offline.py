#!/usr/bin/env python

# Give a player configuration file as a command line argument or run
# the example with '--help' for help with the command line options.

from optparse import OptionParser
import viff.reactor
viff.reactor.install()
from twisted.internet import reactor
from viff.active import ActiveRuntime
from viff.field import GF
from random import randint
import time
import math
from viff.runtime import create_runtime, gather_shares,Share,make_runtime_class
from viff.config import load_config
from viff.util import rand, find_prime
from viff.active import BasicActiveRuntime, TriplesHyperinvertibleMatricesMixin

import sys
sys.setrecursionlimit(2000000)
# We start by defining the protocol, it will be started at the bottom
# of the file.
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

# MNT224
#prime = 15028799613985034465755506450771561352583254744125520639296541195021L
# JubJub
#prime = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001L
prime = find_prime(2**256, blum=True)
Zp = GF(prime)

# TODO: implement general case of sqrt
#def cipolla(v):
# pass


class OfflineProtocol:
    # this is only for testing generating random -1/1 shares.
    def __init__(self, runtime, k):
	self.k = k
	self.runtime = runtime
	self.random_shares = [0 for i in range(self.k * int(math.log(self.k,2)))]
	self.triggers = [Share(self.runtime,Zp) for i in range(self.k * int(math.log(self.k,2)))]
	self.p = prime
	print self.p
        assert self.p % 4 == 3, "Need efficient square roots"

	n = self.runtime.num_players
	t = self.runtime.threshold
        T = n - 2*t

	record_start()
	for i in range(self.k * int(math.log(self.k,2))):
		r = self.runtime.single_share_random(T,t,GF(self.p))

		def random_ready(r,cnt):
			
			u = r[0] * r[0]
			open_u = self.runtime.open(u)

			open_u.addCallback(self.calculate_share,r[0],cnt)
	        self.runtime.schedule_callback(r, random_ready,i)

	list = [self.triggers[i] for i in range(self.k * int(math.log(self.k,2)))]
	result = gather_shares(list)
	result.addCallback(self.preprocess_ready)
        runtime.schedule_callback(result, lambda _: runtime.synchronize())
        runtime.schedule_callback(result, lambda _: runtime.shutdown())

 
	
        #data = [1,2,3,4,5,6,7,8]
	#result = permutation_component(data,8)
	#print result

    def calculate_share(self,result,r,i):
	#print ""caculating shares
	v = result**((-(self.p+1)/4)%(self.p - 1))
        
	self.random_shares[i] = r * v
	self.triggers[i].callback(1)
	
    def preprocess_ready(self,result):
	print "preprocess_ready"
	self.write_to_file(self.random_shares)
	record_stop()
        #results = self.runtime.synchronize()
        #self.runtime.schedule_callback(results, lambda _: self.runtime.shutdown())

	'''
	for i in range(self.k * int(math.log(self.k,2))): 
		open_1= self.runtime.open(self.random_shares[i])
		
		open_1.addCallback(self.plainprint)
	'''

    def write_to_file(self, shares):
	#print "here"
	filename = "precompute-butterfly-N%d-t%d-k%d-id%d.share" % (self.runtime.num_players, self.runtime.threshold, self.k, self.runtime.id)
	
	FD = open(filename, "w")

	content = str(self.k) + "\n" + str(self.p) + "\n"
	for share in shares:
		content = content + str(share.result)[1:-1] + "\n"
	FD.write(content)
	FD.close()

    def __generate_initial_random_values(self, field, b):
        return [rand.randint(0, field.modulus - 1) for _ in range(b)]

    def plainprint(self,result):

	print result

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
# Create a deferred Runtime and ask it to run our protocol when ready.
runtime_class = make_runtime_class(runtime_class=BasicActiveRuntime,
    mixins=[TriplesHyperinvertibleMatricesMixin])
pre_runtime = create_runtime(id, players, 1, options, runtime_class=runtime_class)
pre_runtime.addCallback(OfflineProtocol,k)
pre_runtime.addErrback(errorHandler)

# Start the Twisted event loop.
reactor.run()
