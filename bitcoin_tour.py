# A Bitcoin implementation from scratch using only the Python standard library.
# The code follows what described by Andrej Karpathy in his blog post "A from-scratch tour of Bitcoin in Python" (http://karpathy.github.io/2021/06/21/blockchain/).
# I rewrote the code using a different structure and took advantage of some already implemented algorithms from the standard library.
# Other useful resources: http://www.righto.com/2014/02/bitcoins-hard-way-using-raw-bitcoin.html

import random
import hashlib
from typing import List, Union



# -----------------------------------------------------------------------
# HELPER FUNCTIONS

def inv(n: int, p: int) -> int:
    """ Returns modular multiplicate inverse m s.t. (n * m) % p == 1 """
    # Extended Euclideean Algorithm
    old_r, r = n, p
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    gcd, x, y = old_r, old_s, old_t
    return x % p

def encode_int(i: int, nbytes: int, encoding: str = 'little') -> bytes:
    """ Encode integer i into n-bytes using a given byte ordering. """
    return i.to_bytes(nbytes, encoding)

def encode_varint(i: int) -> bytes:
    """ Encode a (possibly but rarely large) integer into bytes with a super simple compression scheme. """
    if i < 0xfd:
        return bytes([i])
    elif i < 0x10000:
        return b'\xfd' + encode_int(i, 2)
    elif i < 0x100000000:
        return b'\xfe' + encode_int(i, 4)
    elif i < 0x10000000000000000:
        return b'\xff' + encode_int(i, 8)
    else:
        raise ValueError("integer too large: %d" % (i, ))

# -----------------------------------------------------------------------



# ----------------------------------- Elliptic Curve Cryptography ----------------------------------- #
# An elliptic curve is a curve satisfying an equation in the form y² = x³ + ax + b.
# Bitcoin uses the secp256k1 elliptic curve which satifies the equation y² = x³ + 7

class Curve:
    """
        Elliptic Curve over the field of integers modulo a prime.
        Points on the curve satisfy y^2 = x^3 + a*x + b (mod p).
        In the Bitcoin case we have:
            -  a = 0x0000000000000000000000000000000000000000000000000000000000000000  (simply 3)
            -  b = 0x0000000000000000000000000000000000000000000000000000000000000007  (simply 7)
    """
    def __init__(self, p: int, a: int, b: int) -> None:
        self.p = p
        self.a = a
        self.b = b


class Point:
    """ 
        An integer point (x, y) on a Curve.
        It's a fixed starting point on the curve, publicly known and used to begin the random walk around the curve.
    """
    def __init__(self, curve: Curve, x: int, y: int) -> None:
        self.curve = curve
        self.x = x
        self.y = y

    def __add__(self, other):
        # Handle special case
        if self == INF:
            return other
        if other == INF:
            return self
        # Handle special case of P + (-P) = 0
        if self.x == other.x and self.y != other.y:
            return INF
        # Compute the slope
        if self.x == other.x:
            m = (3 * self.x**2 + self.curve.a) * inv(2*self.y, self.curve.p)
        else:
            m = (self.y - other.y) * inv(self.x - other.x, self.curve.p)
        # Compute new point
        rx = (m**2 - self.x - other.x) % self.curve.p
        ry = (-(m*(rx - self.x) + self.y)) % self.curve.p

        return Point(self.curve, rx, ry)

    def __rmul__(self, k: int):
        assert isinstance(k, int) and k >= 0
        result = INF
        append = self
        while k:
            if k & 1:
                result += append
            append += append
            k >>= 1
        return result

# Define extreme point special case
INF = Point(None, None, None)


class Generator:
    """ A generator over a curve -> an initial point and the (pre-computed) order. """
    def __init__(self, G: Point, n: int) -> None:
        self.G = G
        self.n = n



# ----------------------------------- Generate identity ----------------------------------- #
# Create secret and public keys, and address.
# The private key is a 256-bit string between 1 and the order of the generating point.
# The public key is a tuple given by the multiplication of the private key and the publicly known generating point.
# However, the public key, in order to be useful, has to be encoded (with the addition of a publicly known prefix) into a 512-bit string using the HASH256 and RIPEMD160 functions.
# [Note: even though theoretically possible, it's extremely unlikely that someone would be able to derive (or even randomly guess) the private key from the public key.]
# To genereate the addres from the public key:
#      (1) hash down to 160 bits using the HASH256 and RIPEMD160 algorithms
#      (2) encode the key in ASCII using Base58Check encoding
# [Note: you cannot determine the public key or the private key from the address.]

