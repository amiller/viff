#!/usr/bin/env python



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
from viff.comparison import Toft05Runtime
from viff.config import load_config
from viff.util import rand, find_prime
from viff.active import BasicActiveRuntime, TriplesHyperinvertibleMatricesMixin

import sys

import os
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
    global start
    stop = time.time()
    print
    print "Total time used: %.3f sec" % (stop-start)
    start = stop
    '''
    if runtime.id == 1:
        f = open('time.txt', 'w')
        f.write(stop-start)
        f.close()
    '''
    print "*" * 64
    #return x



class OnlineProtocol:

    def __init__(self, runtime,k,batch):
		self.k = k
		self.runtime = runtime
		self.batch = batch
		self.inputs = [[0 for _ in range(self.k)] for _ in range(self.batch)]
		self.p = find_prime(2**256, blum=True)
		self.Zp = GF(self.p)
		self.a_minus_b = [[0 for _ in range(self.k)] for _ in range(self.batch)]
		self.precomputed_powers = [[0 for _ in range(self.k )] for _ in range(self.k)]
		record_start()
		
		self.load_input_from_file(self.k,self.p,self.batch)
		# TODO: for simplicity, if there are multiple batches, they will share the same group of precomputed shares.
		for i in range(self.k):
			#TODO: here for testing we use same random b, in the future we need to change this to:
			#self.load_share_from_file(self.k,self.p,i)
			self.load_share_from_file(self.k,self.p,i)
		print "load input finished"
		record_stop()
		for b in range(self.batch):
			for i in range(self.k):
				self.a_minus_b[b][i] = self.runtime.open(self.inputs[b][i] - self.precomputed_powers[i][0])
		#print self.a_minus_b
		shares = []
		for i in self.a_minus_b:
			shares = shares + i
		result = gather_shares(shares)
		result.addCallback(self.create_output,self.batch)
		#self.runtime.schedule_callback(results, lambda _: self.runtime.synchronize())
	        #self.runtime.schedule_callback(results, lambda _: self.runtime.shutdown())

    def plainprint(self,result):
		print "done!"
		#print result

    def load_input_from_file(self,k,p,batch):
    	for batchiter in range(1, batch + 1):
			filename = "party" + str(self.runtime.id) + "_butterfly_online_batch" + str(batchiter)
			
			FD = open(filename, "r")
			line = FD.readline()
			#if int(line) != k:
			#	print "k dismatch!! k in file is %d"%(int(line))
			line = FD.readline()
			#if int(line) != p:
			#	print "prime dismatch!! prime in file is %d"%(int(line))
			self.Zp = GF(p)

			line = FD.readline()
			i = 0
			while line and i < self.k:
				#print i
				self.inputs[batchiter-1][i] = Share(self.runtime,self.Zp,self.Zp(int(line)))

				line = FD.readline()  
				i = i + 1

    def load_share_from_file(self,k,p,row,cnt = 1):
		#TODO: 
		#filename = "precompute-party%d-%d.share" % (self.runtime.num_players, self.runtime.threshold, self.k, self.runtime.id,cnt)
		filename = "precompute-party%d.share" % (self.runtime.id)
		FD = open(filename, "r")
		line = FD.readline()
		#if int(line) != p:
		#	print "p dismatch!! p in file is %d"%(int(line))
		line = FD.readline()
		#if int(line) != k:
		#	print "k dismatch!! k in file is %d"%(int(line))
		self.Zp = GF(p)

		line = FD.readline()
		i = 0
		while line and i < self.k:
			#print i
			self.precomputed_powers[row][i] = Share(self.runtime,self.Zp,self.Zp(int(line)))

			line = FD.readline()  
			i = i + 1

    def create_output(self,result,batch):
		print "a-b calculation finished"
		record_stop()
		path = "party" + str(self.runtime.id) + "-powermixing-online-phase1-output"
		folder = os.path.exists(path)  
		if not folder:                  
			os.makedirs(path) 
		for b in range(self.batch):
			print "what"
			for i in range(self.k):
				print "how%d%d"%(b,i)
				filename = "party" + str(self.runtime.id) + "-powermixing-online-phase1-output/powermixing-online-phase1-output" + str(i+1) + "-batch" + str(b+1)

				FD = open(filename, "w")
				print "how!"
				content =  str(self.p) + "\n" + str(self.inputs[b][i].result)[1:-1] + "\n" + str(self.a_minus_b[b][i].result)[1:-1] + "\n" + str(self.k) + "\n"
				print "how!!"
				ll = 0
				for share in self.precomputed_powers[i]:
					content = content + str(share.result)[1:-1] + "\n"
					print "how%d"%(ll)
					ll=ll+1
				print "how!!!"
				FD.write(content)
				FD.close()
		print "output to file finished"
		record_stop()
		results = self.runtime.synchronize()
		self.runtime.schedule_callback(results, lambda _: self.runtime.shutdown())

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
k = int(sys.argv[3])
print k
batch = int(sys.argv[4])
print batch
# Create a deferred Runtime and ask it to run our protocol when ready.
runtime_class = make_runtime_class(runtime_class=BasicActiveRuntime,
    mixins=[TriplesHyperinvertibleMatricesMixin])
pre_runtime = create_runtime(id, players, 1, options, runtime_class=runtime_class)
pre_runtime.addCallback(OnlineProtocol,k,batch)
pre_runtime.addErrback(errorHandler)

# Start the Twisted event loop.
reactor.run()