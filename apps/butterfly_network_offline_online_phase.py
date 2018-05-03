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

Zp = GF(find_prime(2**256, blum=True))

class Protocol:

    def __init__(self, runtime):
	self.k = 2048
	self.runtime = runtime
	self.ramdom_shares = [0 for i in range(self.k * int(math.log(self.k,2)))]
	self.triggers = [Share(self.runtime,Zp) for i in range(self.k * int(math.log(self.k,2)))]
	self.input = [0 for i in range(self.k)]
	self.p = find_prime(2**256, blum=True)
	print "begin allocating input shares(Party 1 will generate these shares)"

	for i in range(self.k ):
		if runtime.id == 1:
			self.input[i] = self.runtime.shamir_share([1], Zp,i)			
		else:
			self.input[i] = self.runtime.shamir_share([1], Zp)
	'''
	for i in range(self.k * int(math.log(self.k,2))):
		if runtime.id == 1:
			self.ramdom_shares[i] = self.runtime.shamir_share([1], Zp,randint(0, 1))			
		else:
			self.ramdom_shares[i] = self.runtime.shamir_share([1], Zp)
	'''
	print "begin generating random 1/-1 shares"
	for i in range(self.k * int(math.log(self.k,2))):
		
		r = runtime.prss_share_random(Zp)
		u = r * r
		open_u = self.runtime.open(u)
		open_u.addCallback(self.calculate_share,r,i)

	list = [self.input[i] for i in range(self.k)]
	list = list + [self.triggers[i] for i in range(self.k * int(math.log(self.k,2)))]
	result = gather_shares(list)

	result.addCallback(self.preprocess_ready)

    def preprocess_ready(self,result):
	print "preprocess_ready"
	record_start()
	output =  self.permutation_network(self.input,self.k)
	record_stop()
	print "shuffle done"
	open_tx = [0 for i in range(self.k)]
	for i in range(self.k):
		open_tx[i] = self.runtime.open(output[i])
	list = [open_tx[i] for i in range(self.k)] 
	result = gather_shares(list)
	result.addCallback(self.plainprint)

	self.runtime.schedule_callback(results, lambda _: self.runtime.synchronize())
        self.runtime.schedule_callback(results, lambda _: self.runtime.shutdown())

    def plainprint(self,result):
	print "done!"
	#print result

    def switch0_1(self,input1,input2):
	#print "inside switch"

	select_bit = self.ramdom_shares.pop()
	output1 = (1 - select_bit)* input1 + select_bit * input2
	output2 = select_bit * input1 + (1 - select_bit) * input2


	return output1,output2


    def switch(self,input1,input2):
	#print "inside switch"

	select_bit = self.ramdom_shares.pop()
	m = select_bit * (input1 - input2)
	output1 = 1/Zp(2) *(input1 + input2 + m)
	output2 = 1/Zp(2) *(input1 + input2 - m)


	return output1,output2

    def permutation_network(self,input,num,level = 0):
	trigger1 = 0
	#print "new layer"
	if num ==2:		
		temp1,temp2 = self.switch(input[0],input[1])		
		result =  [temp1,temp2]
		return result	
	else:	
		first_layer_output1 = []
		first_layer_output2 = []
		result = []
		for i in range(num/2):
			temp1,temp2 = self.switch(input[i * 2],input[i * 2 + 1])
			first_layer_output1.append(temp1)
			first_layer_output2.append(temp2)
		#print "hi"
		#print first_layer_output1
		second_layer_output1 = self.permutation_network(first_layer_output1,num/2,level + 1)
		second_layer_output2 = self.permutation_network(first_layer_output2,num/2,level + 1)
					
		for i in range(num/2):
			temp1,temp2 = self.switch(second_layer_output1[i],second_layer_output2[i])
			result.append(temp1)
			result.append(temp2)			
			
		#print num
		#print result
		return result
	'''
	res2 = gather_shares(result)
			
	def finish(result):

		trigger1 = 1
	res2.addCallback(finish)
	while True:
		if trigger1 == 1:			
			return result

	'''

    def calculate_share(self,result,r,i):
	#print i

	v = result**((-(self.p+1)/4)%(self.p - 1))

	self.ramdom_shares[i] = r * v
	self.triggers[i].callback(1)


class Protocol2:
    # this is only for testing generating random shares.
    def __init__(self, runtime):
	self.k = 4
	self.runtime = runtime
	self.ramdom_shares = [0 for i in range(self.k * int(math.log(self.k,2)))]
	self.triggers = [Share(self.runtime,Zp) for i in range(self.k * int(math.log(self.k,2)))]
	self.p = find_prime(2**256, blum=True)
	print self.p

	for i in range(self.k * int(math.log(self.k,2))):
		
		r = runtime.prss_share_random(Zp)
		u = r * r
		open_u = runtime.open(u)
		open_u.addCallback(self.calculate_share,r,i)



	list = [self.triggers[i] for i in range(self.k * int(math.log(self.k,2)))]
	result = gather_shares(list)
	result.addCallback(self.preprocess_ready)

 
	
        #data = [1,2,3,4,5,6,7,8]
	#result = permutation_component(data,8)
	#print result

    def calculate_share(self,result,r,i):
	#print i
	v = result**((-(self.p+1)/4)%(self.p - 1))
	
	self.ramdom_shares[i] = r * v
	self.triggers[i].callback(1)

    def preprocess_ready(self,result):
	print "preprocess_ready"
	for i in range(self.k * int(math.log(self.k,2))): 
		open_1= self.runtime.open(self.ramdom_shares[i])
		
		open_1.addCallback(self.plainprint)


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

# Create a deferred Runtime and ask it to run our protocol when ready.
pre_runtime = create_runtime(id, players, 1, options, ActiveRuntime)
pre_runtime.addCallback(Protocol)
pre_runtime.addErrback(errorHandler)

# Start the Twisted event loop.
reactor.run()