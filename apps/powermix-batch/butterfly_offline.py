#!/usr/bin/env python

# Copyright 2007, 2008 VIFF Development Team.
#
# This file is part of VIFF, the Virtual Ideal Functionality Framework.
#
# VIFF is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License (LGPL) as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# VIFF is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with VIFF. If not, see <http://www.gnu.org/licenses/>.

# This example is a tribute to the original example of secure
# multi-party computation by Yao in 1982. In his example two
# millionaires meet in the street and they want to securely compare
# their fortunes. They want to do so without revealing how much they
# own to each other. This problem would be easy to solve if both
# millionaires trust a common third party, but we want to solve it
# without access to a third party.
#
# In this example the protocol is run between three millionaires and
# uses a protocol for secure integer comparison by Toft from 2005.
#
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
from viff.comparison import Toft05Runtime
from viff.config import load_config
from viff.util import rand, find_prime
from viff.active import BasicActiveRuntime, TriplesHyperinvertibleMatricesMixin

import sys



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
	print "Total time used: %.3f sec" % (stop-start)
    '''
    if runtime.id == 1:
        f = open('time.txt', 'w')
        f.write(stop-start)
        f.close()
    '''
	print "*" * 64
    #return x




class OfflineProtocol:
    # this is only for testing generating random -1/1 shares.
	def __init__(self, runtime,k):
		self.k =k
		self.runtime = runtime
		self.ramdom_shares = [0 for i in range(self.k * int(math.log(self.k,2)))]
		self.p = find_prime(2**256, blum=True)
		self.Zp = GF(self.p)
		self.triggers = [Share(self.runtime,self.Zp) for i in range(self.k * int(math.log(self.k,2)))]
			
		#print self.p

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


	def calculate_share(self,result,r,i):
		#print ""caculating shares
		v = result**((-(self.p+1)/4)%(self.p - 1))
		self.ramdom_shares[i] = r * v
		self.triggers[i].callback(1)
	
	def preprocess_ready(self,result):
		print "preprocess_ready"
		record_stop()
		self.write_to_file(self.ramdom_shares)
		record_stop()
		results = self.runtime.synchronize()
		self.runtime.schedule_callback(results, lambda _: self.runtime.shutdown())

		'''
		for i in range(self.k * int(math.log(self.k,2))): 
			open_1= self.runtime.open(self.ramdom_shares[i])
			
			open_1.addCallback(self.plainprint)
		'''

	def write_to_file(self,shares):
		#print "here"
		filename = "party" + str(self.runtime.id) + "_butterfly_random_share"
		
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
Toft05Runtime.add_options(parser)
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
