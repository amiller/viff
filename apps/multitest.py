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
import time
from viff.runtime import create_runtime, gather_shares,Share
from viff.comparison import Toft05Runtime
from viff.config import load_config
from viff.util import rand, find_prime
from viff.active import TriplesHyperinvertibleMatricesMixin

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

class Protocol:

    def __init__(self, runtime):
        # Save the Runtime for later use
        self.runtime = runtime
	self.k = 64
	self.b = 2
	self.threshold = 1

	self.matrix = [[0 for x in range(self.k + 1)] for y in range(self.k + 1)]
	self.resultmatrix = [[0 for x in range(self.k + 1)] for y in range(self.k + 1)]

	self.openmatrix =[[0 for x in range(self.k + 1)] for y in range(self.k + 1)]
	


	#self.powersum = [0 for x in range(self.k + 1)]
        # This is the value we will use in the protocol.
        self.target = [i for i in range(self.k)]
	#self.target = [7]

	self.Zp = GF(find_prime(2**64))

	self.calculate_powersum(self.target[0],0)

    def calculate_powersum(self,item,cnt):
	
	#print "generating powersums for %d and cnt %d"%(item,cnt)

	if self.runtime.id == 1:
		self.a = self.runtime.shamir_share([1], self.Zp, item)
	else:
		self.a = self.runtime.shamir_share([1], self.Zp)
		
	#print "generating precomputed powers"
	if self.runtime.id == 1:
		self.matrix[0][0] = self.runtime.shamir_share([1], self.Zp,0)
		self.matrix[0][1] = self.runtime.shamir_share([1], self.Zp, self.b)
	else:
		self.matrix[0][0] = self.runtime.shamir_share([1], self.Zp)
		self.matrix[0][1] = self.runtime.shamir_share([1], self.Zp)
	for i in range(2,self.k + 1):
		self.matrix[0][i] = self.matrix[0][i - 1] * self.matrix[0][1]
		
	self.matrix[1][0] = self.a
	self.matrix[1][1] = self.matrix[1][0] * self.matrix[0][1]


	self.prefix = self.runtime.open(self.a - self.matrix[0][1])

	list1 = [self.prefix,self.matrix[1][0],self.matrix[1][1] ]
	list1 = list1 + [self.matrix[0][i] for i in range(1,self.k + 1)]


	results = gather_shares(list1)
	results.addCallback(self.preprocess_ready,cnt)


	#self.runtime.schedule_callback(results, lambda _: self.runtime.synchronize())
        #self.runtime.schedule_callback(results, lambda _: self.runtime.shutdown())




    def preprocess_ready(self,results,cnt):
	print "ready! with value %d"%(cnt)
	print results[0]
	#record_start()
	'''
	for m in xrange(2, self.k+1):
		
		if m == 2 :
			sum = self.matrix[0][1].result + self.matrix[1][1].result
			self.matrix[2][0] = self.prefix.result * sum + self.matrix[0][2]
			self.matrix[2][1] = self.ab
			self.matrix[2][2] = self.matrix[0][2]
			self.matrix[1][2] = self.matrix[2][0]

		else:
			
			if (m %2) == 1:
				
				for n in range(0,m+1):
					print "%d, %d"%(m,n)
					if n == 0:
						for p in range(0,m-n):
							print self.matrix[2][n+p]
					if n == m :
						self.matrix[3][n] = self.matrix[0][m]
					elif n != (m - 1):
	
						sum = 0
						for p in range(0,m-n):
							sum = sum + self.matrix[2][n+p].result
						self.matrix[3][n] = self.prefix.result * sum + self.matrix[0][m]
						print self.matrix[3][n]
						if n == 0 :
							self.matrix[1][m] = self.matrix[3][0]
					else:
						sum = 0
						for p in range(0,n):
							sum = sum + self.matrix[2][n-p-1].result
						self.matrix[3][n] = (-1) * self.prefix.result * sum + self.matrix[1][m]
						print self.matrix[3][n]
						
			else:	
				for n in range(0,m+1):
					print "%d, %d"%(m,n)
					if n == 0:
						for p in range(0,m-n):
							print self.matrix[3][n+p]
					if n == m :
						
						self.matrix[2][n] = self.matrix[0][m]

					elif n != (m - 1):
						sum = 0
						for p in range(0,m-n):
							sum = sum + self.matrix[3][n+p].result
						self.matrix[2][n] = self.prefix.result * sum + self.matrix[0][m]
						print self.matrix[2][n]
						if n == 0 :
							self.matrix[1][m] = self.matrix[2][0]
					else:
						sum = 0
						for p in range(0,n):
							sum = sum + self.matrix[3][n-p-1].result
						self.matrix[2][n] = (-1) * self.prefix.result * sum + self.matrix[1][m]
						print self.matrix[3][n]
	'''
	for m in xrange(2, self.k + 1):
		for n in xrange(0, m):
			if m == 2 and n == 1:
				print "[ab] already calculated"

			else:


				if (m - n) != 1 :
					#print "[%d,%d]"%(m-n,n)
					sum = 0
					for p in range(0,m-n):
						sum = sum + self.matrix[m-n-1-p][n+p].result

					self.matrix[m-n][n] = results[0] * sum + self.matrix[0][m]
					#print self.prefix.result
					#print self.matrix[0][m].result
					#print sum
					#print self.matrix[m-n][n]
				else:
					#print "[%d,%d]"%(m-n,n)
					sum = 0

					for p in range(0,n):
						sum = sum + self.matrix[m-n+p][n-1-p].result
					self.matrix[m-n][n] = (-1) * results[0] * sum + self.matrix[m][0]

					#print sum
					#print self.matrix[m-n][n]
	print "calculation finished %d"%(cnt)
	for i in range(1,self.k + 1 ):
		self.resultmatrix[cnt][i] = self.matrix[i][0]
	#self.triggers.callback(1)
        #record_stop()
	'''
        for i in range(1 , self.k + 1):
                self.openmatrix[i] = self.runtime.open(self.matrix[1][i])
	
        print "reconstruction finished"
        list2 = [self.openmatrix[i] for i in range(1,self.k + 1)]
        
        results = gather_shares(list2)
        results.addCallback(self.calculation_ready,cnt)
	'''
	results = self.runtime.synchronize()
	results.addCallback(self.syncpoint,cnt)

    def syncpoint(self,results,cnt):

	if cnt < len(self.target) - 1:
		self.calculate_powersum(self.target[cnt + 1],cnt + 1)
		
	else:
		self.open_check()






    def calculation_ready(self, results,cnt):
	print "ready to print"
	print cnt
        print results
        # for i in range(1,self.k+1):
                # print results[i][0]
	#return results
	#self.powersum = results
    def open_check(self):
	print"open!!!!"
	list1 = [] 
	for cnt in range(len(self.target)):
		for i in range(1 , self.k + 1):
			
                	self.openmatrix[cnt][i] = self.runtime.open(self.resultmatrix[cnt][i])
		list1 = list1 + [self.openmatrix[cnt][i] for i in range(1,self.k + 1)]
	results = gather_shares(list1)
        results.addCallback(self.calculation_ready,cnt)

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
pre_runtime = create_runtime(id, players, 1, options, ActiveRuntime)
pre_runtime.addCallback(Protocol)
pre_runtime.addErrback(errorHandler)

# Start the Twisted event loop.
reactor.run()