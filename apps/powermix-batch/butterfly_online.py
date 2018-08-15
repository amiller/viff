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
import os,sys
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


class OnlineProtocol:

    def __init__(self, runtime, k, threshold):
	self.k = k
	self.delta = threshold
	self.runtime = runtime
	self.ramdom_shares = [0 for i in range(self.k * int(math.log(self.k,2)))]
	self.input = [0 for i in range(self.k)]
	self.p = find_prime(2**256, blum=True)
	self.Zp = GF(self.p)
	self.write_index = 1
	self.trigger = [Share(self.runtime,self.Zp) for i in range(int(2 ** (int(math.log(self.k,2)) - self.delta))]
	print "begin allocating input shares(Party 1 will generate these shares)"

	for i in range(self.k ):
		if runtime.id == 1:
			self.input[i] = self.runtime.shamir_share([1], self.Zp,i + 1)			
		else:
			self.input[i] = self.runtime.shamir_share([1], self.Zp)
	# load -1/1 shares from file
	self.load_from_file(self.k,self.p)

	self.preprocess_ready()
    def preprocess_ready(self):
	print "preprocess_ready"
	record_start()
	output =  self.permutation_network(self.input,self.k)
	record_stop()
	print "shuffle done"
	if self.delta == 0:
		open_tx = [0 for i in range(self.k)]
		for i in range(self.k):
			open_tx[i] = self.runtime.open(output[i])
		list = [open_tx[i] for i in range(self.k)] 
		result = gather_shares(list)
		result.addCallback(self.write_result_to_file,open_tx)


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
	output1 = 1/self.Zp(2) *(input1 + input2 + m)
	output2 = 1/self.Zp(2) *(input1 + input2 - m)


	return output1,output2

    def permutation_network(self,input,num,level = 0):
	trigger1 = 0
	#print "new layer"
	if level == int(math.log(self.k,2)) - self.delta:
		result = gather_shares(input)
		result.addCallback(self.write_share_to_file,input)
	if level > int(math.log(self.k,2)) - self.delta:
		#print "pls shutdown"
		return None
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
		if second_layer_output1 == None or second_layer_output2 == None:
			return None
					
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

    def load_from_file(self,k,p):
	filename = "party" + str(self.runtime.id) + "_butterfly_random_share"
	
	FD = open(filename, "r")
	line = FD.readline()
	if int(line) != k:
		print "k dismatch!! k in file is %d"%(int(line))
	line = FD.readline()
	if int(line) != p:
		print "prime dismatch!! prime in file is %d"%(int(line))
	self.Zp = GF(p)
	print p
	line = FD.readline()
	i = 0
	while line:
		#print i
		self.ramdom_shares[i] = Share(self.runtime,self.Zp,self.Zp(int(line)))

		line = FD.readline()  
		i = i + 1

    def write_share_to_file(self,result,shares):

	print self.write_index
	filename = "party" + str(self.runtime.id) + "_butterfly_online_batch" + str(self.write_index)
	FD = open(filename, "w")
	self.write_index = self.write_index + 1
	content = str(len(shares)) + "\n" + str(self.p) + "\n"
	for share in shares:
		content = content + str(share.result)[1:-1] + "\n"
	FD.write(content)
	FD.close()

	self.trigger[self.write_index-2].callback(1)
	print "pass"

	if self.write_index == 2 ** (int(math.log(self.k,2)) - self.delta) + 1:
		print "time to shutdown"

		results = self.runtime.synchronize()
        	self.runtime.schedule_callback(results, lambda _: self.runtime.shutdown())
		os._exit(0)
    def write_result_to_file(self,result,shares):


	filename = "party" + str(self.runtime.id) + "_butterfly_online_result" 
	content = ""
	FD = open(filename, "w")
	for share in shares:
		content = content + str(share.result)[1:-1] + "\n"
	FD.write(content)
	FD.close()
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
threshold = int(sys.argv[3])
# Create a deferred Runtime and ask it to run our protocol when ready.
runtime_class = make_runtime_class(runtime_class=BasicActiveRuntime,
    mixins=[TriplesHyperinvertibleMatricesMixin])
pre_runtime = create_runtime(id, players, 1, options, runtime_class=runtime_class)
pre_runtime.addCallback(OnlineProtocol,k,threshold)
pre_runtime.addErrback(errorHandler)

# Start the Twisted event loop.
reactor.run()