class GenerateWallet(Point):
    """
        Contains the functionality for creating:
           - public key
           - private key
           - address
    """
    def __init__(self, curve: Curve, x: int, y: int) -> None:
        super().__init__(curve, x, y)

    def b58encode(self, b: bytes) -> str:
        """ Base58Check encoding function. """
        alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        assert len(b) == 25
        n = int.from_bytes(b, 'big')
        chars = []
        while n:
            n, i = divmod(n, 58)
            chars.append(alphabet[i])
        # Special case which handles the leading 0 bytes
        num_leading_zeros = len(b) - len(b.lstrip(b'\x00'))
        res = num_leading_zeros * alphabet[0] + ''.join(reversed(chars))

        return res

    def get_secret_key(self, generator: Generator) -> int:
        """ Generate secret key (a random 256-bit string). """
        return random.randrange(1, generator.n)

    def get_public_key(self, secret_key, point: Point, compressed: bool, hash160: bool = False):
        """ Generate and encode public key (a 512-bit string derived from the secret key with the addition of a prefix). """
        # Calculate public key
        public_key = secret_key * point

        # Encode public key -> return the SEC bytes encoding of the public key Point
        # Calculate the bytes
        if compressed:
            prefix = b'\x02' if public_key.y % 2 == 0 else b'\x03'
            pkb = prefix + public_key.x.to_bytes(32, 'big')
        else:
            pkb = b'\x04' + public_key.x.to_bytes(32, 'big') + public_key.y.to_bytes(32, 'big')

        # Hash if requested
        if hash160:
            # HASH256 and RIPEMD160 functions
            sha = hashlib.sha256()
            rip = hashlib.new('ripemd160')
            sha.update(pkb)
            rip.update(sha.digest())
            return rip.hexdigest()
        else:
            return pkb

    def get_address(self, public_key, net: str) -> str:
        """ Return associated bitcoin address for the given public key as string. """
        # Add version byte (0x00 for Main Network or 0x6f for Test Network)
        version = { 'main': b'\x00', 'test': b'\x6f' }
        ver_pkb_hash = version[net] + bytes.fromhex(public_key)
        # Calculate the checksum
        sha = hashlib.sha256()
        sha.update(ver_pkb_hash)
        checksum = sha.digest()
        sha = hashlib.sha256()
        sha.update(checksum)
        checksum = sha.digest()[:4]
        # Append to form the full 25-byte binary Bitcoin address
        byte_address = ver_pkb_hash + checksum
        # Base58Check for encoding the result
        b58check_address = self.b58encode(byte_address)
        return b58check_address



# ----------------------------------- Transactions ----------------------------------- #
# Every transtaction has the following elements:
#     -  transaction id -> a SHA256 double hash of the transaction data structure
#     -  one or more inputs -> either one big amount being spent or multiple smaller amounts combined
#     -  one or two outputs -> one for who receives the payment, and (only if needed) one returning the change to the sender
#     -  some other information such as the size of the transaction in bytes, the block in which it is included, the fees, etc...
# The Transaction will be considered valid if the sum of all outputs is lower than the sum of all inputs. 
# The difference between input and outputs, is given by the fee that goes to the miner of the block.
# Bitcoin has a stack-based scripting language, which is responsible for running the transaction operations.
# For example it verifies that the public key provided is valid and that it relates correctly with the signature.

class Script:
    """ 
        A simple implementation of the Script structure.
        It works by storing the script types as numbers and then encoding them into bytes.
    """
    def __init__(self, cmds: List[Union[int, bytes]]) -> None:
        self.cmds = cmds

    def encode(self):
        out = []
        for cmd in self.cmds:
            if isinstance(cmd, int):
                # An int is just an opcode -> encode as a single byte
                out += [encode_int(cmd, 1)]
            elif isinstance(cmd, bytes):
                # Bytes represent an element -> encode its length and then content
                length = len(cmd)
                assert length < 75

                out += [encode_int(length, 1), cmd]
        
        ret = b''.join(out)
        return encode_varint(len(ret)) + ret


