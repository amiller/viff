from optparse import OptionParser
import viff.reactor
viff.reactor.install()
from twisted.internet import reactor

from viff.field import GF
from viff.runtime import (Runtime, create_runtime, make_runtime_class,
                          gather_shares, Share)
from viff.config import load_config

import random
import sys
import cPickle as pickle

class SerializableShare(object):

    def __init__(self, values, field_modulus):
        self.values = values
        self.field_modulus = field_modulus


class Protocol:
    """
    Every player shares one random value in the field which is written to
    the file in the write mode. In read mode the same shares are made available
    to the same player.
    """
    def __init__(self, runtime, field, isReadMode):
        self.runtime = runtime
        self.field = field

        print("Connected to all parties.")

        if not isReadMode:
            players = runtime.players.keys()
            random_number = random.randint(0, field.modulus - 1)
            print "Sharing Value: ", random_number
            shares = runtime.shamir_share(players, field, random_number)
            shares = gather_shares(shares)
            shares.addCallback(self.__write_to_file)
        else:
            shares = self.__read_from_file()
            shares = map(runtime.open, shares)
            shares = gather_shares(shares)
            shares.addCallback(self.__view_shares)

        runtime.schedule_callback(shares, lambda _: runtime.synchronize())
        runtime.schedule_callback(shares, lambda _: runtime.shutdown())

    def __view_shares(self, output):
        print "SHARES:", output 

    def __read_from_file(self):
        with open('share-' + str(self.runtime.id) + '.pickle', 'rb') as handle:
            serializable_share = pickle.load(handle)
            field = GF(serializable_share.field_modulus)
            shares = [Share(self.runtime, field, field(value)) for value in serializable_share.values]
            return shares

    def __write_to_file(self, shares):
        values = [share.value for share in shares]
        serializable_share = SerializableShare(values, self.field.modulus)
        with open('share-' + str(self.runtime.id) + '.pickle', 'wb') as handle:
            pickle.dump(serializable_share, handle)
        return shares

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
    id, players = load_config(args[0])
    pre_runtime = create_runtime(id, players, options.threshold, options)

    # Jubjub.
    Zp = GF(0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001)

    # Pass 0 for reading shares from file, else pass anything to write
    isReadMode = True if int(sys.argv[2]) == 0 else False

    pre_runtime.addCallback(Protocol, Zp, isReadMode)
    pre_runtime.addErrback(errorHandler)

    # Start the Twisted event loop.
    reactor.run()