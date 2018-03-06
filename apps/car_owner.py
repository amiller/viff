#!/usr/bin/env python

# Copyright 2008 VIFF Development Team.
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
#

"""This program is a very simple example of a VIFF program which shows
the secret equality testing of two numbers.

The program can be run as follows for each player (min 3) where 24 is
the number we would like to compare:

$ python equality.py player-X.ini -n 24

Only the numbers of player 1 and player 2 are actually compared, but
more players are necessary for the security.
"""

from optparse import OptionParser
import viff.reactor
viff.reactor.install()
from twisted.internet import reactor

from viff.field import GF
from viff.runtime import Runtime, create_runtime, make_runtime_class
from viff.config import load_config
from viff.util import dprint, find_prime, rand
from viff.equality import ProbabilisticEqualityMixin
from viff.comparison import ComparisonToft07Mixin

def bits_to_val(bits):
    return sum([2**i * b for (i, b) in enumerate(reversed(bits))])

def get_owner_hash_key(owner_id):
    return 10 * owner_id

def get_hmac(index_to_share, new_owner_id, secret_key):
    hmac = (index_to_share * 10000 + new_owner_id * 1000 +
            get_owner_hash_key(new_owner_id) * 10 + secret_key)
    return hmac

def verify_hmac(hmac, index_to_share, secret_key, new_owner_id):
    assert hmac == get_hmac(index_to_share, new_owner_id, secret_key)

def errorHandler(failure):
    print "Error: %s" % failure

def divide(x, y, l):
    """Returns a share of of ``x/y`` (rounded down).

       Precondition:  ``2**l * y < x.field.modulus``.

       If ``y == 0`` return ``(2**(l+1) - 1)``.

       The division is done by making a comparison for every
       i with ``(2**i)*y`` and *x*.
       Protocol by Sigurd Meldgaard.

       Communication cost: *l* rounds of comparison.

       Also works for simple integers:
       >>>divide(3, 3, 2)
       1
       >>>divide(50, 10, 10)
       5
       """
    bits = []
    for i in range(l, -1, -1):
        t = 2**i * y
        cmp = t <= x
        bits.append(cmp)
        x = x - t * cmp
    return bits_to_val(bits)

class Protocol:

    def __init__(self, runtime):
        print "Connected."
        self.rt = runtime

        secret_key = runtime.id
        secret_key_hash = get_owner_hash_key(runtime.id)
        current_owner_id = 1 
        index_to_share = 0
        new_owner_id = 2

        if runtime.id == 1:
            # Initially testing with only one record.
            # Prepare a record which includes the secret key hash and the current
            # owner information.
            my_record = (rand.randint(10, 99) * 1000 + secret_key_hash * 10
                    + current_owner_id)
          
            # Get the HMAC.
            hmac = get_hmac(index_to_share, new_owner_id, secret_key) 
            
            print ("Initial record: " + str(my_record))
            # print ("HMAC " + str(hmac))
            # print ("Secret key " + str(secret_key))
            # print ("New owner id " + str(new_owner_id))

            # The player which wants to transfer the record must share these values.
            shared_secret_key = runtime.input([current_owner_id], Zp, secret_key)
            shared_current_owner_id = runtime.input([current_owner_id], Zp, current_owner_id)
            shared_index = runtime.input([current_owner_id], Zp, index_to_share)
            shared_hmac = runtime.input([current_owner_id], Zp, hmac)
            shared_new_owner_id = runtime.input([current_owner_id], Zp, new_owner_id)
        else:
            shared_secret_key = runtime.input([current_owner_id], Zp, None)
            shared_current_owner_id = runtime.input([current_owner_id], Zp, None)
            shared_index = runtime.input([current_owner_id], Zp, None)
            shared_hmac = runtime.input([current_owner_id], Zp, None)
            shared_new_owner_id = runtime.input([current_owner_id], Zp, None)

        # assert hash(shared_secret_key) == hash_of_secret_key
        # Secret key of the admin is 1, therefore the secret key hash = 10. These
        # two must match.
        #TODO: This is not getting terminated right away when the comparison fails.
        def finish(eq):
            if not eq:
                raise ValueError('Comparison failed!') 

        secret_key_hash_to_compare = shared_secret_key * 10
        result = (secret_key_hash_to_compare == 10)
        result = runtime.open(result)
        dprint("Secret key hashes match :%s", result)
        result.addCallback(finish)

        result = (shared_hmac == get_hmac(shared_index, shared_new_owner_id, shared_secret_key))
        result = runtime.open(result)
        dprint("HMAC matches :%s", result)
        result.addCallback(finish)
        # (VIN, owner, counter) =  records[index]
        # Share the record.
        if runtime.id == 1:
            # Only player 1 is the admin and it shares the records it has while
            # the others share None. 
            shared_record = runtime.input([current_owner_id], Zp, my_record)
        else:
            shared_record = runtime.input([current_owner_id], Zp, None)
        
        # records[index] = (VIN, newOwner, counter+1, newHash)   // writing back
        # Reveal the record.
        record = runtime.output(shared_record)
        dprint("Existing record: %s", record)

        # other_info = divide(shared_record, 1000, 10)
        other_info = record - (secret_key_hash_to_compare * 10) - shared_current_owner_id
        # dprint("Other info: %s", runtime.output(other_info))
        
        new_shared_record = (other_info + get_owner_hash_key(shared_new_owner_id) * 10
                + shared_new_owner_id)
        # dprint("Updated record: %s", runtime.output(new_shared_record))
        # shared_new_owner_id = runtime.output(shared_new_owner_id)
        # dprint("New Owner Id: %s", shared_new_owner_id)
        new_shared_record = runtime.output(new_shared_record)

        # We only print the value of shared record for the new owner,
        # since only player new owner  has the value of the new record.
        if runtime.id == 2:
            dprint("### opened s1: %s ###", new_shared_record)

        # When the values for the opening arrive, we can call the
        # finish function, followed by the shutdown method.

        result.addCallback(lambda _: runtime.shutdown())


# Parse command line arguments.
parser = OptionParser(usage=__doc__)

# parser.add_option("--modulus",
                 # help="lower limit for modulus (can be an expression)")
# parser.add_option("-n", "--number", type="int",
                 # help="number to compare")

parser.set_defaults(modulus=2**65, number=None)

Runtime.add_options(parser)

options, args = parser.parse_args()

if len(args) == 0:
    parser.error("you must specify a config file")

Zp = GF(find_prime(options.modulus, blum=True))

# Load configuration file.
id, players = load_config(args[0])

runtime_class = make_runtime_class(mixins=[ProbabilisticEqualityMixin, ComparisonToft07Mixin])
pre_runtime = create_runtime(id, players, 1, options, runtime_class)
pre_runtime.addCallback(Protocol)
pre_runtime.addErrback(errorHandler)

# Start the Twisted event loop.
reactor.run()
