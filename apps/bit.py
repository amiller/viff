#!/usr/bin/env python

# Copyright 2009 VIFF Development Team.
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

# This file contains a simpel example of a VIFF program, which illustrates
# the basic features of VIFF. How to input values from the command line,
# from individual players in the program, add, multiply, and output values
# to all or some of the players.

# Inorder to run the program follow the three steps:
#
# Generate player configurations in the viff/apps directory using:
#   python generate-config-files.py localhost:4001 localhost:4002 localhost:4003
#
# Generate ssl certificates in the viff/apps directory using:
#   python generate-certificates.py
#
# Run the program using three different shells using the command:
#   python beginner.py player-x.ini 79
# where x is replaced by the player number

# Some useful imports.
import sys

import viff.reactor
viff.reactor.install()
from twisted.internet import reactor
from viff.aes import bit_decompose
from viff.field import GF
from viff.runtime import create_runtime
from viff.config import load_config
from viff.util import dprint, find_prime


# Load the configuration from the player configuration files.
id, players = load_config(sys.argv[1])
input = int(sys.argv[2])
# Initialize the field we do arithmetic over.
Zp = GF(find_prime(2**256))

# Read input from the commandline.


def protocol(runtime):
    print "-" * 64

    print "Program started"
    

    if runtime.id == 1:
        s1 = runtime.input([1], Zp, input)
    else:
        s1 = runtime.input([1], Zp, None)

    print "entry"
    ans = bit_decompose(s1,Zp,False)

    print len(ans)
    for i in range(256):
	a = runtime.output(ans[i])
    	a.addCallback(ready)


    
def ready(results):

    #print results
    m = 1


# Create a runtime
pre_runtime = create_runtime(id, players, 1)
pre_runtime.addCallback(protocol)
# This error handler will enable debugging by capturing
# any exceptions and print them on Standard Out.

print "#### Starting reactor ###"
reactor.run()
