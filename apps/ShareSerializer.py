import pickle
from viff.field import GF
from viff.runtime import Share

class SerializableShare(object):
    def __init__(self, values, field_modulus):
        self.values = values
        self.field_modulus = field_modulus


def read_from_file(runtime, suffix=""):
    with open('share-' + suffix + str(runtime.id) + '.pickle', 'rb') as handle:
        serializable_share = pickle.load(handle)
        field = GF(serializable_share.field_modulus)
        shares = [Share(runtime, field, 
            field(value)) for value in serializable_share.values]
        return shares

def write_to_file(shares, runtime, field, suffix=""):
    values = [share.value for share in shares]
    serializable_share = SerializableShare(values, field.modulus)
    with open('share-' + suffix + str(runtime.id) + '.pickle', 'wb') as handle:
        pickle.dump(serializable_share, handle, -1)
    return shares