class Transaction:
    """ 
        Complete transaction structure.
            - Creates and encodes both transaction inputs and outputs.
            - Encodes the transaction as bytes.
            - Returns id information.
    """
    def __init__(self, version: int, locktime: int = 0) -> None:
        self.version = version
        self.locktime = locktime

    # Creates the structure for the transaction input
    def create_transaction_input(
        self,
        prev_transaction_id: bytes,
        prev_transaction_idx: int,
        publickey_hash: str,
        script_sig: Script = None,   # Script in new transaction  -> must provide the data to satisfy the conditions of the script in the old transaction
        sequence: int = 0xffffffff
    ):
        return { 
            'prev_transaction_id': prev_transaction_id, 
            'prev_transaction_idx': prev_transaction_idx, 
            'script_sig': script_sig,
            'sequence': sequence,
            'prev_transaction_script_pubkey': Script([118, 169, publickey_hash, 126, 172])
        }

    def encode_transaction_input(self, transaction_input, script_override = None):
        """ Returns the given transaction input encoded in bytes. It's just serialization protocol. """
        out = []
        out += [transaction_input['prev_transaction_id'][::-1]]
        out += [encode_int(transaction_input['prev_transaction_idx'], 4)]

        if script_override is None:
            # Use the actual script
            out += [transaction_input['script_sig'].encode()]
        elif script_override is True:
            # Override the script with the "script_pubkey" of the associated input
            out += [transaction_input['prev_transaction_script_pubkey'].encode()]
        elif script_override is False:
            # Override with an empty script
            out += [Script([]).encode()]
        else:
            raise ValueError('script_override must be one of None, True or False')

        out += [encode_int(transaction_input['sequence'], 4)]

        return b''.join(out)

    # Creates the structure for the transaction output
    def create_transaction_output(
        self, 
        amount: int, 
        script_pubkey: Script  # Script in old transaction -> defines the conditions for spending the bitcoins
    ):
        return {
            'amount': amount, 
            'script_pubkey': script_pubkey
        }

    def encode_transaction_output(self, transaction_output):
        """ Returns the given transaction output encoded in bytes. It's just serialization protocol. """
        out = []
        out += [encode_int(transaction_output['amount'], 8)]
        out += [transaction_output['script_pubkey'].encode()]
        return b''.join(out)

    def encode(self, transaction_inputs: List[dict], transaction_outputs: List[dict], sig_index: int = -1) -> bytes:
        """
            Encode this transaction as bytes.
            If sig_index is given then return the modified transaction encoding of this transaction with respect to the single input index. 
            This result then consitutes the "message" that gets signed by the aspiring transactor of this input.
        """
        # Init output
        out = []

        # Encode metadata
        out += [encode_int(self.version, 4)]

        # Encode inputs
        out += [encode_varint(len(transaction_inputs))]
        if sig_index == -1:
            # Serealize a fully formed transaction
            out += [self.encode_transaction_input(transaction_input) for transaction_input in transaction_inputs]
        else:
            # Used when crafting digital signature for a specific input index
            out += [self.encode_transaction_input(transaction_input, script_override=(sig_index == i)) for i, transaction_input in enumerate(transaction_inputs)]
        
        # Encode outputs
        out += [encode_varint(len(transaction_outputs))]
        out += [self.encode_transaction_output(transaction_output) for transaction_output in transaction_outputs]
        
        # Encode other metadata
        out += [encode_int(self.locktime, 4)]
        out += [encode_int(1, 4) if sig_index != -1 else b'']

        return b''.join(out)

    def transaction_id(self, transaction_inputs: List[dict], transaction_outputs: List[dict]) -> str:
        """ Return id of the finished transaction. """
        sha = hashlib.sha256()
        sha.update(self.encode(transaction_inputs, transaction_outputs))
        res = sha.digest()
        sha = hashlib.sha256()
        sha.update(res)
        return sha.digest()[::-1].hex()


class Signature:
    """ 
        Data structure for the signature, which is simply a tuple of two integers (r, s)
    """
    def __init__(self, r: int, s: int) -> None:
        self.r = r
        self.s = s

    def signature_encode(self) -> bytes:
        """ Return the DER encoding of this signature. """
        def dern(n):
            nb = n.to_bytes(32, byteorder='big')
            nb = nb.lstrip(b'\x00')  # Strip leading zeros
            nb = (b'\x00' if nb[0] >= 0x80 else b'') + nb  # Add 0x00 at the beginning if fist byte >= 0x80
            return nb
        
        rb = dern(self.r)
        sb = dern(self.s)
        content = b''.join([bytes([0x02, len(rb)]), rb, bytes([0x02, len(sb)]), sb])
        frame = b''.join([bytes([0x30, len(content)]), content])
        return frame

def sign(secret_key: int, message: bytes, generator: Generator):
    """ Given the private key, the message and the generator, returns the signature that it is necessary for a transaction to be valid. """
    # Get order of the elliptic curve
    n = generator.n
    # Double hash the message and convert to integer
    sha = hashlib.sha256()
    sha.update(message)
    message = sha.digest()
    sha = hashlib.sha256()
    sha.update(message)
    z = int.from_bytes(sha.digest(), 'big')

    # Generate new secret/public key pair at random
    sk = random.randrange(1, n)
    P = sk * generator.G

    # Calculate the signature
    r = P.x
    s = inv(sk, n) * (z + secret_key * r) % n
    if s > n / 2:
        s = n - s

    return Signature(r, s)
