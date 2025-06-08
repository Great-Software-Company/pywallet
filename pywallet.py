#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

pywversion = "2.2-py3-improved"
never_update = False

#
# jackjack's pywallet.py
# https://github.com/jackjack-jj/pywallet
# forked from Joric's pywallet.py
#


import sys

PY3 = sys.version_info.major > 2

import warnings


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return '%s:%s: %s: %s\n' % (filename, lineno, category.__name__, message)


warnings.formatwarning = warning_on_one_line
if PY3:
    import _thread as thread
    import functools

    raw_input = input
    xrange = range
    long = int
    unicode = str
    reduce = functools.reduce
else:
    import thread

missing_dep = []

try:
    if PY3:
        from bsddb3.db import *
        from bsddb3 import db as bdb
    else:
        from bsddb.db import *
        import bsddb as bdb
except ImportError:
    missing_dep.append('bsddb3' if PY3 else 'bsddb')
    bdb = None

import os, sys, time, re

pyw_filename = os.path.basename(__file__)
pyw_path = os.path.dirname(os.path.realpath(__file__))

try:
    import simplejson as json
except:
    import json

import bisect
import itertools
import unicodedata
import hmac
import getpass
import logging
import struct
import traceback
import socket
import types
import string
import hashlib
import random

if PY3:
    import urllib.request as urllib
else:
    import urllib
import math
import base64
import collections
import weakref
import binascii
from types import MethodType
import unittest

from datetime import datetime
from subprocess import *

import os
import os.path
import platform


def ordsix(x):
    if x.__class__ == int: return x
    return ord(x)


def chrsix(x):
    if not (x.__class__ in [int, long]): return x
    if PY3: return bytes([x])
    return chr(x)


def str_to_bytes(k):
    if k is None:
        return b''
    if isinstance(k, int):
        # Convert integer to string then to bytes
        return str(k).encode('ascii')
    if isinstance(k, str) and not hasattr(k, 'decode'):
        return k.encode('ascii')
    if isinstance(k, bytes):
        return k
    # For any other type, convert to string first then to bytes
    return str(k).encode('ascii')


def bytes_to_str(k):
    if k.__class__ == bytes:
        return k.decode()
    if k.__class__ == unicode:
        return bytes_to_str(k.encode())
    return k


class Bdict(dict):
    def __init__(self, *a, **kw):
        super(Bdict, self).__init__(*a, **kw)
        for k, v in self.copy().items():
            try:
                del self[k]
            except:
                pass
            self[bytes_to_str(k)] = v

    def update(self, *a, **kw):
        other = self.__class__(*a, **kw)
        return super(Bdict, self).update(other)

    def pop(self, k, *a):
        return super(Bdict, self).pop(bytes_to_str(k), *a)

    def get(self, k, default=None):
        return super(Bdict, self).get(bytes_to_str(k), default)

    def __getitem__(self, k):
        return super(Bdict, self).__getitem__(bytes_to_str(k))

    def __setitem__(self, k, v):
        return super(Bdict, self).__setitem__(bytes_to_str(k), v)

    def __contains__(self, k):
        return super(Bdict, self).__contains__(bytes_to_str(k))

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, super(Bdict, self).__repr__())


max_version = 81000
json_db = Bdict({})
private_keys = []
private_hex_keys = []
passphrase = ""
global_merging_message = ["", ""]
CNT = collections.namedtuple

balance_site = 'https://blockchain.info/q/addressbalance/'
backup_balance_site = 'https://api.blockcypher.com/v1/btc/main/addrs/'

aversions = {}
for i in range(256):
    aversions[i] = "version %d" % i;
aversions[0] = 'Bitcoin';
aversions[48] = 'Litecoin';
aversions[52] = 'Namecoin';
aversions[111] = 'Testnet';


class Network(collections.namedtuple('Network', 'name p2pkh_prefix p2sh_prefix wif_prefix segwit_hrp')):
    instances = []

    def __init__(self, *a, **kw):
        self.__class__.instances.append(self)
        super(Network, self).__init__()

    def keyinfo(self, *a, **kw):
        pass


def eip55(hex_addr):
    if hex_addr[:2] == '0x': hex_addr = hex_addr[2:]
    hex_addr = hex_addr.lower()
    checksummed_buffer = ""
    hashed_address = bytes_to_str(binascii.hexlify(Keccak256(hex_addr).digest()))
    for nibble_index, character in enumerate(hex_addr):
        if character in "0123456789":
            checksummed_buffer += character
        elif character in "abcdef":
            hashed_address_nibble = int(hashed_address[nibble_index], 16)
            if hashed_address_nibble > 7:
                checksummed_buffer += character.upper()
            else:
                checksummed_buffer += character
        else:
            raise ValueError("Unrecognized hex character {} at position {}".format(character, nibble_index))
    return "0x" + checksummed_buffer


def ethereum_keyinfo(self, keyinfo, print_info=True):
    ethpubkey = keyinfo.uncompressed_public_key[1:]
    eth_hash = binascii.hexlify(Keccak256(ethpubkey).digest())[-40:]
    eth_addr = '0x' + bytes_to_str(eth_hash)
    if print_info and not keyinfo.compressed:
        print("Ethereum address:    %s" % eip55(eth_addr))
        print("Ethereum B58address: %s" % public_key_to_bc_address(eth_hash, 33))
    return CNT('SubKeyInfo', 'addr')(eth_addr)


network_bitcoin = Network('Bitcoin', 0, 5, 0x80, 'bc')
network_bitcoin_testnet3 = Network('Bitcoin-Testnet3', 0x6f, 0xc4, 0xef, 'tb')
network_ethereum = Network('Ethereum', 0, 5, 0x80, 'eth')
network_ethereum.keyinfo = MethodType(ethereum_keyinfo, network_ethereum)
network = network_bitcoin


def find_network(name):
    for n in Network.instances:
        if n.name.lower() == name.lower():
            return n
    return None


wallet_dir = ""
wallet_name = ""

ko = 1e3
kio = 1024
Mo = 1e6
Mio = 1024 ** 2
Go = 1e9
Gio = 1024 ** 3
To = 1e12
Tio = 1024 ** 4

prekeys = [binascii.unhexlify("308201130201010420"), binascii.unhexlify("308201120201010420")]
postkeys = [binascii.unhexlify("a081a530"), binascii.unhexlify("81a530")]

KeyInfo = collections.namedtuple('KeyInfo', 'secret private_key public_key uncompressed_public_key addr wif compressed')


def plural(a):
    if a >= 2: return 's'
    return ''


def systype():
    if platform.system() == "Darwin":
        return 'Mac'
    elif platform.system() == "Windows":
        return 'Win'
    return 'Linux'


def determine_db_dir():
    if wallet_dir in "":
        if platform.system() == "Darwin":
            return os.path.expanduser("~/Library/Application Support/Bitcoin/")
        elif platform.system() == "Windows":
            return os.path.join(os.environ['APPDATA'], "Bitcoin")
        return os.path.expanduser("~/.bitcoin")
    else:
        return wallet_dir


def determine_db_name():
    if wallet_name in "":
        return "wallet.dat"
    else:
        return wallet_name


########################
########################

from math import log
from operator import xor
from copy import deepcopy

RoundConstants = [1, 32898, 0x800000000000808a, 0x8000000080008000, 32907, 2147483649, 0x8000000080008081,
                  0x8000000000008009, 138, 136, 2147516425, 2147483658, 2147516555, 0x800000000000008b,
                  0x8000000000008089, 0x8000000000008003, 0x8000000000008002, 0x8000000000000080, 32778,
                  0x800000008000000a, 0x8000000080008081, 0x8000000000008080, 2147483649, 0x8000000080008008]
RotationConstants = [[0, 1, 62, 28, 27], [36, 44, 6, 55, 20], [3, 10, 43, 25, 39], [41, 45, 15, 21, 8],
                     [18, 2, 61, 56, 14]]
Masks = [(1 << i) - 1 for i in range(65)]


def bits2bytes(x): return (int(x) + 7) // 8


def rol(value, left, bits): top = value >> bits - left;bot = (value & Masks[bits - left]) << left;return bot | top


def ror(value, right, bits): top = value >> right;bot = (value & Masks[right]) << bits - right;return bot | top


def multirate_padding(used_bytes, align_bytes):
    padlen = align_bytes - used_bytes
    if padlen == 0: padlen = align_bytes
    if padlen == 1:
        return [129]
    else:
        return [1] + [0] * (padlen - 2) + [128]


def keccak_f(state):
    def round(A, RC):
        W, H = state.W, state.H;
        rangeW, rangeH = state.rangeW, state.rangeH;
        lanew = state.lanew;
        zero = state.zero;
        C = [reduce(xor, A[x]) for x in rangeW];
        D = [0] * W
        for x in rangeW:
            D[x] = C[(x - 1) % W] ^ rol(C[(x + 1) % W], 1, lanew)
            for y in rangeH: A[x][y] ^= D[x]
        B = zero()
        for x in rangeW:
            for y in rangeH: B[y % W][(2 * x + 3 * y) % H] = rol(A[x][y], RotationConstants[y][x], lanew)
        for x in rangeW:
            for y in rangeH: A[x][y] = B[x][y] ^ ~ B[(x + 1) % W][y] & B[(x + 2) % W][y]
        A[0][0] ^= RC

    l = int(log(state.lanew, 2));
    nr = 12 + 2 * l
    for ir in xrange(nr): round(state.s, RoundConstants[ir])


class KeccakState:
    W = 5;
    H = 5;
    rangeW = range(W);
    rangeH = range(H)

    @staticmethod
    def zero():
        return [[0] * KeccakState.W for x in KeccakState.rangeH]

    @staticmethod
    def format(st):
        rows = []

        def fmt(x):
            return '%016x' % x

        for y in KeccakState.rangeH:
            row = []
            for x in KeccakState.rangeW:
                row.append(fmt(st[x][y]))
            rows.append(' '.join(row))
        return '\n'.join(rows)

    @staticmethod
    def lane2bytes(s, w):
        o = []
        for b in range(0, w, 8): o.append(s >> b & 255)
        return o

    @staticmethod
    def bytes2lane(bb):
        r = 0
        for b in reversed(bb): r = r << 8 | b
        return r

    @staticmethod
    def bytes2str(bb):
        return str_to_bytes('').join(map(chrsix, bb))

    @staticmethod
    def str2bytes(ss):
        return map(ordsix, ss)

    def __init__(self, bitrate, b):
        self.bitrate = bitrate;
        self.b = b;
        assert self.bitrate % 8 == 0;
        self.bitrate_bytes = bits2bytes(
            self.bitrate);
        assert self.b % 25 == 0;
        self.lanew = self.b // 25;
        self.s = KeccakState.zero()

    def __str__(self):
        return KeccakState.format(self.s)

    def absorb(self, bb):
        assert len(bb) == self.bitrate_bytes;
        bb += [0] * bits2bytes(self.b - self.bitrate);
        i = 0
        for y in self.rangeH:
            for x in self.rangeW: self.s[x][y] ^= KeccakState.bytes2lane(bb[i:i + 8]);i += 8

    def squeeze(self):
        return self.get_bytes()[:self.bitrate_bytes]

    def get_bytes(self):
        out = [0] * bits2bytes(self.b);
        i = 0
        for y in self.rangeH:
            for x in self.rangeW: v = KeccakState.lane2bytes(self.s[x][y], self.lanew);out[i:i + 8] = v;i += 8
        return out

    def set_bytes(self, bb):
        i = 0
        for y in self.rangeH:
            for x in self.rangeW: self.s[x][y] = KeccakState.bytes2lane(bb[i:i + 8]);i += 8


class KeccakSponge:
    def __init__(self, bitrate, width, padfn, permfn):
        self.state = KeccakState(bitrate, width);
        self.padfn = padfn;
        self.permfn = permfn;
        self.buffer = []

    def copy(self):
        return deepcopy(self)

    def absorb_block(self, bb):
        assert len(bb) == self.state.bitrate_bytes;
        self.state.absorb(bb);
        self.permfn(self.state)

    def absorb(self, s):
        self.buffer += KeccakState.str2bytes(s)
        while len(self.buffer) >= self.state.bitrate_bytes: self.absorb_block(
            self.buffer[:self.state.bitrate_bytes]);self.buffer = self.buffer[self.state.bitrate_bytes:]

    def absorb_final(self):
        padded = self.buffer + self.padfn(len(self.buffer), self.state.bitrate_bytes);
        self.absorb_block(
            padded);
        self.buffer = []

    def squeeze_once(self):
        rc = self.state.squeeze();
        self.permfn(self.state);
        return rc

    def squeeze(self, l):
        Z = self.squeeze_once()
        while len(Z) < l: Z += self.squeeze_once()
        return Z[:l]


class KeccakHash:
    def __init__(self, bitrate_bits, capacity_bits, output_bits): assert bitrate_bits + capacity_bits in (25, 50, 100,
                                                                                                          200, 400, 800,
                                                                                                          1600);self.sponge = KeccakSponge(
        bitrate_bits, bitrate_bits + capacity_bits, multirate_padding,
        keccak_f);assert output_bits % 8 == 0;self.digest_size = bits2bytes(output_bits);self.block_size = bits2bytes(
        bitrate_bits)

    def __repr__(
            self): inf = self.sponge.state.bitrate, self.sponge.state.b - self.sponge.state.bitrate, self.digest_size * 8;return '<KeccakHash with r=%d, c=%d, image=%d>' % inf

    def copy(self): return deepcopy(self)

    def update(self, s): self.sponge.absorb(s)

    def digest(self): finalised = self.sponge.copy();finalised.absorb_final();digest = finalised.squeeze(
        self.digest_size);return KeccakState.bytes2str(digest)

    def hexdigest(self): return binascii.hexlify(self.digest())

    @staticmethod
    def preset(bitrate_bits, capacity_bits, output_bits):
        def create(initial_input=None):
            h = KeccakHash(bitrate_bits, capacity_bits, output_bits)
            if not (initial_input is None): h.update(initial_input)
            return h

        return create


Keccak256 = KeccakHash.preset(1088, 512, 256)


########################
########################

########################
# begin of aes.py code #
########################

# from the SlowAES project, http://code.google.com/p/slowaes (aes.py)

def append_PKCS7_padding(s):
    """return s padded to a multiple of 16-bytes by PKCS7 padding"""
    numpads = 16 - (len(s) % 16)
    return s + numpads * chrsix(numpads)


def strip_PKCS7_padding(s):
    """return s stripped of PKCS7 padding"""
    if len(s) % 16 or not s:
        raise ValueError("String of len %d can't be PCKS7-padded" % len(s))
    numpads = ordsix(s[-1])
    if numpads > 16:
        raise ValueError("String ending with %r can't be PCKS7-padded" % s[-1])
    return s[:-numpads]


class AES(object):
    # valid key sizes
    keySize = dict(SIZE_128=16, SIZE_192=24, SIZE_256=32)

    # Rijndael S-box
    sbox = [0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67,
            0x2b, 0xfe, 0xd7, 0xab, 0x76, 0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59,
            0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0, 0xb7,
            0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1,
            0x71, 0xd8, 0x31, 0x15, 0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05,
            0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75, 0x09, 0x83,
            0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29,
            0xe3, 0x2f, 0x84, 0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b,
            0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf, 0xd0, 0xef, 0xaa,
            0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c,
            0x9f, 0xa8, 0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc,
            0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2, 0xcd, 0x0c, 0x13, 0xec,
            0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19,
            0x73, 0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee,
            0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb, 0xe0, 0x32, 0x3a, 0x0a, 0x49,
            0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
            0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4,
            0xea, 0x65, 0x7a, 0xae, 0x08, 0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6,
            0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a, 0x70,
            0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9,
            0x86, 0xc1, 0x1d, 0x9e, 0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e,
            0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf, 0x8c, 0xa1,
            0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0,
            0x54, 0xbb, 0x16]

    # Rijndael Inverted S-box
    rsbox = [0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38, 0xbf, 0x40, 0xa3,
             0x9e, 0x81, 0xf3, 0xd7, 0xfb, 0x7c, 0xe3, 0x39, 0x82, 0x9b, 0x2f,
             0xff, 0x87, 0x34, 0x8e, 0x43, 0x44, 0xc4, 0xde, 0xe9, 0xcb, 0x54,
             0x7b, 0x94, 0x32, 0xa6, 0xc2, 0x23, 0x3d, 0xee, 0x4c, 0x95, 0x0b,
             0x42, 0xfa, 0xc3, 0x4e, 0x08, 0x2e, 0xa1, 0x66, 0x28, 0xd9, 0x24,
             0xb2, 0x76, 0x5b, 0xa2, 0x49, 0x6d, 0x8b, 0xd1, 0x25, 0x72, 0xf8,
             0xf6, 0x64, 0x86, 0x68, 0x98, 0x16, 0xd4, 0xa4, 0x5c, 0xcc, 0x5d,
             0x65, 0xb6, 0x92, 0x6c, 0x70, 0x48, 0x50, 0xfd, 0xed, 0xb9, 0xda,
             0x5e, 0x15, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84, 0x90, 0xd8, 0xab,
             0x00, 0x8c, 0xbc, 0xd3, 0x0a, 0xf7, 0xe4, 0x58, 0x05, 0xb8, 0xb3,
             0x45, 0x06, 0xd0, 0x2c, 0x1e, 0x8f, 0xca, 0x3f, 0x0f, 0x02, 0xc1,
             0xaf, 0xbd, 0x03, 0x01, 0x13, 0x8a, 0x6b, 0x3a, 0x91, 0x11, 0x41,
             0x4f, 0x67, 0xdc, 0xea, 0x97, 0xf2, 0xcf, 0xce, 0xf0, 0xb4, 0xe6,
             0x73, 0x96, 0xac, 0x74, 0x22, 0xe7, 0xad, 0x35, 0x85, 0xe2, 0xf9,
             0x37, 0xe8, 0x1c, 0x75, 0xdf, 0x6e, 0x47, 0xf1, 0x1a, 0x71, 0x1d,
             0x29, 0xc5, 0x89, 0x6f, 0xb7, 0x62, 0x0e, 0xaa, 0x18, 0xbe, 0x1b,
             0xfc, 0x56, 0x3e, 0x4b, 0xc6, 0xd2, 0x79, 0x20, 0x9a, 0xdb, 0xc0,
             0xfe, 0x78, 0xcd, 0x5a, 0xf4, 0x1f, 0xdd, 0xa8, 0x33, 0x88, 0x07,
             0xc7, 0x31, 0xb1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xec, 0x5f, 0x60,
             0x51, 0x7f, 0xa9, 0x19, 0xb5, 0x4a, 0x0d, 0x2d, 0xe5, 0x7a, 0x9f,
             0x93, 0xc9, 0x9c, 0xef, 0xa0, 0xe0, 0x3b, 0x4d, 0xae, 0x2a, 0xf5,
             0xb0, 0xc8, 0xeb, 0xbb, 0x3c, 0x83, 0x53, 0x99, 0x61, 0x17, 0x2b,
             0x04, 0x7e, 0xba, 0x77, 0xd6, 0x26, 0xe1, 0x69, 0x14, 0x63, 0x55,
             0x21, 0x0c, 0x7d]

    def getSBoxValue(self, num):
        """Retrieves a given S-Box Value"""
        return self.sbox[num]

    def getSBoxInvert(self, num):
        """Retrieves a given Inverted S-Box Value"""
        return self.rsbox[num]

    def rotate(self, word):
        """ Rijndael's key schedule rotate operation.

		Rotate a word eight bits to the left: eg, rotate(1d2c3a4f) == 2c3a4f1d
		Word is an char list of size 4 (32 bits overall).
		"""
        return word[1:] + word[:1]

    # Rijndael Rcon
    Rcon = [0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36,
            0x6c, 0xd8, 0xab, 0x4d, 0x9a, 0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97,
            0x35, 0x6a, 0xd4, 0xb3, 0x7d, 0xfa, 0xef, 0xc5, 0x91, 0x39, 0x72,
            0xe4, 0xd3, 0xbd, 0x61, 0xc2, 0x9f, 0x25, 0x4a, 0x94, 0x33, 0x66,
            0xcc, 0x83, 0x1d, 0x3a, 0x74, 0xe8, 0xcb, 0x8d, 0x01, 0x02, 0x04,
            0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36, 0x6c, 0xd8, 0xab, 0x4d,
            0x9a, 0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97, 0x35, 0x6a, 0xd4, 0xb3,
            0x7d, 0xfa, 0xef, 0xc5, 0x91, 0x39, 0x72, 0xe4, 0xd3, 0xbd, 0x61,
            0xc2, 0x9f, 0x25, 0x4a, 0x94, 0x33, 0x66, 0xcc, 0x83, 0x1d, 0x3a,
            0x74, 0xe8, 0xcb, 0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40,
            0x80, 0x1b, 0x36, 0x6c, 0xd8, 0xab, 0x4d, 0x9a, 0x2f, 0x5e, 0xbc,
            0x63, 0xc6, 0x97, 0x35, 0x6a, 0xd4, 0xb3, 0x7d, 0xfa, 0xef, 0xc5,
            0x91, 0x39, 0x72, 0xe4, 0xd3, 0xbd, 0x61, 0xc2, 0x9f, 0x25, 0x4a,
            0x94, 0x33, 0x66, 0xcc, 0x83, 0x1d, 0x3a, 0x74, 0xe8, 0xcb, 0x8d,
            0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36, 0x6c,
            0xd8, 0xab, 0x4d, 0x9a, 0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97, 0x35,
            0x6a, 0xd4, 0xb3, 0x7d, 0xfa, 0xef, 0xc5, 0x91, 0x39, 0x72, 0xe4,
            0xd3, 0xbd, 0x61, 0xc2, 0x9f, 0x25, 0x4a, 0x94, 0x33, 0x66, 0xcc,
            0x83, 0x1d, 0x3a, 0x74, 0xe8, 0xcb, 0x8d, 0x01, 0x02, 0x04, 0x08,
            0x10, 0x20, 0x40, 0x80, 0x1b, 0x36, 0x6c, 0xd8, 0xab, 0x4d, 0x9a,
            0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97, 0x35, 0x6a, 0xd4, 0xb3, 0x7d,
            0xfa, 0xef, 0xc5, 0x91, 0x39, 0x72, 0xe4, 0xd3, 0xbd, 0x61, 0xc2,
            0x9f, 0x25, 0x4a, 0x94, 0x33, 0x66, 0xcc, 0x83, 0x1d, 0x3a, 0x74,
            0xe8, 0xcb]

    def getRconValue(self, num):
        """Retrieves a given Rcon Value"""
        return self.Rcon[num]

    def core(self, word, iteration):
        """Key schedule core."""
        # rotate the 32-bit word 8 bits to the left
        word = self.rotate(word)
        # apply S-Box substitution on all 4 parts of the 32-bit word
        for i in range(4):
            word[i] = self.getSBoxValue(word[i])
        # XOR the output of the rcon operation with i to the first part
        # (leftmost) only
        word[0] = word[0] ^ self.getRconValue(iteration)
        return word

    def expandKey(self, key, size, expandedKeySize):
        """Rijndael's key expansion.

		Expands an 128,192,256 key into an 176,208,240 bytes key

		expandedKey is a char list of large enough size,
		key is the non-expanded key.
		"""
        # current expanded keySize, in bytes
        currentSize = 0
        rconIteration = 1
        expandedKey = [0] * expandedKeySize

        # set the 16, 24, 32 bytes of the expanded key to the input key
        for j in range(size):
            expandedKey[j] = key[j]
        currentSize += size

        while currentSize < expandedKeySize:
            # assign the previous 4 bytes to the temporary value t
            t = expandedKey[currentSize - 4:currentSize]

            # every 16,24,32 bytes we apply the core schedule to t
            # and increment rconIteration afterwards
            if currentSize % size == 0:
                t = self.core(t, rconIteration)
                rconIteration += 1
            # For 256-bit keys, we add an extra sbox to the calculation
            if size == self.keySize["SIZE_256"] and ((currentSize % size) == 16):
                for l in range(4): t[l] = self.getSBoxValue(t[l])

            # We XOR t with the four-byte block 16,24,32 bytes before the new
            # expanded key.  This becomes the next four bytes in the expanded
            # key.
            for m in range(4):
                expandedKey[currentSize] = expandedKey[currentSize - size] ^ \
                                           t[m]
                currentSize += 1

        return expandedKey

    def addRoundKey(self, state, roundKey):
        """Adds (XORs) the round key to the state."""
        for i in range(16):
            state[i] ^= roundKey[i]
        return state

    def createRoundKey(self, expandedKey, roundKeyPointer):
        """Create a round key.
		Creates a round key from the given expanded key and the
		position within the expanded key.
		"""
        roundKey = [0] * 16
        for i in range(4):
            for j in range(4):
                roundKey[j * 4 + i] = expandedKey[roundKeyPointer + i * 4 + j]
        return roundKey

    def galois_multiplication(self, a, b):
        """Galois multiplication of 8 bit characters a and b."""
        p = 0
        for counter in range(8):
            if b & 1: p ^= a
            hi_bit_set = a & 0x80
            a <<= 1
            # keep a 8 bit
            a &= 0xFF
            if hi_bit_set:
                a ^= 0x1b
            b >>= 1
        return p

    #
    # substitute all the values from the state with the value in the SBox
    # using the state value as index for the SBox
    #
    def subBytes(self, state, isInv):
        if isInv:
            getter = self.getSBoxInvert
        else:
            getter = self.getSBoxValue
        for i in range(16): state[i] = getter(state[i])
        return state

    # iterate over the 4 rows and call shiftRow() with that row
    def shiftRows(self, state, isInv):
        for i in range(4):
            state = self.shiftRow(state, i * 4, i, isInv)
        return state

    # each iteration shifts the row to the left by 1
    def shiftRow(self, state, statePointer, nbr, isInv):
        for i in range(nbr):
            if isInv:
                state[statePointer:statePointer + 4] = \
                    state[statePointer + 3:statePointer + 4] + \
                    state[statePointer:statePointer + 3]
            else:
                state[statePointer:statePointer + 4] = \
                    state[statePointer + 1:statePointer + 4] + \
                    state[statePointer:statePointer + 1]
        return state

    # galois multiplication of the 4x4 matrix
    def mixColumns(self, state, isInv):
        # iterate over the 4 columns
        for i in range(4):
            # construct one column by slicing over the 4 rows
            column = state[i:i + 16:4]
            # apply the mixColumn on one column
            column = self.mixColumn(column, isInv)
            # put the values back into the state
            state[i:i + 16:4] = column

        return state

    # galois multiplication of 1 column of the 4x4 matrix
    def mixColumn(self, column, isInv):
        if isInv:
            mult = [14, 9, 13, 11]
        else:
            mult = [2, 1, 1, 3]
        cpy = list(column)
        g = self.galois_multiplication

        column[0] = g(cpy[0], mult[0]) ^ g(cpy[3], mult[1]) ^ \
                    g(cpy[2], mult[2]) ^ g(cpy[1], mult[3])
        column[1] = g(cpy[1], mult[0]) ^ g(cpy[0], mult[1]) ^ \
                    g(cpy[3], mult[2]) ^ g(cpy[2], mult[3])
        column[2] = g(cpy[2], mult[0]) ^ g(cpy[1], mult[1]) ^ \
                    g(cpy[0], mult[2]) ^ g(cpy[3], mult[3])
        column[3] = g(cpy[3], mult[0]) ^ g(cpy[2], mult[1]) ^ \
                    g(cpy[1], mult[2]) ^ g(cpy[0], mult[3])
        return column

    # applies the 4 operations of the forward round in sequence
    def aes_round(self, state, roundKey):
        state = self.subBytes(state, False)
        state = self.shiftRows(state, False)
        state = self.mixColumns(state, False)
        state = self.addRoundKey(state, roundKey)
        return state

    # applies the 4 operations of the inverse round in sequence
    def aes_invRound(self, state, roundKey):
        state = self.shiftRows(state, True)
        state = self.subBytes(state, True)
        state = self.addRoundKey(state, roundKey)
        state = self.mixColumns(state, True)
        return state

    # Perform the initial operations, the standard round, and the final
    # operations of the forward aes, creating a round key for each round
    def aes_main(self, state, expandedKey, nbrRounds):
        state = self.addRoundKey(state, self.createRoundKey(expandedKey, 0))
        i = 1
        while i < nbrRounds:
            state = self.aes_round(state,
                                   self.createRoundKey(expandedKey, 16 * i))
            i += 1
        state = self.subBytes(state, False)
        state = self.shiftRows(state, False)
        state = self.addRoundKey(state,
                                 self.createRoundKey(expandedKey, 16 * nbrRounds))
        return state

    # Perform the initial operations, the standard round, and the final
    # operations of the inverse aes, creating a round key for each round
    def aes_invMain(self, state, expandedKey, nbrRounds):
        state = self.addRoundKey(state,
                                 self.createRoundKey(expandedKey, 16 * nbrRounds))
        i = nbrRounds - 1
        while i > 0:
            state = self.aes_invRound(state,
                                      self.createRoundKey(expandedKey, 16 * i))
            i -= 1
        state = self.shiftRows(state, True)
        state = self.subBytes(state, True)
        state = self.addRoundKey(state, self.createRoundKey(expandedKey, 0))
        return state

    # encrypts a 128 bit input block against the given key of size specified
    def encrypt(self, iput, key, size):
        output = [0] * 16
        # the number of rounds
        nbrRounds = 0
        # the 128 bit block to encode
        block = [0] * 16
        # set the number of rounds
        if size == self.keySize["SIZE_128"]:
            nbrRounds = 10
        elif size == self.keySize["SIZE_192"]:
            nbrRounds = 12
        elif size == self.keySize["SIZE_256"]:
            nbrRounds = 14
        else:
            return None

        # the expanded keySize
        expandedKeySize = 16 * (nbrRounds + 1)

        # Set the block values, for the block:
        # a0,0 a0,1 a0,2 a0,3
        # a1,0 a1,1 a1,2 a1,3
        # a2,0 a2,1 a2,2 a2,3
        # a3,0 a3,1 a3,2 a3,3
        # the mapping order is a0,0 a1,0 a2,0 a3,0 a0,1 a1,1 ... a2,3 a3,3
        #
        # iterate over the columns
        for i in range(4):
            # iterate over the rows
            for j in range(4):
                block[(i + (j * 4))] = iput[(i * 4) + j]

        # expand the key into an 176, 208, 240 bytes key
        # the expanded key
        expandedKey = self.expandKey(key, size, expandedKeySize)

        # encrypt the block using the expandedKey
        block = self.aes_main(block, expandedKey, nbrRounds)

        # unmap the block again into the output
        for k in range(4):
            # iterate over the rows
            for l in range(4):
                output[(k * 4) + l] = block[(k + (l * 4))]
        return output

    # decrypts a 128 bit input block against the given key of size specified
    def decrypt(self, iput, key, size):
        output = [0] * 16
        # the number of rounds
        nbrRounds = 0
        # the 128 bit block to decode
        block = [0] * 16
        # set the number of rounds
        if size == self.keySize["SIZE_128"]:
            nbrRounds = 10
        elif size == self.keySize["SIZE_192"]:
            nbrRounds = 12
        elif size == self.keySize["SIZE_256"]:
            nbrRounds = 14
        else:
            return None

        # the expanded keySize
        expandedKeySize = 16 * (nbrRounds + 1)

        # Set the block values, for the block:
        # a0,0 a0,1 a0,2 a0,3
        # a1,0 a1,1 a1,2 a1,3
        # a2,0 a2,1 a2,2 a2,3
        # a3,0 a3,1 a3,2 a3,3
        # the mapping order is a0,0 a1,0 a2,0 a3,0 a0,1 a1,1 ... a2,3 a3,3

        # iterate over the columns
        for i in range(4):
            # iterate over the rows
            for j in range(4):
                block[(i + (j * 4))] = iput[(i * 4) + j]
        # expand the key into an 176, 208, 240 bytes key
        expandedKey = self.expandKey(key, size, expandedKeySize)
        # decrypt the block using the expandedKey
        block = self.aes_invMain(block, expandedKey, nbrRounds)
        # unmap the block again into the output
        for k in range(4):
            # iterate over the rows
            for l in range(4):
                output[(k * 4) + l] = block[(k + (l * 4))]
        return output


class AESModeOfOperation(object):
    aes = AES()

    # structure of supported modes of operation
    modeOfOperation = dict(OFB=0, CFB=1, CBC=2)

    # converts a 16 character string into a number array
    def convertString(self, string, start, end, mode):
        if end - start > 16: end = start + 16
        if mode == self.modeOfOperation["CBC"]:
            ar = [0] * 16
        else:
            ar = []

        i = start
        j = 0
        while len(ar) < end - start:
            ar.append(0)
        while i < end:
            ar[j] = ordsix(string[i])
            j += 1
            i += 1
        return ar

    # Mode of Operation Encryption
    # stringIn - Input String
    # mode - mode of type modeOfOperation
    # hexKey - a hex key of the bit length size
    # size - the bit length of the key
    # hexIV - the 128 bit hex Initilization Vector
    def encrypt(self, stringIn, mode, key, size, IV):
        if len(key) % size:
            return None
        if len(IV) % 16:
            return None
        # the AES input/output
        plaintext = []
        iput = [0] * 16
        output = []
        ciphertext = [0] * 16
        # the output cipher string
        cipherOut = []
        # char firstRound
        firstRound = True
        if stringIn != None:
            for j in range(int(math.ceil(float(len(stringIn)) // 16))):
                start = j * 16
                end = j * 16 + 16
                if end > len(stringIn):
                    end = len(stringIn)
                plaintext = self.convertString(stringIn, start, end, mode)
                # print('PT@%s:%s' % (j, plaintext))
                if mode == self.modeOfOperation["CFB"]:
                    if firstRound:
                        output = self.aes.encrypt(IV, key, size)
                        firstRound = False
                    else:
                        output = self.aes.encrypt(iput, key, size)
                    for i in range(16):
                        if len(plaintext) - 1 < i:
                            ciphertext[i] = 0 ^ output[i]
                        elif len(output) - 1 < i:
                            ciphertext[i] = plaintext[i] ^ 0
                        elif len(plaintext) - 1 < i and len(output) < i:
                            ciphertext[i] = 0 ^ 0
                        else:
                            ciphertext[i] = plaintext[i] ^ output[i]
                    for k in range(end - start):
                        cipherOut.append(ciphertext[k])
                    iput = ciphertext
                elif mode == self.modeOfOperation["OFB"]:
                    if firstRound:
                        output = self.aes.encrypt(IV, key, size)
                        firstRound = False
                    else:
                        output = self.aes.encrypt(iput, key, size)
                    for i in range(16):
                        if len(plaintext) - 1 < i:
                            ciphertext[i] = 0 ^ output[i]
                        elif len(output) - 1 < i:
                            ciphertext[i] = plaintext[i] ^ 0
                        elif len(plaintext) - 1 < i and len(output) < i:
                            ciphertext[i] = 0 ^ 0
                        else:
                            ciphertext[i] = plaintext[i] ^ output[i]
                    for k in range(end - start):
                        cipherOut.append(ciphertext[k])
                    iput = output
                elif mode == self.modeOfOperation["CBC"]:
                    for i in range(16):
                        if firstRound:
                            iput[i] = plaintext[i] ^ IV[i]
                        else:
                            iput[i] = plaintext[i] ^ ciphertext[i]
                    # print('IP@%s:%s' % (j, iput))
                    firstRound = False
                    ciphertext = self.aes.encrypt(iput, key, size)
                    # always 16 bytes because of the padding for CBC
                    for k in range(16):
                        cipherOut.append(ciphertext[k])
        return mode, len(stringIn), cipherOut

    # Mode of Operation Decryption
    # cipherIn - Encrypted String
    # originalsize - The unencrypted string length - required for CBC
    # mode - mode of type modeOfOperation
    # key - a number array of the bit length size
    # size - the bit length of the key
    # IV - the 128 bit number array Initilization Vector
    def decrypt(self, cipherIn, originalsize, mode, key, size, IV):
        # cipherIn = unescCtrlChars(cipherIn)
        if len(key) % size:
            return None
        if len(IV) % 16:
            return None
        # the AES input/output
        ciphertext = []
        iput = []
        output = []
        plaintext = [0] * 16
        # the output plain text string
        stringOut = b''
        # char firstRound
        firstRound = True
        if cipherIn != None:
            for j in range(int(math.ceil(float(len(cipherIn)) // 16))):
                start = j * 16
                end = j * 16 + 16
                if j * 16 + 16 > len(cipherIn):
                    end = len(cipherIn)
                ciphertext = cipherIn[start:end]
                if mode == self.modeOfOperation["CFB"]:
                    if firstRound:
                        output = self.aes.encrypt(IV, key, size)
                        firstRound = False
                    else:
                        output = self.aes.encrypt(iput, key, size)
                    for i in range(16):
                        if len(output) - 1 < i:
                            plaintext[i] = 0 ^ ciphertext[i]
                        elif len(ciphertext) - 1 < i:
                            plaintext[i] = output[i] ^ 0
                        elif len(output) - 1 < i and len(ciphertext) < i:
                            plaintext[i] = 0 ^ 0
                        else:
                            plaintext[i] = output[i] ^ ciphertext[i]
                    for k in range(end - start):
                        stringOut += chrsix(plaintext[k])
                    iput = ciphertext
                elif mode == self.modeOfOperation["OFB"]:
                    if firstRound:
                        output = self.aes.encrypt(IV, key, size)
                        firstRound = False
                    else:
                        output = self.aes.encrypt(iput, key, size)
                    for i in range(16):
                        if len(output) - 1 < i:
                            plaintext[i] = 0 ^ ciphertext[i]
                        elif len(ciphertext) - 1 < i:
                            plaintext[i] = output[i] ^ 0
                        elif len(output) - 1 < i and len(ciphertext) < i:
                            plaintext[i] = 0 ^ 0
                        else:
                            plaintext[i] = output[i] ^ ciphertext[i]
                    for k in range(end - start):
                        stringOut += chrsix(plaintext[k])
                    iput = output
                elif mode == self.modeOfOperation["CBC"]:
                    output = self.aes.decrypt(ciphertext, key, size)
                    for i in range(16):
                        if firstRound:
                            plaintext[i] = IV[i] ^ output[i]
                        else:
                            plaintext[i] = iput[i] ^ output[i]
                    firstRound = False
                    if not (originalsize is None) and originalsize < end:
                        for k in range(originalsize - start):
                            stringOut += chrsix(plaintext[k])
                    else:
                        for k in range(end - start):
                            stringOut += chrsix(plaintext[k])
                    iput = ciphertext
        return stringOut


######################
# end of aes.py code #
######################

###################################
# pywallet crypter implementation #
###################################

class Crypter_pycrypto(object):
    def SetKeyFromPassphrase(self, vKeyData, vSalt, nDerivIterations, nDerivationMethod):
        if nDerivationMethod != 0:
            return 0
        try:
            data = str_to_bytes(vKeyData) + str_to_bytes(vSalt)
            for i in xrange(nDerivIterations):
                data = hashlib.sha512(data).digest()
            self.SetKey(data[0:32])
            self.SetIV(data[32:32 + 16])
            return len(data)
        except Exception as e:
            print(f"Error in Crypter_pycrypto.SetKeyFromPassphrase: {str(e)}")
            print(f"vKeyData type: {type(vKeyData)}, value: {vKeyData}")
            print(f"vSalt type: {type(vSalt)}, value: {vSalt}")
            return 0

    def SetKey(self, key):
        self.chKey = key

    def SetIV(self, iv):
        self.chIV = iv[0:16]

    def Encrypt(self, data):
        return AES.new(self.chKey, AES.MODE_CBC, self.chIV).encrypt(append_PKCS7_padding(data))

    def Decrypt(self, data):
        return AES.new(self.chKey, AES.MODE_CBC, self.chIV).decrypt(data)[0:32]


class Crypter_ssl(object):
    def __init__(self):
        self.chKey = ctypes.create_string_buffer(32)
        self.chIV = ctypes.create_string_buffer(16)

    def SetKeyFromPassphrase(self, vKeyData, vSalt, nDerivIterations, nDerivationMethod):
        if nDerivationMethod != 0:
            return 0
        try:
            vKeyData_bytes = str_to_bytes(vKeyData)
            vSalt_bytes = str_to_bytes(vSalt)
            strKeyData = ctypes.create_string_buffer(vKeyData_bytes)
            chSalt = ctypes.create_string_buffer(vSalt_bytes)
            return ssl.EVP_BytesToKey(ssl.EVP_aes_256_cbc(), ssl.EVP_sha512(), chSalt, strKeyData,
                                      len(vKeyData_bytes), nDerivIterations, ctypes.byref(self.chKey), ctypes.byref(self.chIV))
        except Exception as e:
            print(f"Error in SetKeyFromPassphrase: {str(e)}")
            print(f"vKeyData type: {type(vKeyData)}, value: {vKeyData}")
            print(f"vSalt type: {type(vSalt)}, value: {vSalt}")
            return 0

    def SetKey(self, key):
        self.chKey = ctypes.create_string_buffer(str_to_bytes(key))

    def SetIV(self, iv):
        self.chIV = ctypes.create_string_buffer(str_to_bytes(iv))

    def Encrypt(self, data):
        buf = ctypes.create_string_buffer(len(data) + 16)
        written = ctypes.c_int(0)
        final = ctypes.c_int(0)
        ctx = ssl.EVP_CIPHER_CTX_new()
        ssl.EVP_CIPHER_CTX_init(ctx)
        ssl.EVP_EncryptInit_ex(ctx, ssl.EVP_aes_256_cbc(), None, self.chKey, self.chIV)
        ssl.EVP_EncryptUpdate(ctx, buf, ctypes.byref(written), data, len(data))
        output = buf.raw[:written.value]
        ssl.EVP_EncryptFinal_ex(ctx, buf, ctypes.byref(final))
        output += buf.raw[:final.value]
        return output

    def Decrypt(self, data):
        buf = ctypes.create_string_buffer(len(data) + 16)
        written = ctypes.c_int(0)
        final = ctypes.c_int(0)
        ctx = ssl.EVP_CIPHER_CTX_new()
        ssl.EVP_CIPHER_CTX_init(ctx)
        ssl.EVP_DecryptInit_ex(ctx, ssl.EVP_aes_256_cbc(), None, self.chKey, self.chIV)
        ssl.EVP_DecryptUpdate(ctx, buf, ctypes.byref(written), data, len(data))
        output = buf.raw[:written.value]
        ssl.EVP_DecryptFinal_ex(ctx, buf, ctypes.byref(final))
        output += buf.raw[:final.value]
        return output


class Crypter_pure(object):
    def __init__(self):
        self.m = AESModeOfOperation()
        self.cbc = self.m.modeOfOperation["CBC"]
        self.sz = self.m.aes.keySize["SIZE_256"]

    def SetKeyFromPassphrase(self, vKeyData, vSalt, nDerivIterations, nDerivationMethod):
        if nDerivationMethod != 0:
            return 0
        try:
            data = str_to_bytes(vKeyData) + str_to_bytes(vSalt)
            for i in xrange(nDerivIterations):
                data = hashlib.sha512(data).digest()
            self.SetKey(data[0:32])
            self.SetIV(data[32:32 + 16])
            return len(data)
        except Exception as e:
            print(f"Error in Crypter_pure.SetKeyFromPassphrase: {str(e)}")
            print(f"vKeyData type: {type(vKeyData)}, value: {vKeyData}")
            print(f"vSalt type: {type(vSalt)}, value: {vSalt}")
            return 0

    def SetKey(self, key):
        self.chKey = [ordsix(i) for i in key]

    def SetIV(self, iv):
        self.chIV = [ordsix(i) for i in iv]

    def Encrypt(self, data):
        mode, size, cypher = self.m.encrypt(append_PKCS7_padding(data), self.cbc, self.chKey, self.sz, self.chIV)
        return b''.join(map(chrsix, cypher))

    def Decrypt(self, data):
        chData = [ordsix(i) for i in data]
        return self.m.decrypt(chData, self.sz, self.cbc, self.chKey, self.sz, self.chIV)


crypter = None
if crypter is None:
    try:
        from pycryptodome.Cipher import AES

        crypter = Crypter_pycrypto()
    except ImportError:
        try:
            import ctypes
            import ctypes.util

            ssl = ctypes.cdll.LoadLibrary(ctypes.util.find_library('ssl') or 'libeay32')
            crypter = Crypter_ssl()
        except:
            crypter = Crypter_pure()
            logging.warning("pycrypto or libssl not found, decryption may be slow")


##########################################
# end of pywallet crypter implementation #
##########################################

def bytes_to_int(bytes):
    result = 0
    for b in bytes:
        result = result * 256 + ordsix(b)
    return result


def int_to_bytes(value, length=None):
    if not length and value == 0:
        result = [0]
    else:
        result = []
        for i in range(0, length or 1 + int(math.log(value, 2 ** 8))):
            result.append(value >> (i * 8) & 0xff)
        result.reverse()
    return str(bytearray(result))


# secp256k1

_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_r = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_b = 0x0000000000000000000000000000000000000000000000000000000000000007
_a = 0x0000000000000000000000000000000000000000000000000000000000000000
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
_Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8

try:
    import ecdsa
    from ecdsa import der

    curve_secp256k1 = ecdsa.ellipticcurve.CurveFp(_p, _a, _b)
    generator_secp256k1 = g = ecdsa.ellipticcurve.Point(curve_secp256k1, _Gx, _Gy, _r)
    randrange = random.SystemRandom().randrange
    secp256k1 = ecdsa.curves.Curve("secp256k1", curve_secp256k1, generator_secp256k1, (1, 3, 132, 0, 10))
    ecdsa.curves.curves.append(secp256k1)
except ImportError:
    missing_dep.append('ecdsa')


# python-ecdsa code (EC_KEY implementation)

class CurveFp(object):
    def __init__(self, p, a, b):
        self.__p = p
        self.__a = a
        self.__b = b

    def p(self):
        return self.__p

    def a(self):
        return self.__a

    def b(self):
        return self.__b

    def contains_point(self, x, y):
        return (y * y - (x * x * x + self.__a * x + self.__b)) % self.__p == 0

    def sqrt_root(self, x):
        return pow(x, (self.__p + 1) // 4, self.__p)

    def y_from_x(self, x, y_odd):
        y = self.sqrt_root((x * x * x + self.__a * x + self.__b) % self.__p)
        if (y % 2 == 1) == y_odd:
            return y
        else:
            return self.__p - y


class Point(object):
    def __init__(self, curve, x, y=None, order=None, y_odd=None):
        self.__curve = curve
        self.__x = x
        if y != None or curve == None:
            self.__y = y
        else:
            self.__y = self.__curve.y_from_x(self.__x, y_odd)
        self.__order = order
        if self.__curve: assert self.__curve.contains_point(self.__x, self.__y)
        if order: assert self * order == INFINITY

    def __add__(self, other):
        if other == INFINITY: return self
        if self == INFINITY: return other
        assert self.__curve == other.__curve
        if self.__x == other.__x:
            if (self.__y + other.__y) % self.__curve.p() == 0:
                return INFINITY
            else:
                return self.double()

        p = self.__curve.p()
        l = ((other.__y - self.__y) * \
             inverse_mod(other.__x - self.__x, p)) % p
        x3 = (l * l - self.__x - other.__x) % p
        y3 = (l * (self.__x - x3) - self.__y) % p
        return Point(self.__curve, x3, y3)

    def __mul__(self, other):
        def leftmost_bit(x):
            assert x > 0
            result = 1
            while result <= x: result = 2 * result
            return result // 2

        e = other
        if self.__order: e = e % self.__order
        if e == 0: return INFINITY
        if self == INFINITY: return INFINITY
        assert e > 0
        e3 = 3 * e
        negative_self = Point(self.__curve, self.__x, -self.__y, self.__order)
        i = leftmost_bit(e3) // 2
        result = self
        while i > 1:
            result = result.double()
            if (e3 & i) != 0 and (e & i) == 0: result = result + self
            if (e3 & i) == 0 and (e & i) != 0: result = result + negative_self
            i = i // 2
        return result

    def __rmul__(self, other):
        return self * other

    def __str__(self):
        if self == INFINITY: return "infinity"
        return "(%d,%d)" % (self.__x, self.__y)

    def double(self):
        if self == INFINITY:
            return INFINITY

        p = self.__curve.p()
        a = self.__curve.a()
        l = ((3 * self.__x * self.__x + a) * \
             inverse_mod(2 * self.__y, p)) % p
        x3 = (l * l - 2 * self.__x) % p
        y3 = (l * (self.__x - x3) - self.__y) % p
        return Point(self.__curve, x3, y3)

    def x(self):
        return self.__x

    def y(self):
        return self.__y

    def curve(self):
        return self.__curve

    def order(self):
        return self.__order


INFINITY = Point(None, None, None)
secp256k1_curve = CurveFp(_p, _a, _b)
secp256k1_generator = Point(secp256k1_curve, _Gx, _Gy, _r)


def inverse_mod(a, m):
    if a < 0 or m <= a: a = a % m
    c, d = a, m
    uc, vc, ud, vd = 1, 0, 0, 1
    while c != 0:
        q, c, d = divmod(d, c) + (c,)
        uc, vc, ud, vd = ud - q * uc, vd - q * vc, uc, vc
    assert d == 1
    if ud > 0:
        return ud
    else:
        return ud + m


class Signature(object):
    def __init__(self, r, s):
        self.r = r
        self.s = s


class Public_key(object):
    def __init__(self, generator, point, c=None):
        self.curve = generator.curve()
        self.generator = generator
        self.point = point
        self.compressed = c
        n = generator.order()
        if not n:
            raise RuntimeError("Generator point must have order.")
        if not n * point == INFINITY:
            raise RuntimeError("Generator point order is bad.")
        if point.x() < 0 or n <= point.x() or point.y() < 0 or n <= point.y():
            raise RuntimeError("Generator point has x or y out of range.")

    def verifies(self, hash, signature):
        G = self.generator
        n = G.order()
        r = signature.r
        s = signature.s
        if r < 1 or r > n - 1: return False
        if s < 1 or s > n - 1: return False
        c = inverse_mod(s, n)
        u1 = (hash * c) % n
        u2 = (r * c) % n
        xy = u1 * G + u2 * self.point
        v = xy.x() % n
        return v == r

    def ser(self):
        if self.compressed:
            pk = ('%02x' % (2 + (self.point.y() & 1))) + '%064x' % self.point.x()
        else:
            pk = '04%064x%064x' % (self.point.x(), self.point.y())

        return binascii.unhexlify(pk)

    def get_addr(self, v=0):
        return public_key_to_bc_address(self.ser(), v)

    @classmethod
    def from_ser(cls, g, ser):
        if len(ser) == 33:
            return cls(g, Point(g.curve(), bytes_to_int(ser[1:]), y_odd=ordsix(ser[0]) == 3), ordsix(ser[0]) < 4)
        elif len(ser) == 65:
            return cls(g, Point(g.curve(), bytes_to_int(ser[1:33]), bytes_to_int(ser[33:])), ordsix(ser[0]) < 4)
        raise Exception("Bad public key format: %s" % repr(ser))


class Private_key(object):
    def __init__(self, public_key, secret_multiplier):
        self.public_key = public_key
        self.secret_multiplier = secret_multiplier

    def der(self):
        hex_der_key = '06052b8104000a30740201010420' + \
                      '%064x' % self.secret_multiplier + \
                      'a00706052b8104000aa14403420004' + \
                      '%064x' % self.public_key.point.x() + \
                      '%064x' % self.public_key.point.y()
        return binascii.unhexlify(hex_der_key)

    def sign(self, hash, random_k):
        G = self.public_key.generator
        n = G.order()
        k = random_k % n
        p1 = k * G
        r = p1.x()
        if r == 0: raise RuntimeError("amazingly unlucky random number r")
        s = (inverse_mod(k, n) * \
             (hash + (self.secret_multiplier * r) % n)) % n
        if s == 0: raise RuntimeError("amazingly unlucky random number s")
        return Signature(r, s)


class EC_KEY(object):
    def __init__(self, secret):
        curve = CurveFp(_p, _a, _b)
        generator = Point(curve, _Gx, _Gy, _r)
        self.pubkey = Public_key(generator, generator * secret)
        self.privkey = Private_key(self.pubkey, secret)
        self.secret = secret


# end of python-ecdsa code

# pywallet openssl private key implementation

def i2d_ECPrivateKey(pkey, compressed=False):  # , crypted=True):
    part3 = 'a081a53081a2020101302c06072a8648ce3d0101022100'  # for uncompressed keys
    if compressed:
        if True:  # not crypted:  ## Bitcoin accepts both part3's for crypted wallets...
            part3 = 'a08185308182020101302c06072a8648ce3d0101022100'  # for compressed keys
        key = '3081d30201010420' + \
              '%064x' % pkey.secret + \
              part3 + \
              '%064x' % _p + \
              '3006040100040107042102' + \
              '%064x' % _Gx + \
              '022100' + \
              '%064x' % _r + \
              '020101a124032200'
    else:
        key = '308201130201010420' + \
              '%064x' % pkey.secret + \
              part3 + \
              '%064x' % _p + \
              '3006040100040107044104' + \
              '%064x' % _Gx + \
              '%064x' % _Gy + \
              '022100' + \
              '%064x' % _r + \
              '020101a144034200'

    return binascii.unhexlify(key) + i2o_ECPublicKey(pkey, compressed)


def i2o_ECPublicKey(pkey, compressed=False):
    # public keys are 65 bytes long (520 bits)
    # 0x04 + 32-byte X-coordinate + 32-byte Y-coordinate
    # 0x00 = point at infinity, 0x02 and 0x03 = compressed, 0x04 = uncompressed
    # compressed keys: <sign> <x> where <sign> is 0x02 if y is even and 0x03 if y is odd
    if compressed:
        if pkey.pubkey.point.y() & 1:
            key = '03' + '%064x' % pkey.pubkey.point.x()
        else:
            key = '02' + '%064x' % pkey.pubkey.point.x()
    else:
        key = '04' + \
              '%064x' % pkey.pubkey.point.x() + \
              '%064x' % pkey.pubkey.point.y()

    return binascii.unhexlify(key)


# bitcointools hashes and base58 implementation

def hash_160(public_key):
    md = hashlib.new('ripemd160')
    md.update(hashlib.sha256(public_key).digest())
    return md.digest()


def public_key_to_bc_address(public_key, v=None):
    if v == None:
        v = network.p2pkh_prefix
    h160 = hash_160(public_key)
    return hash_160_to_bc_address(h160, v)


def hash_160_to_bc_address(h160, v=None):
    if v == None:
        v = network.p2pkh_prefix
    vh160 = chrsix(v) + h160
    h = Hash(vh160)
    addr = vh160 + h[0:4]
    return b58encode(addr)


def bc_address_to_hash_160(addr):
    bytes = b58decode(addr, 25)
    return bytes[1:21]


__b58chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def b58encode(v, __b58chars=__b58chars):
    """ encode v, which is a string of bytes, to base58.
	"""
    __b58base = len(__b58chars)

    long_value = 0
    for (i, c) in enumerate(v[::-1]):
        long_value += (256 ** i) * ordsix(c)

    result = ''
    while long_value >= __b58base:
        div, mod = divmod(long_value, __b58base)
        result = __b58chars[mod] + result
        long_value = div
    result = __b58chars[long_value] + result

    # Bitcoin does a little leading-zero-compression:
    # leading 0-bytes in the input become leading-1s
    nPad = 0
    for c in v:
        if chrsix(c) == b'\0':
            nPad += 1
        else:
            break

    return (__b58chars[0] * nPad) + result


def b58decode(v, length, __b58chars=__b58chars):
    """ decode v into a string of len bytes
	"""
    __b58base = len(__b58chars)
    long_value = 0
    for (i, c) in enumerate(v[::-1]):
        long_value += __b58chars.find(c) * (__b58base ** i)

    result = b''
    while long_value >= 256:
        div, mod = divmod(long_value, 256)
        result = chrsix(mod) + result
        long_value = div
    result = chrsix(long_value) + result

    nPad = 0
    for c in v:
        if c == __b58chars[0]:
            nPad += 1
        else:
            break

    result = chrsix(0) * nPad + result
    if not (length is None) and len(result) != length:
        return None

    return result


# end of bitcointools base58 implementation

# address handling code

def Hash(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def EncodeBase58Check(secret, __b58chars=__b58chars):
    hash = Hash(secret)
    return b58encode(secret + hash[0:4], __b58chars)


def DecodeBase58Check(sec, __b58chars=__b58chars):
    vchRet = b58decode(sec, None, __b58chars)
    secret = vchRet[0:-4]
    csum = vchRet[-4:]
    hash = Hash(secret)
    cs32 = hash[0:4]
    if cs32 != csum:
        return None
    else:
        return secret


def str_to_long(b):
    res = 0
    pos = 1
    for a in reversed(b):
        res += ordsix(a) * pos
        pos *= 256
    return res


def PrivKeyToSecret(privkey):
    if len(privkey) == 279:
        return privkey[9:9 + 32]
    else:
        return privkey[8:8 + 32]


def SecretToASecret(secret, compressed=False):
    prefix = chrsix(network.wif_prefix)
    vchIn = prefix + secret
    if compressed: vchIn += b'\01'
    return EncodeBase58Check(vchIn)


def ASecretToSecret(sec):
    vch = DecodeBase58Check(sec)
    if not vch:
        return False
    if ordsix(vch[0]) != network.wif_prefix:
        print('Warning: adress prefix seems bad (%d vs %d)' % (ordsix(vch[0]), network.wif_prefix))
    return vch[1:]


def regenerate_key(sec):
    b = ASecretToSecret(sec)
    if not b:
        return False
    b = b[0:32]
    secret = int(b'0x' + binascii.hexlify(b), 16)
    return EC_KEY(secret)


def GetPubKey(pkey, compressed=False):
    return i2o_ECPublicKey(pkey, compressed)


def GetPrivKey(pkey, compressed=False):
    return i2d_ECPrivateKey(pkey, compressed)


def GetSecret(pkey):
    return binascii.unhexlify('%064x' % pkey.secret)


def is_compressed(sec):
    b = ASecretToSecret(sec)
    return len(b) == 33


# bitcointools wallet.dat handling code

try:
    from bsddb3.db import *
    from bsddb3.db import DBEnv
    from bsddb3.db import DB_CREATE, DB_INIT_LOCK, DB_INIT_LOG, DB_INIT_MPOOL, DB_INIT_TXN, DB_THREAD, DB_RECOVER
except ImportError:
    raise ImportError("bsddb3 module is required. Please install it using: pip install bsddb3")


def create_env(db_dir):
    db_env = DBEnv(0)
    r = db_env.open(db_dir,
                    (DB_CREATE | DB_INIT_LOCK | DB_INIT_LOG | DB_INIT_MPOOL | DB_INIT_TXN | DB_THREAD | DB_RECOVER))
    return db_env


def parse_CAddress(vds):
    d = Bdict({'ip': '0.0.0.0', 'port': 0, 'nTime': 0})
    try:
        d['nVersion'] = vds.read_int32()
        d['nTime'] = vds.read_uint32()
        d['nServices'] = vds.read_uint64()
        d['pchReserved'] = vds.read_bytes(12)
        d['ip'] = socket.inet_ntoa(vds.read_bytes(4))
        d['port'] = vds.read_uint16()
    except:
        pass
    return d


def deserialize_CAddress(d):
    return d['ip'] + ":" + str(d['port'])


def parse_BlockLocator(vds):
    d = Bdict({'hashes': []})
    nHashes = vds.read_compact_size()
    for i in xrange(nHashes):
        d['hashes'].append(vds.read_bytes(32))
        return d


def deserialize_BlockLocator(d):
    result = "Block Locator top: " + binascii.hexlify(d['hashes'][0][::-1])
    return result


def parse_setting(setting, vds):
    if setting[0] == "f":  # flag (boolean) settings
        return str(vds.read_boolean())
    elif setting[0:4] == "addr":  # CAddress
        d = parse_CAddress(vds)
        return deserialize_CAddress(d)
    elif setting == "nTransactionFee":
        return vds.read_int64()
    elif setting == "nLimitProcessors":
        return vds.read_int32()
    return 'unknown setting'


class SerializationError(Exception):
    """ Thrown when there's a problem deserializing or serializing """


def overlapped_read(f, sz, overlap, maxlen=None):
    buffer = b''
    stop = False
    total_read = 0
    while not stop and (not maxlen or maxlen > total_read):
        new_content = os.read(f, sz)
        if not new_content: break
        total_read += len(new_content)
        buffer = buffer[-overlap:] + new_content
        yield buffer


def search_patterns_on_disk(device, size, inc, patternlist):  # inc must be higher than 1k
    try:
        otype = os.O_RDONLY | os.O_BINARY
    except:
        otype = os.O_RDONLY
    try:
        fd = os.open(device, otype)
    except Exception as e:
        print("Can't open %s, check the path or try as root" % device)
        print("  Error: " + str(e.args))
        exit(0)

    i = 0
    data = b''

    tzero = time.time()
    sizetokeep = 0
    BlocksToInspect = dict(map(lambda x: [x, []], patternlist))
    lendataloaded = None
    writeProgressEvery = 100 * Mo
    while i < int(size) and (lendataloaded != 0 or lendataloaded == None):
        if int(i // writeProgressEvery) != int((i + inc) // writeProgressEvery):
            print("%.2f Go read" % (i // 1e9))
        try:
            datakept = data[-sizetokeep:]
            data = datakept + os.read(fd, inc)
            lendataloaded = len(data) - len(datakept)  # should be inc
            for text in patternlist:
                if text in data:
                    BlocksToInspect[text].append([i - len(datakept), data, len(datakept)])
                    pass
            sizetokeep = 20  # 20 because all the patterns have a len<20. Could be higher.
            i += lendataloaded
        except Exception as exc:
            if lendataloaded % 512 > 0:
                raise Exception("SPOD error 1: %d, %d" % (lendataloaded, i - len(datakept)))
            os.lseek(fd, lendataloaded, os.SEEK_CUR)
            print(str(exc))
            i += lendataloaded
            continue
    os.close(fd)

    AllOffsets = dict(map(lambda x: [repr(x), []], patternlist))
    for text, blocks in BlocksToInspect.items():
        for offset, data, ldk in blocks:  # ldk = len(datakept)
            offsetslist = [offset + m.start() for m in re.finditer(text, data)]
            AllOffsets[repr(text)].extend(offsetslist)

    AllOffsets['PRFdevice'] = device
    AllOffsets['PRFdt'] = time.time() - tzero
    AllOffsets['PRFsize'] = i
    return AllOffsets


def multiextract(s, ll):
    r = []
    cursor = 0
    for length in ll:
        r.append(s[cursor:cursor + length])
        cursor += length
    if s[cursor:] != b'':
        r.append(s[cursor:])
    return r


class RecovCkey(object):
    def __init__(self, epk, pk):
        self.encrypted_pk = epk
        self.public_key = pk
        self.mkey = None
        self.privkey = None


class RecovMkey(object):
    def __init__(self, ekey, salt, nditer, ndmethod, nid):
        self.encrypted_key = ekey
        self.salt = salt
        self.iterations = nditer
        self.method = ndmethod
        self.id = nid


# print((ekey, salt, nditer, ndmethod, nid))


def readpartfile(fd, offset, length):  # make everything 512*n because of windows...
    rest = offset % 512
    new_offset = offset - rest
    big_length = 512 * (int((length + rest - 1) // 512) + 1)
    os.lseek(fd, new_offset, os.SEEK_SET)
    d = os.read(fd, big_length)
    return d[rest:rest + length]


def recov_ckey(fd, offset):
    d = readpartfile(fd, offset - 49, 122)
    me = multiextract(d, [1, 48, 4, 4, 1])

    checks = []
    checks.append([0, '30'])
    checks.append([3, '636b6579'])
    if sum(map(lambda x: int(me[x[0]] != binascii.unhexlify(x[1])), checks)):  # number of false statements
        return None

    return me


def recov_mkey(fd, offset):
    d = readpartfile(fd, offset - 72, 84)
    me = multiextract(d, [4, 48, 1, 8, 4, 4, 1, 2, 8, 4])

    checks = []
    checks.append([0, '43000130'])
    checks.append([2, '08'])
    checks.append([6, '00'])
    checks.append([8, '090001046d6b6579'])
    if sum(map(lambda x: int(me[x[0]] != binascii.unhexlify(x[1])), checks)):  # number of false statements
        return None

    return me


def drop_first(e):
    if hasattr(e, 'next'):
        e.next()
    else:
        e = e[1:]
    for i in e: yield i


def recov_uckey(fd, offset):
    dd = readpartfile(fd, offset, 223)
    r = []
    for beg in map(binascii.unhexlify, ['3081d30201010420', '308201130201010420']):
        for chunk in drop_first(dd.split(beg)):
            r.append(chunk[:32])
    return r and (None, None, None, None, r[0])


def recov_uckeyOLD(fd, offset):
    checks = []

    d = readpartfile(fd, offset - 217, 223)
    if d[-7] == '\x26':
        me = multiextract(d, [2, 1, 4, 1, 32, 141, 33, 2, 1, 6])

        checks.append([0, '3081'])
        checks.append([2, '02010104'])
    elif d[-7] == '\x46':
        d = readpartfile(fd, offset - 282, 286)

        me = multiextract(d, [2, 1, 4, 1, 32, 173, 65, 1, 2, 5])

        checks.append([0, '8201'])
        checks.append([2, '02010104'])
        checks.append([-1, '460001036b'])
    else:
        return None

    if sum(map(lambda x: int(me[x[0]] != binascii.unhexlify(x[1])), checks)):  # number of false statements
        return None

    return me


def recov(device, passes, size=102400, inc=10240, outputdir='.'):
    if inc % 512 > 0:
        inc -= inc % 512  # inc must be 512*n on Windows... Don't ask me why...

    nameToDBName = {
        'mkey': b'\x09\x00\x01\x04mkey',
        'ckey': b'\x27\x00\x01\x04ckey',
        'key': b'\x00\x01\x03key'
    }

    # Ensure output directory exists
    import os
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    if not device.startswith('PartialRecoveryFile:'):
        r = search_patterns_on_disk(device, size, inc, nameToDBName.values())
        f = open(outputdir + '/pywallet_partial_recovery_%d.json' % ts(), 'w')
        f.write(json.dumps(r))
        f.close()
        print("\nRead %.1f Go in %.1f minutes\n" % (r['PRFsize'] // 1e9, r['PRFdt'] // 60.0))
    else:
        prf = device[20:]
        f = open(prf, 'r')
        content = f.read()
        f.close()
        r = json.loads(content)
        device = r['PRFdevice']
        print("\nLoaded %.1f Go from %s\n" % (r['PRFsize'] // 1e9, device))

    try:
        otype = os.O_RDONLY | os.O_BINARY
    except:
        otype = os.O_RDONLY
    fd = os.open(device, otype)

    mkeys = []
    crypters = []
    for offset in r[repr(nameToDBName['mkey'])]:
        s = recov_mkey(fd, offset)
        if s == None:
            continue
        if s[-1] == b'': s = s[:-1]
        newmkey = RecovMkey(
            s[1],
            s[3],
            int(binascii.hexlify(s[5][::-1]), 16),
            int(binascii.hexlify(s[4][::-1]), 16),
            int(binascii.hexlify(s[-1][::-1]), 16)
        )
        mkeys.append([offset, newmkey])

    print("Found %d possible wallets" % len(mkeys))

    ckeys = []
    for offset in r[repr(nameToDBName['ckey'])]:
        s = recov_ckey(fd, offset)
        if s == None:
            continue
        newckey = RecovCkey(s[1], s[5][:int(binascii.hexlify(s[4]), 16)])
        ckeys.append([offset, newckey])
    print('Found %d possible encrypted keys' % len(ckeys))

    uckeys = []
    for offset in r[repr(nameToDBName['key'])]:
        s = recov_uckey(fd, offset)
        if s:
            uckeys.append(s[4])
    uckeys = list(set(uckeys))
    print('Found %d possible unencrypted keys' % len(uckeys))

    os.close(fd)

    list_of_possible_keys_per_master_key = dict(map(lambda x: [x[1], []], mkeys))
    for cko, ck in ckeys:
        tl = map(lambda x: [abs(x[0] - cko)] + x, mkeys)
        tl = sorted(tl, key=lambda x: x[0])
        list_of_possible_keys_per_master_key[tl[0][2]].append(ck)

    cpt = 0
    mki = 1
    tzero = time.time()
    if len(passes) == 0:
        if len(ckeys) > 0:
            print("Can't decrypt them as you didn't provide any passphrase.")
    else:
        for mko, mk in mkeys:
            list_of_possible_keys = list_of_possible_keys_per_master_key[mk]
            sys.stdout.write("\nPossible wallet #" + str(mki))
            sys.stdout.flush()
            for ppi, pp in enumerate(passes):
                sys.stdout.write("\n    with passphrase #" + str(ppi + 1) + "  ")
                sys.stdout.flush()
                failures_in_a_row = 0
                #				print("SKFP params:", pp, mk.salt, mk.iterations, mk.method)
                try:
                    # Ensure passphrase is properly converted
                    passphrase = str(pp) if not isinstance(pp, (str, bytes)) else pp
                    res = crypter.SetKeyFromPassphrase(passphrase, mk.salt, mk.iterations, mk.method)
                    if res == 0:
                        print("Unsupported derivation method")
                        continue  # Try next passphrase instead of exiting
                    masterkey = crypter.Decrypt(mk.encrypted_key)
                    crypter.SetKey(masterkey)
                except Exception as e:
                    print(f"\nError processing passphrase: {str(e)}")
                    print(f"Passphrase type: {type(pp)}, value: {pp}")
                    print(f"Salt type: {type(mk.salt)}, iterations: {mk.iterations}, method: {mk.method}")
                    continue  # Try next passphrase
                for ck in list_of_possible_keys:
                    if cpt % 10 == 9 and failures_in_a_row == 0:
                        sys.stdout.write('.')
                        sys.stdout.flush()
                    if failures_in_a_row > 5:
                        break
                    crypter.SetIV(Hash(ck.public_key))
                    secret = crypter.Decrypt(ck.encrypted_pk)
                    compressed = ck.public_key[0] != '\04'

                    pkey = EC_KEY(int(b'0x' + binascii.hexlify(secret), 16))
                    if ck.public_key != GetPubKey(pkey, compressed):
                        failures_in_a_row += 1
                    else:
                        failures_in_a_row = 0
                        ck.mkey = mk
                        ck.privkey = secret
                    cpt += 1
            mki += 1
        print("\n")
        tone = time.time()
        try:
            calcspeed = 1.0 * cpt // (tone - tzero) * 60  # calc/min
        except:
            calcspeed = 1.0
        if calcspeed == 0:
            calcspeed = 1.0

        ckeys_not_decrypted = list(filter(lambda x: x[1].privkey == None, ckeys))
        refused_to_test_all_pps = True
        if len(ckeys_not_decrypted) == 0:
            print("All the found encrypted private keys have been decrypted.")
            return map(lambda x: x[1].privkey, ckeys)
        else:
            print("Private keys not decrypted: %d" % len(ckeys_not_decrypted))
            print("Trying all the remaining possibilities (%d) might take up to %d minutes." % (
                len(ckeys_not_decrypted) * len(passes) * len(mkeys),
                int(len(ckeys_not_decrypted) * len(passes) * len(mkeys) // calcspeed)))
            cont = raw_input("Do you want to test them? (y/n): ")
            while len(cont) == 0:
                cont = raw_input("Do you want to test them? (y/n): ")
                if cont[0] == 'y':
                    refused_to_test_all_pps = False
                    cpt = 0
                    for dist, mko, mk in tl:
                        for ppi, pp in enumerate(passes):
                            res = crypter.SetKeyFromPassphrase(pp, mk.salt, mk.iterations, mk.method)
                            if res == 0:
                                logging.error("Unsupported derivation method")
                                sys.exit(1)
                            masterkey = crypter.Decrypt(mk.encrypted_key)
                            crypter.SetKey(masterkey)
                            for cko, ck in ckeys_not_decrypted:
                                tl = map(lambda x: [abs(x[0] - cko)] + x, mkeys)
                                tl = sorted(tl, key=lambda x: x[0])
                                if mk == tl[0][2]:
                                    continue  # because already tested
                                crypter.SetIV(Hash(ck.public_key))
                                secret = crypter.Decrypt(ck.encrypted_pk)
                                compressed = ck.public_key[0] != '\04'

                                pkey = EC_KEY(int(b'0x' + binascii.hexlify(secret), 16))
                                if ck.public_key == GetPubKey(pkey, compressed):
                                    ck.mkey = mk
                                    ck.privkey = secret
                                cpt += 1

        print("")
        ckeys_not_decrypted = filter(lambda x: x[1].privkey == None, ckeys)
        if len(ckeys_not_decrypted) == 0:
            print("All the found encrypted private keys have been finally decrypted.")
        elif not refused_to_test_all_pps:
            print("Private keys not decrypted: %d" % len(ckeys_not_decrypted))
            print("Try another password, check the size of your partition or seek help")

    uncrypted_ckeys = filter(lambda x: x != None, map(lambda x: x[1].privkey, ckeys))
    uckeys.extend(uncrypted_ckeys)

    return uckeys


def ts():
    return int(time.mktime(datetime.now().timetuple()))


def check_postkeys(key, postkeys):
    for i in postkeys:
        if key[:len(i)] == i:
            return True
    return False


def one_element_in(a, string):
    for i in a:
        if i in string:
            return True
    return False


def first_read(device, size, prekeys, inc=10000):
    t0 = ts() - 1
    try:
        fd = os.open(device, os.O_RDONLY)
    except:
        print("Can't open %s, check the path or try as root" % device)
        exit(0)
    prekey = prekeys[0]
    data = b""
    i = 0
    data = os.read(fd, i)
    before_contained_key = False
    contains_key = False
    ranges = []

    while i < int(size):
        if i % (10 * Mio) > 0 and i % (10 * Mio) <= inc:
            print("\n%.2f/%.2f Go" % (i // 1e9, size // 1e9))
            t = ts()
            speed = i // (t - t0)
            ETAts = size // speed + t0
            d = datetime.fromtimestamp(ETAts)
            print(d.strftime("   ETA: %H:%M:%S"))

        try:
            data = os.read(fd, inc)
        except Exception as exc:
            os.lseek(fd, inc, os.SEEK_CUR)
            print(str(exc))
            i += inc
            continue

        contains_key = one_element_in(prekeys, data)

        if not before_contained_key and contains_key:
            ranges.append(i)

        if before_contained_key and not contains_key:
            ranges.append(i)

        before_contained_key = contains_key

        i += inc

    os.close(fd)
    return ranges


def shrink_intervals(device, ranges, prekeys, inc=1000):
    prekey = prekeys[0]
    nranges = []
    fd = os.open(device, os.O_RDONLY)
    for j in range(len(ranges) // 2):
        before_contained_key = False
        contains_key = False
        bi = ranges[2 * j]
        bf = ranges[2 * j + 1]

        mini_blocks = []
        k = bi
        while k <= bf + len(prekey) + 1:
            mini_blocks.append(k)
            k += inc
            mini_blocks.append(k)

        for k in range(len(mini_blocks) // 2):
            mini_blocks[2 * k] -= len(prekey) + 1
            mini_blocks[2 * k + 1] += len(prekey) + 1

            bi = mini_blocks[2 * k]
            bf = mini_blocks[2 * k + 1]

            os.lseek(fd, bi, 0)

            data = os.read(fd, bf - bi + 1)
            contains_key = one_element_in(prekeys, data)

            if not before_contained_key and contains_key:
                nranges.append(bi)

            if before_contained_key and not contains_key:
                nranges.append(bi + len(prekey) + 1 + len(prekey) + 1)

            before_contained_key = contains_key

    os.close(fd)

    return nranges


def find_offsets(device, ranges, prekeys):
    prekey = prekeys[0]
    list_offsets = []
    to_read = 0
    fd = os.open(device, os.O_RDONLY)
    for i in range(len(ranges) // 2):
        bi = ranges[2 * i] - len(prekey) - 1
        os.lseek(fd, bi, 0)
        bf = ranges[2 * i + 1] + len(prekey) + 1
        to_read += bf - bi + 1
        buf = b""
        for j in range(len(prekey)):
            buf += b"\x00"
        curs = bi

        while curs <= bf:
            data = os.read(fd, 1)
            buf = buf[1:] + data
            if buf in prekeys:
                list_offsets.append(curs)
            curs += 1

    os.close(fd)

    return [to_read, list_offsets]


def read_keys(device, list_offsets):
    found_hexkeys = []
    fd = os.open(device, os.O_RDONLY)
    for offset in list_offsets:
        os.lseek(fd, offset + 1, 0)
        data = os.read(fd, 40)
        hexkey = binascii.hexlify(data[1:33])
        after_key = binascii.hexlify(data[33:39])
        if hexkey not in found_hexkeys and check_postkeys(binascii.unhexlify(after_key), postkeys):
            found_hexkeys.append(hexkey)

    os.close(fd)

    return found_hexkeys


def is_sqlite_wallet(wallet_file):
    """
    Check if the wallet file is a SQLite database
    """
    try:
        with open(wallet_file, 'rb') as f:
            header = f.read(16)
            return header.startswith(b'SQLite format 3\x00')
    except:
        return False


def extract_keys_from_sqlite_wallet(wallet_file, passphrases):
    """
    Extract keys from SQLite wallet format (newer Bitcoin Core)
    """
    try:
        import sqlite3

        print("Opening SQLite wallet...")
        conn = sqlite3.connect(wallet_file)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Found tables: %s" % [table[0] for table in tables])

        private_keys = []

        # Look for keys in the main table
        try:
            # First, check the table structure
            cursor.execute("PRAGMA table_info(main);")
            columns = cursor.fetchall()
            print("Table structure: %s" % [col[1] for col in columns])

            # Get all rows to analyze
            cursor.execute("SELECT key, value FROM main;")
            all_rows = cursor.fetchall()
            print("Found %d entries in main table" % len(all_rows))

            # Look for specific key patterns that contain private keys
            key_patterns = [
                b'walletdescriptorkey',  # Contains private keys in DER format
                b'key',  # Traditional key entries
                b'ckey',  # Encrypted key entries
                b'mkey'  # Master key entries
            ]

            for key_data, value_data in all_rows:
                try:
                    if not value_data or not isinstance(value_data, (bytes, bytearray)):
                        continue

                    # Check if this row contains key data
                    is_key_row = False
                    if isinstance(key_data, (bytes, bytearray)):
                        for pattern in key_patterns:
                            if pattern in key_data:
                                is_key_row = True
                                print("Found key pattern '%s' in row" % pattern.decode('ascii', errors='ignore'))
                                break

                    if is_key_row and len(value_data) >= 32:
                        # Look for DER-encoded private keys (ASN.1 format)
                        # Pattern: 30 81 D3 02 01 01 04 20 [32-byte private key]
                        value_hex = binascii.hexlify(value_data).decode('ascii')

                        # Look for DER private key pattern
                        der_pattern = '3081d3020101042'
                        if der_pattern in value_hex:
                            pattern_pos = value_hex.find(der_pattern)
                            key_start = pattern_pos + len(der_pattern) + 1  # +1 for the length byte
                            if key_start + 64 <= len(value_hex):
                                private_key_hex = value_hex[key_start:key_start + 64]
                                try:
                                    private_key_bytes = binascii.unhexlify(private_key_hex)
                                    # Validate it's a valid secp256k1 private key
                                    key_int = int(private_key_hex, 16)
                                    secp256k1_order = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
                                    if 1 <= key_int < secp256k1_order:
                                        print("Found valid private key in DER format")
                                        private_keys.append(private_key_bytes)
                                except:
                                    pass

                        # Also look for raw 32-byte sequences that might be keys
                        for i in range(len(value_data) - 31):
                            potential_key = value_data[i:i + 32]
                            if len(potential_key) == 32:
                                try:
                                    # Validate it's a potential private key
                                    key_hex = binascii.hexlify(potential_key).decode('ascii')
                                    key_int = int(key_hex, 16)
                                    secp256k1_order = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

                                    # Check if it's in valid range and not obviously invalid
                                    if (1 <= key_int < secp256k1_order and
                                            key_hex != '00' * 64 and
                                            key_hex != 'ff' * 64 and
                                            not key_hex.startswith('00000000')):
                                        private_keys.append(potential_key)
                                        print("Found potential private key at offset %d" % i)
                                except:
                                    pass

                except Exception as e:
                    print("Error processing SQLite row: %s" % e)
                    continue

        except Exception as e:
            print("Error reading SQLite keys: %s" % e)

        conn.close()

        # Remove duplicates
        private_keys = list(set(private_keys))
        print("Extracted %d potential keys from SQLite wallet" % len(private_keys))

        return private_keys

    except ImportError:
        print("SQLite3 module not available")
        return []
    except Exception as e:
        print("Error reading SQLite wallet: %s" % e)
        return []


def extract_keys_from_wallet(wallet_file, passphrases):
    """
    Extract private keys from a wallet.dat file
    """
    try:
        # Check if this is a SQLite wallet (newer format)
        if is_sqlite_wallet(wallet_file):
            print("Detected SQLite wallet format (newer Bitcoin Core)")
            return extract_keys_from_sqlite_wallet(wallet_file, passphrases)

        # Create a temporary database environment for Berkeley DB
        temp_db_dir = os.path.dirname(wallet_file)
        wallet_name = os.path.basename(wallet_file)

        # Try to open the wallet
        db_env = create_env(temp_db_dir)

        # Read wallet data
        json_db = {}
        try:
            read_wallet(json_db, db_env, wallet_name, True, True, "", False)
        except Exception as e:
            print("Error reading wallet: %s" % e)
            return []

        # Extract private keys
        private_keys = []

        # Get unencrypted keys
        if 'keys' in json_db:
            for key_data in json_db['keys']:
                if 'sec' in key_data and key_data['sec']:
                    # Convert hex string to bytes
                    try:
                        if isinstance(key_data['sec'], str):
                            private_key_bytes = binascii.unhexlify(key_data['sec'])
                        else:
                            private_key_bytes = key_data['sec']
                        private_keys.append(private_key_bytes)
                    except Exception as e:
                        print("Error processing key: %s" % e)
                        continue

        # Try to decrypt encrypted keys if passphrases provided
        if passphrases and 'mkey' in json_db and json_db['mkey']:
            print("Attempting to decrypt encrypted keys...")
            for passphrase in passphrases:
                try:
                    # Try to decrypt with this passphrase
                    decrypted_keys = decrypt_wallet_keys(json_db, passphrase)
                    private_keys.extend(decrypted_keys)
                except Exception as e:
                    print("Failed to decrypt with passphrase: %s" % e)
                    continue

        print("Extracted %d keys from wallet file" % len(private_keys))
        return private_keys

    except Exception as e:
        print("Error extracting keys from wallet: %s" % e)
        return []


def decrypt_wallet_keys(json_db, passphrase):
    """
    Decrypt encrypted keys from wallet data
    """
    decrypted_keys = []

    try:
        if 'mkey' not in json_db or not json_db['mkey']:
            return decrypted_keys

        mkey_data = json_db['mkey']

        # Set up crypter with passphrase
        if isinstance(passphrase, str):
            passphrase = passphrase.encode('utf-8')

        result = crypter.SetKeyFromPassphrase(
            passphrase,
            mkey_data['salt'],
            mkey_data['nDerivationIterations'],
            mkey_data['nDerivationMethod']
        )

        if result == 0:
            print("Unsupported derivation method")
            return decrypted_keys

        # Decrypt master key
        master_key = crypter.Decrypt(mkey_data['encrypted_key'])
        crypter.SetKey(master_key)

        # Decrypt individual keys
        if 'keys' in json_db:
            for key_data in json_db['keys']:
                if 'encrypted' in key_data and key_data['encrypted']:
                    try:
                        # Set IV and decrypt
                        if 'public_key' in key_data:
                            crypter.SetIV(Hash(key_data['public_key']))
                            decrypted_key = crypter.Decrypt(key_data['encrypted'])
                            decrypted_keys.append(decrypted_key)
                    except Exception as e:
                        print("Error decrypting individual key: %s" % e)
                        continue

    except Exception as e:
        print("Error in decrypt_wallet_keys: %s" % e)

    return decrypted_keys


def read_device_size(size):
    # Support both old format (Mo, Gio) and new format (MB, GB)
    # Parse the size string to extract number, prefix, and binary indicator

    # Handle different formats: MB, GB, Mo, Gio, etc.
    match = re.match(r'(\d+)(|k|K|M|G|T|P)(i?)(o|B)?$', size, re.IGNORECASE)
    if not match:
        raise ValueError("Invalid size format: %s. Use formats like: 100MB, 50GB, 20Mo, 10Gio" % size)

    n, prefix, bi, suffix = match.groups()
    n = int(n)

    # Normalize prefix to uppercase
    prefix = prefix.upper() if prefix else ''

    # Determine if binary (1024-based) or decimal (1000-based)
    # 'i' indicates binary (e.g., Gio, MiB), 'o' suffix also indicates binary for compatibility
    is_binary = bool(bi) or (suffix and suffix.lower() == 'o')

    # Calculate multiplier
    base = 1024 if is_binary else 1000
    prefixes = {'': 0, 'K': 1, 'M': 2, 'G': 3, 'T': 4, 'P': 5}

    if prefix not in prefixes:
        raise ValueError("Unknown prefix: %s" % prefix)

    multiplier = base ** prefixes[prefix]
    result = n * multiplier

    return result


def md5_2(a):
    return hashlib.md5(a).digest()


def md5_file(nf):
    try:
        with open(nf, 'r') as f:
            fichier = f.read()
        return md5_2(fichier)
    except:
        return 'zz'


def md5_onlinefile(add):
    page = urllib.urlopen(add).read()
    return md5_2(page)


class KEY:
    def __init__(self):
        self.prikey = None
        self.pubkey = None

    def generate(self, secret=None):
        if secret:
            exp = int(b'0x' + binascii.hexlify(secret), 16)
            self.prikey = ecdsa.SigningKey.from_secret_exponent(exp, curve=secp256k1)
        else:
            self.prikey = ecdsa.SigningKey.generate(curve=secp256k1)
        self.pubkey = self.prikey.get_verifying_key()
        return self.prikey.to_der()

    def set_privkey(self, key):
        if len(key) == 279:
            seq1, rest = der.remove_sequence(key)
            integer, rest = der.remove_integer(seq1)
            octet_str, rest = der.remove_octet_string(rest)
            tag1, cons1, rest, = der.remove_constructed(rest)
            tag2, cons2, rest, = der.remove_constructed(rest)
            point_str, rest = der.remove_bitstring(cons2)
            self.prikey = ecdsa.SigningKey.from_string(octet_str, curve=secp256k1)
        else:
            self.prikey = ecdsa.SigningKey.from_der(key)

    def set_pubkey(self, key):
        key = key[1:]
        self.pubkey = ecdsa.VerifyingKey.from_string(key, curve=secp256k1)

    def get_privkey(self):
        _p = self.prikey.curve.curve.p()
        _r = self.prikey.curve.generator.order()
        _Gx = self.prikey.curve.generator.x()
        _Gy = self.prikey.curve.generator.y()
        encoded_oid2 = der.encode_oid(*(1, 2, 840, 10045, 1, 1))
        encoded_gxgy = binascii.unhexlify("04" + ("%64x" % _Gx) + ("%64x" % _Gy))
        param_sequence = der.encode_sequence(
            ecdsa.der.encode_integer(1),
            der.encode_sequence(
                encoded_oid2,
                der.encode_integer(_p),
            ),
            der.encode_sequence(
                der.encode_octet_string("\x00"),
                der.encode_octet_string("\x07"),
            ),
            der.encode_octet_string(encoded_gxgy),
            der.encode_integer(_r),
            der.encode_integer(1),
        );
        encoded_vk = "\x00\x04" + self.pubkey.to_string()
        return der.encode_sequence(
            der.encode_integer(1),
            der.encode_octet_string(self.prikey.to_string()),
            der.encode_constructed(0, param_sequence),
            der.encode_constructed(1, der.encode_bitstring(encoded_vk)),
        )

    def get_pubkey(self):
        return "\x04" + self.pubkey.to_string()

    def sign(self, hash):
        sig = self.prikey.sign_digest(hash, sigencode=ecdsa.util.sigencode_der)
        return binascii.hexlify(sig)

    def verify(self, hash, sig):
        return self.pubkey.verify_digest(sig, hash, sigdecode=ecdsa.util.sigdecode_der)


import mmap


class BCDataStream(object):
    def __init__(self):
        self.input = None
        self.read_cursor = 0

    def clear(self):
        self.input = None
        self.read_cursor = 0

    def write(self, bytes):  # Initialize with string of bytes
        if self.input is None:
            self.input = bytes
        else:
            self.input += bytes

    def map_file(self, file, start):  # Initialize with bytes from file
        self.input = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
        self.read_cursor = start

    def seek_file(self, position):
        self.read_cursor = position

    def close_file(self):
        self.input.close()

    def read_string(self):
        # Strings are encoded depending on length:
        # 0 to 252 :	1-byte-length followed by bytes (if any)
        # 253 to 65,535 : byte'253' 2-byte-length followed by bytes
        # 65,536 to 4,294,967,295 : byte '254' 4-byte-length followed by bytes
        # ... and the Bitcoin client is coded to understand:
        # greater than 4,294,967,295 : byte '255' 8-byte-length followed by bytes of string
        # ... but I don't think it actually handles any strings that big.
        if self.input is None:
            raise SerializationError("call write(bytes) before trying to deserialize")

        try:
            length = self.read_compact_size()
        except IndexError:
            raise SerializationError("attempt to read past end of buffer")

        return self.read_bytes(length)

    def write_string(self, string):
        # Length-encoded as with read-string
        self.write_compact_size(len(string))
        self.write(string)

    def read_bytes(self, length):
        try:
            result = self.input[self.read_cursor:self.read_cursor + length]
            self.read_cursor += length
            return result
        except IndexError:
            raise SerializationError("attempt to read past end of buffer")

        return b''

    def read_boolean(self):
        return self.read_bytes(1)[0] != chrsix(0)

    def read_int16(self):
        return self._read_num('<h')

    def read_uint16(self):
        return self._read_num('<H')

    def read_int32(self):
        return self._read_num('<i')

    def read_uint32(self):
        return self._read_num('<I')

    def read_int64(self):
        return self._read_num('<q')

    def read_uint64(self):
        return self._read_num('<Q')

    def write_boolean(self, val):
        return self.write(chrsix(int(val)))

    def write_int16(self, val):
        return self._write_num('<h', val)

    def write_uint16(self, val):
        return self._write_num('<H', val)

    def write_int32(self, val):
        return self._write_num('<i', val)

    def write_uint32(self, val):
        return self._write_num('<I', val)

    def write_int64(self, val):
        return self._write_num('<q', val)

    def write_uint64(self, val):
        return self._write_num('<Q', val)

    def read_compact_size(self):
        size = ordsix(self.input[self.read_cursor])
        self.read_cursor += 1
        if size == 253:
            size = self._read_num('<H')
        elif size == 254:
            size = self._read_num('<I')
        elif size == 255:
            size = self._read_num('<Q')
        return size

    def write_compact_size(self, size):
        if size < 0:
            raise SerializationError("attempt to write size < 0")
        elif size < 253:
            self.write(chrsix(size))
        elif size < 2 ** 16:
            self.write('\xfd')
            self._write_num('<H', size)
        elif size < 2 ** 32:
            self.write('\xfe')
            self._write_num('<I', size)
        elif size < 2 ** 64:
            self.write('\xff')
            self._write_num('<Q', size)

    def _read_num(self, format):
        (i,) = struct.unpack_from(format, self.input, self.read_cursor)
        self.read_cursor += struct.calcsize(format)
        return i

    def _write_num(self, format, num):
        s = struct.pack(format, num)
        self.write(s)


class DBError:
    pass


def open_wallet(db_env, walletfile, writable=False, DB_RDONLY_param=None, DB_BTREE_param=None):
    db = bdb.DB(db_env)
    if writable:
        DB_TYPEOPEN = DB_CREATE
    else:
        DB_TYPEOPEN = DB_RDONLY
    flags = DB_THREAD | DB_TYPEOPEN
    try:
        r = db.open(walletfile, "main", DB_BTREE, flags)
    except Exception as e:
        print(f"DB open error: {e}")
        r = True

    if not (r is None):
        logging.error("Couldn't open wallet.dat/main. Try quitting Bitcoin and running this again.")
        sys.exit(1)

    return db


def parse_wallet(db, item_callback):
    kds = BCDataStream()
    vds = BCDataStream()

    def parse_TxIn(vds):
        d = Bdict({})
        d['prevout_hash'] = binascii.hexlify(vds.read_bytes(32))
        d['prevout_n'] = vds.read_uint32()
        d['scriptSig'] = binascii.hexlify(vds.read_bytes(vds.read_compact_size()))
        d['sequence'] = vds.read_uint32()
        return d

    def parse_TxOut(vds):
        d = Bdict({})
        d['value'] = vds.read_int64() // 1e8
        d['scriptPubKey'] = binascii.hexlify(vds.read_bytes(vds.read_compact_size()))
        return d

    for (key, value) in db.items():
        d = Bdict({})

        kds.clear();
        kds.write(key)
        vds.clear();
        vds.write(value)

        type = kds.read_string()

        d["__key__"] = key
        d["__value__"] = value
        d["__type__"] = type

        try:
            if type == b"tx":
                d["tx_id"] = binascii.hexlify(kds.read_bytes(32)[::-1])
                start = vds.read_cursor
                d['version'] = vds.read_int32()
                n_vin = vds.read_compact_size()
                d['txIn'] = []
                for i in xrange(n_vin):
                    d['txIn'].append(parse_TxIn(vds))
                n_vout = vds.read_compact_size()
                d['txOut'] = []
                for i in xrange(n_vout):
                    d['txOut'].append(parse_TxOut(vds))
                d['lockTime'] = vds.read_uint32()
                d['tx'] = binascii.hexlify(vds.input[start:vds.read_cursor])
                d['txv'] = binascii.hexlify(value)
                d['txk'] = binascii.hexlify(key)
            elif type == b"name":
                d['hash'] = kds.read_string()
                d['name'] = vds.read_string()
            elif type == b"version":
                d['version'] = vds.read_uint32()
            elif type == b"minversion":
                d['minversion'] = vds.read_uint32()
            elif type == b"setting":
                d['setting'] = kds.read_string()
                d['value'] = parse_setting(d['setting'], vds)
            elif type == b"key":
                d['public_key'] = kds.read_bytes(kds.read_compact_size())
                d['private_key'] = vds.read_bytes(vds.read_compact_size())
            elif type == b"wkey":
                d['public_key'] = kds.read_bytes(kds.read_compact_size())
                d['private_key'] = vds.read_bytes(vds.read_compact_size())
                d['created'] = vds.read_int64()
                d['expires'] = vds.read_int64()
                d['comment'] = vds.read_string()
            elif type == b"defaultkey":
                d['key'] = vds.read_bytes(vds.read_compact_size())
            elif type == b"pool":
                d['n'] = kds.read_int64()
                d['nVersion'] = vds.read_int32()
                d['nTime'] = vds.read_int64()
                d['public_key'] = vds.read_bytes(vds.read_compact_size())
            elif type == b"acc":
                d['account'] = kds.read_string()
                d['nVersion'] = vds.read_int32()
                d['public_key'] = vds.read_bytes(vds.read_compact_size())
            elif type == b"acentry":
                d['account'] = kds.read_string()
                d['n'] = kds.read_uint64()
                d['nVersion'] = vds.read_int32()
                d['nCreditDebit'] = vds.read_int64()
                d['nTime'] = vds.read_int64()
                d['otherAccount'] = vds.read_string()
                d['comment'] = vds.read_string()
            # elif type == b"bestblock":
            # 	d['nVersion'] = vds.read_int32()
            # 	d.update(parse_BlockLocator(vds))
            elif type == b"ckey":
                d['public_key'] = kds.read_bytes(kds.read_compact_size())
                d['encrypted_private_key'] = vds.read_bytes(vds.read_compact_size())
            elif type == b"mkey":
                d['nID'] = kds.read_uint32()
                d['encrypted_key'] = vds.read_string()
                d['salt'] = vds.read_string()
                d['nDerivationMethod'] = vds.read_uint32()
                d['nDerivationIterations'] = vds.read_uint32()
                d['otherParams'] = vds.read_string()

            item_callback(type, d)

        except Exception as e:
            traceback.print_exc()
            print("ERROR parsing wallet.dat, type %s" % type)
            print("key data: %s" % key)
            print("key data in hex: %s" % binascii.hexlify(key))
            print("value data in hex: %s" % binascii.hexlify(value))
            sys.exit(1)


def delete_from_wallet(db_env, walletfile, typedel, kd):
    db = open_wallet(db_env, walletfile, True)
    kds = BCDataStream()
    vds = BCDataStream()

    deleted_items = 0

    if not isinstance(kd, list):
        kd = [kd]

    if typedel == 'tx' and kd != ['all']:
        for keydel in kd:
            db.delete('\x02\x74\x78' + binascii.unhexlify(keydel)[::-1])
            deleted_items += 1

    else:
        for i, keydel in enumerate(kd):
            for (key, value) in db.items():
                kds.clear();
                kds.write(key)
                vds.clear();
                vds.write(value)
                type = kds.read_string()

                if typedel == "tx" and type == b"tx":
                    db.delete(key)
                    deleted_items += 1
                elif typedel == "key":
                    if type == b"key" or type == b"ckey":
                        if keydel == public_key_to_bc_address(kds.read_bytes(kds.read_compact_size())):
                            db.delete(key)
                            deleted_items += 1
                    elif type == b"pool":
                        vds.read_int32()
                        vds.read_int64()
                        if keydel == public_key_to_bc_address(vds.read_bytes(vds.read_compact_size())):
                            db.delete(key)
                            deleted_items += 1
                    elif type == b"name":
                        if keydel == kds.read_string():
                            db.delete(key)
                            deleted_items += 1

    db.close()
    return deleted_items


def merge_keys_lists(la, lb):
    lr = Bdict({})
    llr = []
    for k in la:
        lr[k[0]] = k[1]

    for k in lb:
        if k[0] in lr.keys():
            lr[k[0]] = lr[k[0]] + " / " + k[1]
        else:
            lr[k[0]] = k[1]

    for k, j in lr.items():
        llr.append([k, j])

    return llr


def merge_wallets(wadir, wa, wbdir, wb, wrdir, wr, passphrase_a, passphrase_b, passphrase_r):
    global passphrase
    passphrase_LAST = passphrase

    # Read Wallet 1
    passphrase = passphrase_a
    dba_env = create_env(wadir)
    crypted_a = read_wallet(json_db, dba_env, wa, True, True, "", None)['crypted']

    list_keys_a = []
    for i in json_db['keys']:
        try:
            label = i['label']
        except:
            label = "#Reserve"
        try:
            list_keys_a.append([i['secret'], label])
        except:
            pass

    if len(list_keys_a) == 0:
        return [False, "Something went wrong with the first wallet."]

    # Read Wallet 2
    passphrase = passphrase_b
    dbb_env = create_env(wbdir)
    crypted_b = read_wallet(json_db, dbb_env, wb, True, True, "", None)['crypted']

    list_keys_b = []
    for i in json_db['keys']:
        try:
            label = i['label']
        except:
            label = "#Reserve"
        try:
            list_keys_b.append([i['secret'], label])
        except:
            pass
    if len(list_keys_b) == 0:
        return [False, "Something went wrong with the second wallet."]

    m = merge_keys_lists(list_keys_a, list_keys_b)

    # Create new wallet
    dbr_env = create_env(wrdir)
    create_new_wallet(dbr_env, wr, 80100)

    dbr = open_wallet(dbr_env, wr, True)
    update_wallet(dbr, 'minversion', {'minversion': 60000})

    if len(passphrase_r) > 0:
        NPP_salt = os.urandom(8)
        NPP_rounds = int(50000 + random.random() * 20000)
        NPP_method = 0
        NPP_MK = os.urandom(32)

        crypter.SetKeyFromPassphrase(passphrase_r, NPP_salt, NPP_rounds, NPP_method)
        NPP_EMK = crypter.Encrypt(NPP_MK)

        update_wallet(dbr, 'mkey', {
            'encrypted_key': NPP_EMK,
            'nDerivationIterations': NPP_rounds,
            'nDerivationMethod': NPP_method,
            'nID': 1,
            'otherParams': b'',
            'salt': NPP_salt
        })

    dbr.close()

    t = '\n'.join(map(lambda x: ';'.join(x), m))
    passphrase = passphrase_r

    global global_merging_message

    global_merging_message = ["Merging...", "Merging..."]
    thread.start_new_thread(import_csv_keys, ("\x00" + t, wrdir, wr,))
    t = ""

    passphrase = passphrase_LAST

    return [True]


def random_string(l, alph="0123456789abcdef"):
    r = ""
    la = len(alph)
    for i in range(l):
        r += alph[int(la * (random.random()))]
    return r


def update_wallet(db, types, datas, paramsAreLists=False):
    """Write a single item to the wallet.
	db must be open with writable=True.
	type and data are the type code and data dictionary as parse_wallet would
	give to item_callback.
	data's __key__, __value__ and __type__ are ignored; only the primary data
	fields are used.
	"""

    if not paramsAreLists:
        types = [types]
        datas = [datas]

    if len(types) != len(datas):
        raise Exception("UpdateWallet: sizes are different")

    for it, type in enumerate(types):
        type = str_to_bytes(type)
        data = datas[it]

        d = data
        kds = BCDataStream()
        vds = BCDataStream()

        # Write the type code to the key
        kds.write_string(type)
        vds.write(b"")  # Ensure there is something

        try:
            if type == b"tx":
                #			raise NotImplementedError("Writing items of type 'tx'")
                kds.write(binascii.unhexlify(d['txi'][6:]))
                vds.write(binascii.unhexlify(d['txv']))
            elif type == b"name":
                kds.write_string(d['hash'])
                vds.write_string(d['name'])
            elif type == b"version":
                vds.write_uint32(d['version'])
            elif type == b"minversion":
                vds.write_uint32(d['minversion'])
            elif type == b"setting":
                raise NotImplementedError("Writing items of type 'setting'")
                kds.write_string(d['setting'])
            # d['value'] = parse_setting(d['setting'], vds)
            elif type == b"key":
                kds.write_string(d['public_key'])
                vds.write_string(d['private_key'])
            elif type == b"wkey":
                kds.write_string(d['public_key'])
                vds.write_string(d['private_key'])
                vds.write_int64(d['created'])
                vds.write_int64(d['expires'])
                vds.write_string(d['comment'])
            elif type == b"defaultkey":
                vds.write_string(d['key'])
            elif type == b"pool":
                kds.write_int64(d['n'])
                vds.write_int32(d['nVersion'])
                vds.write_int64(d['nTime'])
                vds.write_string(d['public_key'])
            elif type == b"acc":
                kds.write_string(d['account'])
                vds.write_int32(d['nVersion'])
                vds.write_string(d['public_key'])
            elif type == b"acentry":
                kds.write_string(d['account'])
                kds.write_uint64(d['n'])
                vds.write_int32(d['nVersion'])
                vds.write_int64(d['nCreditDebit'])
                vds.write_int64(d['nTime'])
                vds.write_string(d['otherAccount'])
                vds.write_string(d['comment'])
            # elif type == b"bestblock":
            # 	vds.write_int32(d['nVersion'])
            # 	vds.write_compact_size(len(d['hashes']))
            # 	for h in d['hashes']:
            # 		vds.write(h)
            elif type == b"ckey":
                kds.write_string(d['public_key'])
                vds.write_string(d['encrypted_private_key'])
            elif type == b"mkey":
                kds.write_uint32(d['nID'])
                vds.write_string(d['encrypted_key'])
                vds.write_string(d['salt'])
                vds.write_uint32(d['nDerivationMethod'])
                vds.write_uint32(d['nDerivationIterations'])
                vds.write_string(d['otherParams'])

            else:
                print("Unknown key type: %s" % type)

            # Write the key/value pair to the database
            db.put(kds.input, vds.input)

        except Exception as e:
            print("ERROR writing to wallet.dat, type %s" % type)
            print("data dictionary: %r" % data)
            traceback.print_exc()


try:
    from bsddb3.db import DB, DBError, DB_BTREE, DB_CREATE
except ImportError:
    print("bsddb3 module not found. Please install it using: pip install bsddb3")
    sys.exit(1)

if 'sys' not in globals():
    import sys


def create_new_wallet(db_env, walletfile, version):
    db_out = DB(db_env)

    try:
        r = db_out.open(walletfile, "main", DB_BTREE, DB_CREATE)
    except DBError:
        r = True

    if not (r is None):
        logging.error("Couldn't open %s." % walletfile)
        sys.exit(1)

    db_out.put(binascii.unhexlify("0776657273696f6e"), binascii.unhexlify("%08x" % version)[::-1])

    db_out.close()


def rewrite_wallet(db_env, walletfile, destFileName, pre_put_callback=None):
    db = open_wallet(db_env, walletfile)

    db_out = DB(db_env)
    try:
        r = db_out.open(destFileName, "main", DB_BTREE, DB_CREATE)
    except DBError:
        r = True

    if not (r is None):
        logging.error("Couldn't open %s." % destFileName)
        sys.exit(1)

    def item_callback(type, d):
        if (pre_put_callback is None or pre_put_callback(type, d)):
            db_out.put(d["__key__"], d["__value__"])

    parse_wallet(db, item_callback)
    db_out.close()
    db.close()


# end of bitcointools wallet.dat handling code

# wallet.dat reader / writer

addr_to_keys = {}


def read_wallet(json_db, db_env, walletfile, print_wallet, print_wallet_transactions, transaction_filter,
                include_balance, FillPool=False):
    global passphrase, addr_to_keys
    crypted = False

    private_keys = []
    private_hex_keys = []

    db = open_wallet(db_env, walletfile, writable=FillPool)

    json_db['keys'] = []
    json_db['pool'] = []
    json_db['tx'] = []
    json_db['names'] = Bdict({})
    json_db['ckey'] = []
    json_db['mkey'] = Bdict({})

    def item_callback(type, d):
        if type == b"tx":
            json_db['tx'].append(
                {"tx_id": d['tx_id'], "txin": d['txIn'], "txout": d['txOut'], "tx_v": d['txv'], "tx_k": d['txk']})

        elif type == b"name":
            json_db['names'][d['hash']] = d['name']

        elif type == b"version":
            json_db['version'] = d['version']

        elif type == b"minversion":
            json_db['minversion'] = d['minversion']

        elif type == b"setting":
            if not json_db.has_key('settings'):
                json_db['settings'] = Bdict({})
            json_db["settings"][d['setting']] = d['value']

        elif type == b"defaultkey":
            json_db['defaultkey'] = public_key_to_bc_address(d['key'])

        elif type == b"key":
            addr = public_key_to_bc_address(d['public_key'])
            compressed = d['public_key'][0] != '\04'
            sec = SecretToASecret(PrivKeyToSecret(d['private_key']), compressed)
            hexsec = binascii.hexlify(ASecretToSecret(sec)[:32])
            private_keys.append(sec)
            addr_to_keys[addr] = [hexsec, binascii.hexlify(d['public_key'])]
            json_db['keys'].append({'addr': addr, 'sec': sec, 'hexsec': hexsec, 'secret': hexsec,
                                    'pubkey': binascii.hexlify(d['public_key']), 'compressed': compressed,
                                    'private': binascii.hexlify(d['private_key'])})

        elif type == b"wkey":
            if not json_db.has_key('wkey'): json_db['wkey'] = []
            json_db['wkey']['created'] = d['created']

        elif type == b"pool":
            """	d['n'] = kds.read_int64()
				d['nVersion'] = vds.read_int32()
				d['nTime'] = vds.read_int64()
				d['public_key'] = vds.read_bytes(vds.read_compact_size())"""
            try:
                json_db['pool'].append({'n': d['n'], 'addr': public_key_to_bc_address(d['public_key']),
                                        'addr2': public_key_to_bc_address(binascii.unhexlify(d['public_key'])),
                                        'addr3': public_key_to_bc_address(binascii.hexlify(d['public_key'])),
                                        'nTime': d['nTime'], 'nVersion': d['nVersion'],
                                        'public_key_hex': d['public_key']})
            except:
                json_db['pool'].append(
                    {'n': d['n'], 'addr': public_key_to_bc_address(d['public_key']), 'nTime': d['nTime'],
                     'nVersion': d['nVersion'], 'public_key_hex': binascii.hexlify(d['public_key'])})

        elif type == b"acc":
            json_db['acc'] = d['account']
        # print("Account %s (current key: %s)"%(d['account'], public_key_to_bc_address(d['public_key'])))

        elif type == b"acentry":
            json_db['acentry'] = (d['account'], d['nCreditDebit'], d['otherAccount'], time.ctime(d['nTime']), d['n'],
                                  d['comment'])

        # elif type == b"bestblock":
        # 	json_db['bestblock'] = binascii.hexlify(d['hashes'][0][::-1])

        elif type == b"ckey":
            crypted = True
            compressed = d['public_key'][0] != '\04'
            json_db['keys'].append(
                {'pubkey': binascii.hexlify(d['public_key']), 'addr': public_key_to_bc_address(d['public_key']),
                 'encrypted_privkey': binascii.hexlify(d['encrypted_private_key']), 'compressed': compressed})

        elif type == b"mkey":
            json_db['mkey']['nID'] = d['nID']
            json_db['mkey']['encrypted_key'] = binascii.hexlify(d['encrypted_key'])
            json_db['mkey']['salt'] = binascii.hexlify(d['salt'])
            json_db['mkey']['nDerivationMethod'] = d['nDerivationMethod']
            json_db['mkey']['nDerivationIterations'] = d['nDerivationIterations']
            json_db['mkey']['otherParams'] = d['otherParams']

            if passphrase:
                res = crypter.SetKeyFromPassphrase(passphrase, d['salt'], d['nDerivationIterations'],
                                                   d['nDerivationMethod'])
                if res == 0:
                    logging.error("Unsupported derivation method")
                    sys.exit(1)
                masterkey = crypter.Decrypt(d['encrypted_key'])
                crypter.SetKey(masterkey)

        else:
            json_db[type] = 'unsupported'
            if type not in b'keymeta'.split():
                print("Wallet data not recognized: %s" % str(d))

    list_of_reserve_not_in_pool = []
    parse_wallet(db, item_callback)

    nkeys = len(json_db['keys'])
    i = 0
    for k in json_db['keys']:
        i += 1
        addr = k['addr']
        if include_balance:
            #			print("%3d/%d  %s  %s" % (i, nkeys, k["addr"], k["balance"]))
            k["balance"] = balance(balance_site, k["addr"])
        #			print("  %s" % (i, nkeys, k["addr"], k["balance"]))

        if addr in json_db['names'].keys():
            k["label"] = json_db['names'][addr]
            k["reserve"] = 0
        else:
            k["reserve"] = 1
            list_of_reserve_not_in_pool.append(k['pubkey'])

    def rnip_callback(a):
        list_of_reserve_not_in_pool.remove(a['public_key_hex'])

    if FillPool:
        map(rnip_callback, json_db['pool'])

        cpt = 1
        for p in list_of_reserve_not_in_pool:
            update_wallet(db, 'pool', {'public_key': binascii.unhexlify(p), 'n': cpt, 'nTime': ts(), 'nVersion': 80100})
            cpt += 1

    db.close()

    crypted = 'salt' in json_db['mkey']

    if not crypted:
        print("The wallet is not encrypted")

    if crypted and not passphrase:
        print("The wallet is encrypted but no passphrase is used")

    if crypted and passphrase:
        check = True
        ppcorrect = True
        for k in json_db['keys']:
            if 'encrypted_privkey' in k:
                ckey = binascii.unhexlify(k['encrypted_privkey'])
                public_key = binascii.unhexlify(k['pubkey'])
                crypter.SetIV(Hash(public_key))
                secret = crypter.Decrypt(ckey)
                compressed = public_key[0] != '\04'

                if check:
                    check = False
                    pkey = EC_KEY(int(b'0x' + binascii.hexlify(secret), 16))
                    if public_key != GetPubKey(pkey, compressed):
                        print("The wallet is encrypted and the passphrase is incorrect")
                        ppcorrect = False
                        break

                sec = SecretToASecret(secret, compressed)
                k['sec'] = sec
                k['hexsec'] = binascii.hexlify(secret[:32])
                k['secret'] = binascii.hexlify(secret)
                k['compressed'] = compressed
                addr_to_keys[k['addr']] = [sec, k['pubkey']]
                #			del(k['ckey'])
                #			del(k['secret'])
                #			del(k['pubkey'])
                private_keys.append(sec)
        if ppcorrect:
            print("The wallet is encrypted and the passphrase is correct")

    for k in json_db['keys']:
        if k['compressed'] and 'secret' in k:
            k['secret'] += b"01"

    #	del(json_db['pool'])
    #	del(json_db['names'])

    return {'crypted': crypted}


def parse_private_key(sec, force_compressed=None):
    as_compressed = lambda x: x if force_compressed is None else force_compressed
    try:
        pkey = regenerate_key(sec)
        compressed = as_compressed(is_compressed(sec))
    except:
        pkey = None
        try:
            binascii.unhexlify(sec)
        except:
            pass
    if not pkey:
        if len(sec) == 64:
            pkey = EC_KEY(str_to_long(binascii.unhexlify(sec)))
            compressed = as_compressed(False)
        elif len(sec) == 66:
            pkey = EC_KEY(str_to_long(binascii.unhexlify(sec[:-2])))
            compressed = as_compressed(True)
        else:
            warnings.warn("Hexadecimal private keys must be 64 or 66 characters long (specified one is " + str(
                len(sec)) + " characters long)")
            if len(sec) < 64:
                compressed = as_compressed(False)
                warnings.warn("Padding with zeroes, %scompressed" % ('un' if not compressed else ''))
                try:
                    pkey = EC_KEY(str_to_long(binascii.unhexlify('0' * (64 - len(sec)) + sec)))
                except Exception as e:
                    warnings.warn(e)
                    raise Exception("Failed padding with zeroes")
            elif len(sec) > 66:
                compressed = as_compressed(False)
                warnings.warn("Keeping first 64 characters, %scompressed" % ('un' if not compressed else ''))
                pkey = EC_KEY(str_to_long(binascii.unhexlify(sec[:64])))
            else:
                raise Exception("Error")
    return (pkey, compressed)


def pubkey_info(pubkey, network):
    addr = public_key_to_bc_address(pubkey, network.p2pkh_prefix)
    p2wpkh = p2sh_script_to_addr(b'\x00\x14' + hash_160(pubkey))
    witaddr = witprog_to_bech32_addr(hash_160(pubkey), network)
    h160 = bc_address_to_hash_160(addr)
    return addr, p2wpkh, witaddr, h160


def keyinfo(sec, network=None, print_info=False, force_compressed=None):
    if not (network is None) and network.__class__ != Network:
        network = find_network(network) or network
    if sec.__class__ == Xpriv:
        assert sec.ktype == 0
        return keyinfo(binascii.hexlify(sec.key), network, print_info, force_compressed)
    network = network or network_bitcoin
    (pkey, compressed) = parse_private_key(sec, force_compressed)
    if not pkey:
        return False

    secret = GetSecret(pkey)
    private_key = GetPrivKey(pkey, compressed)
    uncompressed_ser_public_key = GetPubKey(pkey, False)
    ser_public_key = GetPubKey(pkey, compressed)
    addr, p2wpkh, witaddr, h160 = pubkey_info(ser_public_key, network)
    wif = SecretToASecret(secret, compressed) if network.wif_prefix else None

    if print_info:
        print("Network: %s" % network.name)
        print("Compressed: %s" % str(compressed))
        if network.p2pkh_prefix != None:
            print("P2PKH Address:       %s" % (addr))
        if compressed:
            if network.p2sh_prefix != None:
                print("P2SH-P2WPKH Address: %s" % (p2wpkh))
            else:
                print("P2SH unavailable:    unknown network P2SH prefix")
        if compressed:
            if network.segwit_hrp != None:
                print("P2WPKH Address:      %s" % (witaddr))
            else:
                print("P2WPKH unavailable:  unknown network SegWit HRP")
        if network.wif_prefix != None:
            print("Privkey:             %s" % wif)
        else:
            print("Privkey unavailable: unknown network WIF prefix")
        print("Hexprivkey:          %s" % bytes_to_str(binascii.hexlify(secret)))
        if compressed:
            warnings.warn(
                "    For compressed keys, the hexadecimal private key sometimes contains an extra '01' at the end")
        print("Hash160:             %s" % bytes_to_str(binascii.hexlify(h160)))
        print("Pubkey:              %s" % bytes_to_str(binascii.hexlify(ser_public_key)))
        if int(binascii.hexlify(secret), 16) > _r:
            warnings.warn('/!\\ Beware, 0x%s is equivalent to 0x%.33x' % (binascii.hexlify(secret),
                                                                          int(binascii.hexlify(secret), 16) - _r))

    r = KeyInfo(secret, private_key, ser_public_key, uncompressed_ser_public_key, addr, wif, compressed)
    if network:
        ki = network.keyinfo(r, print_info=print_info)
        if ki:
            addr = ki.addr
        r = KeyInfo(secret, private_key, ser_public_key, uncompressed_ser_public_key, addr, wif, compressed)
    return r


def importprivkey(db, sec, label, reserve, verbose=True):
    k = keyinfo(sec, network, verbose)
    secret = k.secret
    private_key = k.private_key
    public_key = k.public_key
    addr = k.addr

    global crypter, passphrase, json_db
    crypted = False
    if 'mkey' in json_db.keys() and 'salt' in json_db['mkey']:
        crypted = True
    if crypted:
        if passphrase:
            cry_master = binascii.unhexlify(json_db['mkey']['encrypted_key'])
            cry_salt = binascii.unhexlify(json_db['mkey']['salt'])
            cry_rounds = json_db['mkey']['nDerivationIterations']
            cry_method = json_db['mkey']['nDerivationMethod']

            crypter.SetKeyFromPassphrase(passphrase, cry_salt, cry_rounds, cry_method)
            #			if verbose:
            #				print("Import with", passphrase, "", binascii.hexlify(cry_master), "", binascii.hexlify(cry_salt))
            masterkey = crypter.Decrypt(cry_master)
            crypter.SetKey(masterkey)
            crypter.SetIV(Hash(public_key))
            e = crypter.Encrypt(secret)
            ck_epk = e

            update_wallet(db, 'ckey', {'public_key': public_key, 'encrypted_private_key': ck_epk})
    else:
        update_wallet(db, 'key', {'public_key': public_key, 'private_key': private_key})

    if not reserve:
        update_wallet(db, 'name', {'hash': addr, 'name': label})

    return True


def balance(site, address):
    page = urllib.urlopen("%s%s" % (site, address))
    query_result = page.read()
    # If the initial API call returned an error, use a secondary API
    if query_result.startswith("error"):
        page = urllib.urlopen("%s%s" % (backup_balance_site, address))
        query_result = json.loads(page.read())["balance"]
    return query_result


def read_jsonfile(filename):
    filin = open(filename, 'r')
    txdump = filin.read()
    filin.close()
    return json.loads(txdump)


def write_jsonfile(filename, array):
    filout = open(filename, 'w')
    filout.write(json.dumps(array, sort_keys=True, indent=0))
    filout.close()


def export_all_keys(db, ks, filename):
    txt = ";".join(ks) + "\n"
    for i in db['keys']:
        try:
            j = i.copy()
            if 'label' not in j:
                j['label'] = '#Reserve'
            t = ";".join([str(j[k]) for k in ks])
            txt += t + "\n"
        except:
            return False

    try:
        myFile = open(filename, 'w')
        myFile.write(txt)
        myFile.close()
        return True
    except:
        return False


def import_csv_keys(filename, wdir, wname, nbremax=9999999):
    global global_merging_message
    if filename[0] == "\x00":  # yeah, dirty workaround
        content = filename[1:]
    else:
        filen = open(filename, "r")
        content = filen.read()
        filen.close()

    db_env = create_env(wdir)
    read_wallet(json_db, db_env, wname, True, True, "", None)
    db = open_wallet(db_env, wname, writable=True)

    content = content.split('\n')
    content = content[:min(nbremax, len(content))]
    for i in range(len(content)):
        c = content[i]
        global_merging_message = ["Merging: " + str(round(100.0 * (i + 1) // len(content), 1)) + "%" for j in range(2)]
        if ';' in c and len(c) > 0 and c[0] != "#":
            cs = c.split(';')
            sec, label = cs[0:2]
            reserve = False
            if label == "#Reserve":
                reserve = True
            importprivkey(db, sec, label, reserve, verbose=False)

    global_merging_message = ["Merging done.", ""]

    db.close()

    read_wallet(json_db, db_env, wname, True, True, "", None, True)  # Fill the pool if empty

    return True


def message_to_hash(msg, msgIsHex=False):
    str = ""
    #	str += '04%064x%064x'%(pubkey.point.x(), pubkey.point.y())
    #	str += "Padding text - "
    str += msg
    if msgIsHex:
        str = binascii.unhexlify(str)
    hash = Hash(str)
    return hash


def sign_message(secret, msg, msgIsHex=False):
    k = KEY()
    k.generate(secret)
    return k.sign(message_to_hash(msg, msgIsHex))


def verify_message_signature(pubkey, sign, msg, msgIsHex=False):
    k = KEY()
    k.set_pubkey(binascii.unhexlify(pubkey))
    return k.verify(message_to_hash(msg, msgIsHex), binascii.unhexlify(sign))


OP_DUP = 118;
OP_HASH160 = 169;
OP_EQUALVERIFY = 136;
OP_CHECKSIG = 172;

XOP_DUP = "%02x" % OP_DUP;
XOP_HASH160 = "%02x" % OP_HASH160;
XOP_EQUALVERIFY = "%02x" % OP_EQUALVERIFY;
XOP_CHECKSIG = "%02x" % OP_CHECKSIG;

BTC = 1e8


def ct(l_prevh, l_prevn, l_prevsig, l_prevpubkey, l_value_out, l_pubkey_out, is_msg_to_sign=-1, oldScriptPubkey=""):
    scriptSig = True
    if is_msg_to_sign != -1:
        scriptSig = False
        index = is_msg_to_sign

    ret = ""
    ret += inverse_str("%08x" % 1)
    nvin = len(l_prevh)
    ret += "%02x" % nvin

    for i in range(nvin):
        txin_ret = ""
        txin_ret2 = ""

        txin_ret += inverse_str(l_prevh[i])
        txin_ret += inverse_str("%08x" % l_prevn[i])

        if scriptSig:
            txin_ret2 += "%02x" % (1 + len(l_prevsig[i]) // 2)
            txin_ret2 += l_prevsig[i]
            txin_ret2 += "01"
            txin_ret2 += "%02x" % (len(l_prevpubkey[i]) // 2)
            txin_ret2 += l_prevpubkey[i]

            txin_ret += "%02x" % (len(txin_ret2) // 2)
            txin_ret += txin_ret2

        elif index == i:
            txin_ret += "%02x" % (len(oldScriptPubkey) // 2)
            txin_ret += oldScriptPubkey
        else:
            txin_ret += "00"

        ret += txin_ret
        ret += "ffffffff"

    nvout = len(l_value_out)
    ret += "%02x" % nvout
    for i in range(nvout):
        txout_ret = ""

        txout_ret += inverse_str("%016x" % (l_value_out[i]))
        txout_ret += "%02x" % (len(l_pubkey_out[i]) // 2 + 5)
        txout_ret += "%02x" % OP_DUP
        txout_ret += "%02x" % OP_HASH160
        txout_ret += "%02x" % (len(l_pubkey_out[i]) // 2)
        txout_ret += l_pubkey_out[i]
        txout_ret += "%02x" % OP_EQUALVERIFY
        txout_ret += "%02x" % OP_CHECKSIG
        ret += txout_ret

    ret += "00000000"
    if not scriptSig:
        ret += "01000000"
    return ret


def create_transaction(secret_key, hashes_txin, indexes_txin, pubkey_txin, prevScriptPubKey, amounts_txout,
                       scriptPubkey):
    li1 = len(secret_key)
    li2 = len(hashes_txin)
    li3 = len(indexes_txin)
    li4 = len(pubkey_txin)
    li5 = len(prevScriptPubKey)

    if li1 != li2 or li2 != li3 or li3 != li4 or li4 != li5:
        print("Error in the number of tx inputs")
        exit(0)

    lo1 = len(amounts_txout)
    lo2 = len(scriptPubkey)

    if lo1 != lo2:
        print("Error in the number of tx outputs")
        exit(0)

    sig_txin = []
    i = 0
    for cpt in hashes_txin:
        sig_txin.append(sign_message(binascii.unhexlify(secret_key[i]),
                                     ct(hashes_txin, indexes_txin, sig_txin, pubkey_txin, amounts_txout, scriptPubkey,
                                        i, prevScriptPubKey[i]), True) + "01")
        i += 1

    tx = ct(hashes_txin, indexes_txin, sig_txin, pubkey_txin, amounts_txout, scriptPubkey)
    hashtx = binascii.hexlify(Hash(binascii.unhexlify(tx)))

    for i in range(len(sig_txin)):
        try:
            verify_message_signature(pubkey_txin[i], sig_txin[i][:-2],
                                     ct(hashes_txin, indexes_txin, sig_txin, pubkey_txin, amounts_txout, scriptPubkey,
                                        i, prevScriptPubKey[i]), True)
            print("sig %2d: verif ok" % i)
        except:
            print("sig %2d: verif error" % i)
            exit(0)

    #	tx += end_of_wallettx([], int(time.time()))
    #	return [inverse_str(hashtx), "027478" + hashtx, tx]
    return [inverse_str(hashtx), "", tx]


def inverse_str(string):
    ret = ""
    for i in range(len(string) // 2):
        ret += string[len(string) - 2 - 2 * i];
        ret += string[len(string) - 2 - 2 * i + 1];
    return ret


def read_table(table, beg, end):
    rows = table.split(beg)
    for i in range(len(rows)):
        rows[i] = rows[i].split(end)[0]
    return rows


def read_blockexplorer_table(table):
    cell = []
    rows = read_table(table, '<tr>', '</tr>')
    for i in range(len(rows)):
        cell.append(read_table(rows[i], '<td>', '</td>'))
        del cell[i][0]
    del cell[0]
    del cell[0]
    return cell


txin_amounts = Bdict({})


def bc_address_to_available_tx(address, testnet=False):
    TN = ""
    if testnet:
        TN = "testnet"

    blockexplorer_url = "http://blockexplorer.com/" + TN + "/address/"
    ret = ""
    txin = []
    txin_no = Bdict({})
    global txin_amounts
    txout = []
    balance = 0
    txin_is_used = Bdict({})

    page = urllib.urlopen("%s/%s" % (blockexplorer_url, address))
    try:
        table = page.read().split('<table class="txtable">')[1]
        table = table.split("</table>")[0]
    except:
        return {address: []}

    cell = read_blockexplorer_table(table)

    for i in range(len(cell)):
        txhash = read_table(cell[i][0], '/tx/', '#')[1]
        post_hash = read_table(cell[i][0], '#', '">')[1]
        io = post_hash[0]
        no_tx = post_hash[1:]
        if io in 'i':
            txout.append([txhash, post_hash])
        else:
            txin.append(txhash + no_tx)
            txin_no[txhash + no_tx] = post_hash[1:]
            txin_is_used[txhash + no_tx] = 0

        # hashblock = read_table(cell[i][1], '/block/', '">')[1]
        # blocknumber = read_table(cell[i][1], 'Block ', '</a>')[1]

        txin_amounts[txhash + no_tx] = round(float(cell[i][2]), 8)

        #		if cell[i][3][:4] in 'Sent' and io in 'o':
        #			print(cell[i][3][:4])
        #			print(io)
        #			return 'error'
        #		if cell[i][3][:4] in 'Rece' and io in 'i':
        #			print(cell[i][3][:4])
        #			print(io)
        #			return 'error'

        balance = round(float(cell[i][5]), 8)

    for tx in txout:
        pagetx = urllib.urlopen("http://blockexplorer.com/" + TN + "/tx/" + tx[0])
        table_in = \
            pagetx.read().split('<a name="outputs">Outputs</a>')[0].split('<table class="txtable">')[1].split(
                "</table>")[0]

        cell = read_blockexplorer_table(table_in)
        for i in range(len(cell)):
            txhash = read_table(cell[i][0], '/tx/', '#')[1]
            no_tx = read_table(cell[i][0], '#', '">')[1][1:]

            if txhash + no_tx in txin:
                txin_is_used[txhash + no_tx] = 1

    ret = []
    for tx in txin:
        if not txin_is_used[tx]:
            ret.append([tx, txin_amounts[tx], txin_no[tx]])

    return {address: ret}


empty_txin = Bdict({'hash': '', 'index': '', 'sig': '##', 'pubkey': '', 'oldscript': '', 'addr': ''})
empty_txout = Bdict({'amount': '', 'script': ''})


class tx():
    ins = []
    outs = []
    tosign = False

    def hashtypeone(self, index, script):
        global empty_txin
        for i in range(len(self.ins)):
            self.ins[i] = empty_txin
        self.ins[index]['pubkey'] = ""
        self.ins[index]['oldscript'] = script
        self.tosign = True

    def copy(self):
        r = tx()
        r.ins = self.ins[:]
        r.outs = self.outs[:]
        return r

    def sign(self, n=-1):
        if n == -1:
            for i in range(len(self.ins)):
                self.sign(i)
                return "done"

        global json_db
        txcopy = self.copy()
        txcopy.hashtypeone(n, self.ins[n]['oldscript'])

        sec = ''
        for k in json_db['keys']:
            if k['addr'] == self.ins[n]['addr'] and 'hexsec' in k:
                sec = k['hexsec']
        if sec == '':
            print("priv key not found (addr:" + self.ins[n]['addr'] + ")")
            return ""

        self.ins[n]['sig'] = sign_message(binascii.unhexlify(sec), txcopy.get_tx(), True)

    def ser(self):
        r = Bdict({})
        r['ins'] = self.ins
        r['outs'] = self.outs
        r['tosign'] = self.tosign
        return json.dumps(r)

    def unser(self, r):
        s = json.loads(r)
        self.ins = s['ins']
        self.outs = s['outs']
        self.tosign = s['tosign']

    def get_tx(self):
        ret = inverse_str("%08x" % 1)
        ret += "%02x" % len(self.ins)

        for i in range(len(self.ins)):
            txin = self.ins[i]
            ret += inverse_str(txin['hash'])
            ret += inverse_str("%08x" % txin['index'])

            if txin['pubkey'] != "":
                tmp = ""
                tmp += "%02x" % (1 + len(txin['sig']) // 2)
                tmp += txin['sig']
                tmp += "01"
                tmp += "%02x" % (len(txin['pubkey']) // 2)
                tmp += txin['pubkey']

                ret += "%02x" % (len(tmp) / 2)
                ret += tmp

            elif txin['oldscript'] != "":
                ret += "%02x" % (len(txin['oldscript']) // 2)
                ret += txin['oldscript']

            else:
                ret += "00"

            ret += "ffffffff"

        ret += "%02x" % len(self.outs)

        for i in range(len(self.outs)):
            txout = self.outs[i]
            ret += inverse_str("%016x" % (txout['amount']))

            if txout['script'][:2] == 's:':  # script
                script = txout['script'][2:]
                ret += "%02x" % (len(script) // 2)
                ret += script
            else:  # address
                ret += "%02x" % (len(txout['script']) // 2 + 5)
                ret += "%02x" % OP_DUP
                ret += "%02x" % OP_HASH160
                ret += "%02x" % (len(txout['script']) // 2)
                ret += txout['script']
                ret += "%02x" % OP_EQUALVERIFY
                ret += "%02x" % OP_CHECKSIG

        ret += "00000000"
        if not self.tosign:
            ret += "01000000"
        return ret


def update_pyw():
    global md5_pywallet
    md5_pywallet = md5_2(__file__)  # Get MD5 of current file
    if md5_last_pywallet[0] and md5_last_pywallet[1] != md5_pywallet:
        dl = urllib.urlopen('https://raw.github.com/jackjack-jj/pywallet/master/pywallet.py').read()
        if len(dl) > 40 and md5_2(dl) == md5_last_pywallet[1]:
            filout = open(pyw_path + "/" + pyw_filename, 'w')
            filout.write(dl)
            filout.close()
        else:
            return "Problem when downloading new version (" + md5_2(dl) + "/" + md5_last_pywallet[1] + ")"


def clone_wallet(parentPath, clonePath):
    types, datas = [], []
    parentdir, parentname = os.path.split(parentPath)
    wdir, wname = os.path.split(clonePath)

    db_env = create_env(parentdir)
    read_wallet(json_db, db_env, parentname, True, True, "", False)

    types.append('version')
    datas.append({'version': json_db['version']})
    types.append('defaultkey')
    datas.append({'key': json_db['defaultkey']})
    for k in json_db['keys']:
        types.append('ckey')
        datas.append({'public_key': binascii.unhexlify(k['pubkey']),
                      'encrypted_private_key': binascii.unhexlify(random_string(96))})
    for k in json_db['pool']:
        types.append('pool')
        datas.append({'n': k['n'], 'nVersion': k['nVersion'], 'nTime': k['nTime'],
                      'public_key': binascii.unhexlify(k['public_key_hex'])})
    for addr, label in json_db['names'].items():
        types.append('name')
        datas.append({'hash': addr, 'name': 'Watch:' + label})

    db_env = create_env(wdir)
    create_new_wallet(db_env, wname, 60000)

    db = open_wallet(db_env, wname, True)
    NPP_salt = binascii.unhexlify(random_string(16))
    NPP_rounds = int(50000 + random.random() * 20000)
    NPP_method = 0
    NPP_MK = binascii.unhexlify(random_string(64))
    crypter.SetKeyFromPassphrase(random_string(64), NPP_salt, NPP_rounds, NPP_method)
    NPP_EMK = crypter.Encrypt(NPP_MK)
    update_wallet(db, 'mkey', {
        "encrypted_key": NPP_EMK,
        'nDerivationIterations': NPP_rounds,
        'nDerivationMethod': NPP_method,
        'nID': 1,
        'otherParams': b'',
        "salt": NPP_salt
    })
    db.close()

    read_wallet(json_db, db_env, wname, True, True, "", False)

    db = open_wallet(db_env, wname, writable=True)
    update_wallet(db, types, datas, True)
    db.close()
    print("Wallet successfully cloned to:\n   %s" % clonePath)


md5_last_pywallet = [False, ""]


def retrieve_last_pywallet_md5():
    global md5_last_pywallet
    md5_last_pywallet = [True, md5_onlinefile('https://raw.github.com/jackjack-jj/pywallet/master/pywallet.py')]


def find_wallet_files(directory):
    """
    Find all wallet.dat files in the specified directory and its subdirectories
    
    Args:
        directory (str): Directory to search in
        
    Returns:
        list: List of full paths to wallet.dat files
    """
    wallet_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower() == "wallet.dat":
                wallet_files.append(os.path.join(root, file))
    
    return wallet_files


from optparse import OptionParser
import subprocess


def bech32_polymod(values):
    GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        b = (chk >> 25)
        chk = (chk & 0x1ffffff) << 5 ^ v
        for i in range(5):
            chk ^= GEN[i] if ((b >> i) & 1) else 0
    return chk


def bech32_hrp_expand(s):
    return [ordsix(x) >> 5 for x in s] + [0] + [ordsix(x) & 31 for x in s]


def bech32_verify_checksum(hrp, data):
    return bech32_polymod(bech32_hrp_expand(hrp) + data) == 1


def bech32_create_checksum(hrp, data):
    values = bech32_hrp_expand(hrp) + data
    polymod = bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


BECH32_ALPH = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'
BASE32_ALPH = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'


def witprog_to_bech32_addr(witprog, network, witv=0):
    x = base64.b32encode(witprog)
    if PY3: x = x.decode()
    x = x.replace('=', '')
    data = [witv] + list(map(lambda y: BASE32_ALPH.index(y), x))
    combined = data + bech32_create_checksum(network.segwit_hrp, data)
    addr = network.segwit_hrp + '1' + ''.join([BECH32_ALPH[d] for d in combined])
    return addr


def p2sh_script_to_addr(script):
    version = 5
    return hash_160_to_bc_address(hash_160(script), version)


def whitepaper():
    try:
        rawtx = subprocess.check_output(
            ["bitcoin-cli", "getrawtransaction", "54e48e5f5c656b26c3bca14a8c95aa583d07ebe84dde3b7dd4a78f4e4186e713"])
    except:
        rawtx = urllib.urlopen(
            "https://blockchain.info/tx/54e48e5f5c656b26c3bca14a8c95aa583d07ebe84dde3b7dd4a78f4e4186e713?format=hex").read()
    outputs = rawtx.split("0100000000000000")
    pdf = b""
    for output in outputs[1:-2]:
        i = 6
        pdf += binascii.unhexlify(output[i:i + 130])
        i += 132
        pdf += binascii.unhexlify(output[i:i + 130])
        i += 132
        pdf += binascii.unhexlify(output[i:i + 130])
    pdf += binascii.unhexlify(outputs[-2][6:-4])
    content = pdf[8:-8]
    assert hashlib.sha256(content).hexdigest() == 'b1674191a88ec5cdd733e4240a81803105dc412d6c6708d53ab94fc248f4f553'
    filename = 'bitcoin_whitepaper'
    while os.path.exists(filename + '.pdf'):
        filename += '_'
    with open(filename + '.pdf', "wb") as f:
        f.write(content)
    print("Wrote the Bitcoin whitepaper to %s.pdf" % filename)


bip39_wordlist = '''
 abandon ability able about above absent absorb abstract absurd abuse access accident account accuse achieve acid acoustic acquire across act action actor actress actual adapt add addict address adjust admit adult advance advice aerobic affair afford afraid again age agent agree ahead aim air
 airport aisle alarm album alcohol alert alien all alley allow almost alone alpha already also alter always amateur amazing among amount amused analyst anchor ancient anger angle angry animal ankle announce annual another answer antenna antique anxiety any apart apology appear apple approve april
 arch arctic area arena argue arm armed armor army around arrange arrest arrive arrow art artefact artist artwork ask aspect assault asset assist assume asthma athlete atom attack attend attitude attract auction audit august aunt author auto autumn average avocado avoid awake aware away awesome
 awful awkward axis baby bachelor bacon badge bag balance balcony ball bamboo banana banner bar barely bargain barrel base basic basket battle beach bean beauty because become beef before begin behave behind believe below belt bench benefit best betray better between beyond bicycle bid bike bind
 biology bird birth bitter black blade blame blanket blast bleak bless blind blood blossom blouse blue blur blush board boat body boil bomb bone bonus book boost border boring borrow boss bottom bounce box boy bracket brain brand brass brave bread breeze brick bridge brief bright bring brisk
 broccoli broken bronze broom brother brown brush bubble buddy budget buffalo build bulb bulk bullet bundle bunker burden burger burst bus business busy butter buyer buzz cabbage cabin cable cactus cage cake call calm camera camp can canal cancel candy cannon canoe canvas canyon capable capital
 captain car carbon card cargo carpet carry cart case cash casino castle casual cat catalog catch category cattle caught cause caution cave ceiling celery cement census century cereal certain chair chalk champion change chaos chapter charge chase chat cheap check cheese chef cherry chest chicken
 chief child chimney choice choose chronic chuckle chunk churn cigar cinnamon circle citizen city civil claim clap clarify claw clay clean clerk clever click client cliff climb clinic clip clock clog close cloth cloud clown club clump cluster clutch coach coast coconut code coffee coil coin collect
 color column combine come comfort comic common company concert conduct confirm congress connect consider control convince cook cool copper copy coral core corn correct cost cotton couch country couple course cousin cover coyote crack cradle craft cram crane crash crater crawl crazy cream credit
 creek crew cricket crime crisp critic crop cross crouch crowd crucial cruel cruise crumble crunch crush cry crystal cube culture cup cupboard curious current curtain curve cushion custom cute cycle dad damage damp dance danger daring dash daughter dawn day deal debate debris decade december decide
 decline decorate decrease deer defense define defy degree delay deliver demand demise denial dentist deny depart depend deposit depth deputy derive describe desert design desk despair destroy detail detect develop device devote diagram dial diamond diary dice diesel diet differ digital dignity
 dilemma dinner dinosaur direct dirt disagree discover disease dish dismiss disorder display distance divert divide divorce dizzy doctor document dog doll dolphin domain donate donkey donor door dose double dove draft dragon drama drastic draw dream dress drift drill drink drip drive drop drum dry
 duck dumb dune during dust dutch duty dwarf dynamic eager eagle early earn earth easily east easy echo ecology economy edge edit educate effort egg eight either elbow elder electric elegant element elephant elevator elite else embark embody embrace emerge emotion employ empower empty enable enact
 end endless endorse enemy energy enforce engage engine enhance enjoy enlist enough enrich enroll ensure enter entire entry envelope episode equal equip era erase erode erosion error erupt escape essay essence estate eternal ethics evidence evil evoke evolve exact example excess exchange excite
 exclude excuse execute exercise exhaust exhibit exile exist exit exotic expand expect expire explain expose express extend extra eye eyebrow fabric face faculty fade faint faith fall false fame family famous fan fancy fantasy farm fashion fat fatal father fatigue fault favorite feature february
 federal fee feed feel female fence festival fetch fever few fiber fiction field figure file film filter final find fine finger finish fire firm first fiscal fish fit fitness fix flag flame flash flat flavor flee flight flip float flock floor flower fluid flush fly foam focus fog foil fold follow
 food foot force forest forget fork fortune forum forward fossil foster found fox fragile frame frequent fresh friend fringe frog front frost frown frozen fruit fuel fun funny furnace fury future gadget gain galaxy gallery game gap garage garbage garden garlic garment gas gasp gate gather gauge
 gaze general genius genre gentle genuine gesture ghost giant gift giggle ginger giraffe girl give glad glance glare glass glide glimpse globe gloom glory glove glow glue goat goddess gold good goose gorilla gospel gossip govern gown grab grace grain grant grape grass gravity great green grid grief
 grit grocery group grow grunt guard guess guide guilt guitar gun gym habit hair half hammer hamster hand happy harbor hard harsh harvest hat have hawk hazard head health heart heavy hedgehog height hello helmet help hen hero hidden high hill hint hip hire history hobby hockey hold hole holiday
 hollow home honey hood hope horn horror horse hospital host hotel hour hover hub huge human humble humor hundred hungry hunt hurdle hurry hurt husband hybrid ice icon idea identify idle ignore ill illegal illness image imitate immense immune impact impose improve impulse inch include income
 increase index indicate indoor industry infant inflict inform inhale inherit initial inject injury inmate inner innocent input inquiry insane insect inside inspire install intact interest into invest invite involve iron island isolate issue item ivory jacket jaguar jar jazz jealous jeans jelly
 jewel job join joke journey joy judge juice jump jungle junior junk just kangaroo keen keep ketchup key kick kid kidney kind kingdom kiss kit kitchen kite kitten kiwi knee knife knock know lab label labor ladder lady lake lamp language laptop large later latin laugh laundry lava law lawn lawsuit
 layer lazy leader leaf learn leave lecture left leg legal legend leisure lemon lend length lens leopard lesson letter level liar liberty library license life lift light like limb limit link lion liquid list little live lizard load loan lobster local lock logic lonely long loop lottery loud lounge
 love loyal lucky luggage lumber lunar lunch luxury lyrics machine mad magic magnet maid mail main major make mammal man manage mandate mango mansion manual maple marble march margin marine market marriage mask mass master match material math matrix matter maximum maze meadow mean measure meat
 mechanic medal media melody melt member memory mention menu mercy merge merit merry mesh message metal method middle midnight milk million mimic mind minimum minor minute miracle mirror misery miss mistake mix mixed mixture mobile model modify mom moment monitor monkey monster month moon moral
 more morning mosquito mother motion motor mountain mouse move movie much muffin mule multiply muscle museum mushroom music must mutual myself mystery myth naive name napkin narrow nasty nation nature near neck need negative neglect neither nephew nerve nest net network neutral never news next nice
 night noble noise nominee noodle normal north nose notable note nothing notice novel now nuclear number nurse nut oak obey object oblige obscure observe obtain obvious occur ocean october odor off offer office often oil okay old olive olympic omit once one onion online only open opera opinion
 oppose option orange orbit orchard order ordinary organ orient original orphan ostrich other outdoor outer output outside oval oven over own owner oxygen oyster ozone pact paddle page pair palace palm panda panel panic panther paper parade parent park parrot party pass patch path patient patrol
 pattern pause pave payment peace peanut pear peasant pelican pen penalty pencil people pepper perfect permit person pet phone photo phrase physical piano picnic picture piece pig pigeon pill pilot pink pioneer pipe pistol pitch pizza place planet plastic plate play please pledge pluck plug plunge
 poem poet point polar pole police pond pony pool popular portion position possible post potato pottery poverty powder power practice praise predict prefer prepare present pretty prevent price pride primary print priority prison private prize problem process produce profit program project promote
 proof property prosper protect proud provide public pudding pull pulp pulse pumpkin punch pupil puppy purchase purity purpose purse push put puzzle pyramid quality quantum quarter question quick quit quiz quote rabbit raccoon race rack radar radio rail rain raise rally ramp ranch random range
 rapid rare rate rather raven raw razor ready real reason rebel rebuild recall receive recipe record recycle reduce reflect reform refuse region regret regular reject relax release relief rely remain remember remind remove render renew rent reopen repair repeat replace report require rescue
 resemble resist resource response result retire retreat return reunion reveal review reward rhythm rib ribbon rice rich ride ridge rifle right rigid ring riot ripple risk ritual rival river road roast robot robust rocket romance roof rookie room rose rotate rough round route royal rubber rude rug
 rule run runway rural sad saddle sadness safe sail salad salmon salon salt salute same sample sand satisfy satoshi sauce sausage save say scale scan scare scatter scene scheme school science scissors scorpion scout scrap screen script scrub sea search season seat second secret section security
 seed seek segment select sell seminar senior sense sentence series service session settle setup seven shadow shaft shallow share shed shell sheriff shield shift shine ship shiver shock shoe shoot shop short shoulder shove shrimp shrug shuffle shy sibling sick side siege sight sign silent silk
 silly silver similar simple since sing siren sister situate six size skate sketch ski skill skin skirt skull slab slam sleep slender slice slide slight slim slogan slot slow slush small smart smile smoke smooth snack snake snap sniff snow soap soccer social sock soda soft solar soldier solid
 solution solve someone song soon sorry sort soul sound soup source south space spare spatial spawn speak special speed spell spend sphere spice spider spike spin spirit split spoil sponsor spoon sport spot spray spread spring spy square squeeze squirrel stable stadium staff stage stairs stamp
 stand start state stay steak steel stem step stereo stick still sting stock stomach stone stool story stove strategy street strike strong struggle student stuff stumble style subject submit subway success such sudden suffer sugar suggest suit summer sun sunny sunset super supply supreme sure
 surface surge surprise surround survey suspect sustain swallow swamp swap swarm swear sweet swift swim swing switch sword symbol symptom syrup system table tackle tag tail talent talk tank tape target task taste tattoo taxi teach team tell ten tenant tennis tent term test text thank that theme
 then theory there they thing this thought three thrive throw thumb thunder ticket tide tiger tilt timber time tiny tip tired tissue title toast tobacco today toddler toe together toilet token tomato tomorrow tone tongue tonight tool tooth top topic topple torch tornado tortoise toss total tourist
 toward tower town toy track trade traffic tragic train transfer trap trash travel tray treat tree trend trial tribe trick trigger trim trip trophy trouble truck true truly trumpet trust truth try tube tuition tumble tuna tunnel turkey turn turtle twelve twenty twice twin twist two type typical
 ugly umbrella unable unaware uncle uncover under undo unfair unfold unhappy uniform unique unit universe unknown unlock until unusual unveil update upgrade uphold upon upper upset urban urge usage use used useful useless usual utility vacant vacuum vague valid valley valve van vanish vapor various
 vast vault vehicle velvet vendor venture venue verb verify version very vessel veteran viable vibrant vicious victory video view village vintage violin virtual virus visa visit visual vital vivid vocal voice void volcano volume vote voyage wage wagon wait walk wall walnut want warfare warm warrior
 wash wasp waste water wave way wealth weapon wear weasel weather web wedding weekend weird welcome west wet whale what wheat wheel when where whip whisper wide width wife wild will win window wine wing wink winner winter wire wisdom wise wish witness wolf woman wonder wood wool word work world
 worry worth wrap wreck wrestle wrist write wrong yard year yellow you young youth zebra zero zone zoo
'''.split()

PBKDF2_ROUNDS = 2048


def binary_search(a, x, lo, hi):
    hi = hi if hi is not None else len(a)
    pos = bisect.bisect_left(a, x, lo, hi)
    return pos if pos != hi and a[pos] == x else -1


class Mnemonic(object):
    def __init__(self):
        self.language = "english"
        self.radix = 2048
        self.wordlist = bip39_wordlist
        if len(self.wordlist) != self.radix:
            raise ValueError("Wordlist should contain {} words, but it's {} words long instead.".format(self.radix,
                                                                                                        len(self.wordlist)))

    @staticmethod
    def normalize_string(txt):
        if isinstance(txt, bytes):
            utxt = txt.decode("utf8")
        elif isinstance(txt, str):
            utxt = txt
        else:
            raise TypeError("String value expected")
        return unicodedata.normalize("NFKD", utxt)

    def generate(self, strength=128):
        if strength not in [128, 160, 192, 224, 256]:
            raise ValueError("Invalid strength value. Allowed values are [128, 160, 192, 224, 256].")
        return self.to_mnemonic(os.urandom(strength // 8))

    def to_entropy(self, words):
        if not isinstance(words, list):
            words = words.split(" ")
        if len(words) not in [12, 15, 18, 21, 24]:
            raise ValueError(
                "Number of words must be one of the following: [12, 15, 18, 21, 24], but it is not (%d)." % len(words))
        concatLenBits = len(words) * 11
        concatBits = [False] * concatLenBits
        wordindex = 0
        if self.language == "english":
            use_binary_search = True
        else:
            use_binary_search = False
        for word in words:
            ndx = (
                binary_search(self.wordlist, word)
                if use_binary_search
                else self.wordlist.index(word)
            )
            if ndx < 0:
                raise LookupError('Unable to find "%s" in word list.' % word)
            for ii in range(11):
                concatBits[(wordindex * 11) + ii] = (ndx & (1 << (10 - ii))) != 0
            wordindex += 1
        checksumLengthBits = concatLenBits // 33
        entropyLengthBits = concatLenBits - checksumLengthBits
        entropy = bytearray(entropyLengthBits // 8)
        for ii in range(len(entropy)):
            for jj in range(8):
                if concatBits[(ii * 8) + jj]:
                    entropy[ii] |= 1 << (7 - jj)
        hashBytes = hashlib.sha256(entropy).digest()
        hashBits = list(
            itertools.chain.from_iterable(
                [c & (1 << (7 - i)) != 0 for i in range(8)] for c in hashBytes
            )
        )
        for i in range(checksumLengthBits):
            if concatBits[entropyLengthBits + i] != hashBits[i]:
                raise ValueError("Failed checksum.")
        return entropy

    def to_mnemonic(self, data):
        if len(data) not in [16, 20, 24, 28, 32]:
            raise ValueError(
                "Data length should be one of the following: [16, 20, 24, 28, 32], but is {}.".format(len(data)))
        h = hashlib.sha256(data).hexdigest()
        b = (
                bin(int.from_bytes(data, byteorder="big"))[2:].zfill(len(data) * 8)
                + bin(int(h, 16))[2:].zfill(256)[: len(data) * 8 // 32]
        )
        result = []
        for i in range(len(b) // 11):
            idx = int(b[i * 11: (i + 1) * 11], 2)
            result.append(self.wordlist[idx])
        if self.language == "japanese":
            result_phrase = "\u3000".join(result)
        else:
            result_phrase = " ".join(result)
        return result_phrase

    def check(self, mnemonic):
        mnemonic_list = self.normalize_string(mnemonic).split(" ")
        if len(mnemonic_list) not in [12, 15, 18, 21, 24]:
            return False
        try:
            idx = map(lambda x: bin(self.wordlist.index(x))[2:].zfill(11), mnemonic_list)
            b = "".join(idx)
        except ValueError:
            return False
        l = len(b)  # noqa: E741
        d = b[: l // 33 * 32]
        h = b[-l // 33:]
        nd = int(d, 2).to_bytes(l // 33 * 4, byteorder="big")
        nh = bin(int(hashlib.sha256(nd).hexdigest(), 16))[2:].zfill(256)[: l // 33]
        return h == nh

    def expand_word(self, prefix):
        if prefix in self.wordlist:
            return prefix
        else:
            matches = [word for word in self.wordlist if word.startswith(prefix)]
            if len(matches) == 1:  # matched exactly one word in the wordlist
                return matches[0]
            else:
                return prefix

    def expand(self, mnemonic):
        return " ".join(map(self.expand_word, mnemonic.split(" ")))

    @classmethod
    def to_seed(cls, mnemonic, passphrase=""):
        mnemonic = cls.normalize_string(mnemonic)
        passphrase = cls.normalize_string(passphrase)
        passphrase = "mnemonic" + passphrase
        mnemonic_bytes = mnemonic.encode("utf-8")
        passphrase_bytes = passphrase.encode("utf-8")
        stretched = hashlib.pbkdf2_hmac("sha512", mnemonic_bytes, passphrase_bytes, PBKDF2_ROUNDS)
        return stretched[:64]

    @classmethod
    def mnemonic_to_xprv(cls, mnemonic, passphrase=""):
        seed = cls.to_seed(mnemonic, passphrase)
        return Xpriv.from_seed(seed)

    @staticmethod
    def to_hd_master_key(seed, testnet=False):
        if len(seed) != 64:
            raise ValueError("Provided seed should have length of 64")
        seed = hmac.new(b"Bitcoin seed", seed, digestmod=hashlib.sha512).digest()
        xprv = b"\x04\x88\xad\xe4"  # Version for private mainnet
        if testnet:
            xprv = b"\x04\x35\x83\x94"  # Version for private testnet
        xprv += b"\x00" * 9  # Depth, parent fingerprint, and child number
        xprv += seed[32:]  # Chain code
        xprv += b"\x00" + seed[:32]  # Master key
        hashed_xprv = hashlib.sha256(xprv).digest()
        hashed_xprv = hashlib.sha256(hashed_xprv).digest()
        xprv += hashed_xprv[:4]
        return b58encode(xprv)


bip39_mnemonic = Mnemonic()


def parse_ckd_path(str_path):
    str_path = str_path.lstrip('m/')
    path_split = []
    for j in str_path.split('/'):
        if not j: continue
        hardened = 0
        if j.endswith("'") or j.lower().endswith("h"):
            hardened = 0x80000000
            j = j[:-1]
        try:
            path_split.append([int(j) + hardened])
        except:
            a, b = map(int, j.split('-'))
            path_split.append(list(range(a + hardened, b + 1 + hardened)))
    return path_split


class Xpriv(collections.namedtuple('XprivNT', 'version depth prt_fpr childnr cc ktype key')):
    xpriv_fmt = '>IB4sI32sB32s'

    def __new__(cls, *a, **kw):
        self = super(Xpriv, cls).__new__(cls, *a, **kw)
        self.fullpath = 'm'
        return self

    @classmethod
    def xpriv_version_bytes(cls):
        return 0x0488ADE4

    @classmethod
    def xpub_version_bytes(cls):
        return 0x0488B21E

    @classmethod
    def from_mnemomic(cls, mnemonic, passphrase=""):
        return bip39_mnemonic.mnemonic_to_xprv(mnemonic, passphrase)

    @classmethod
    def from_seed(cls, s, seed=b'Bitcoin seed'):
        I = hmac.new(seed, s, digestmod=hashlib.sha512).digest()
        mk, cc = I[:32], I[32:]
        return cls(cls.xpriv_version_bytes(), 0, b'\x00' * 4, 0, cc, 0, mk)

    def clone(self):
        return self.__class__.b58decode(self.b58encode())

    def b58encode(self):
        return EncodeBase58Check(struct.pack(self.xpriv_fmt, *self._asdict().values()))

    def address(self, **kw):
        return keyinfo(self, kw.get('network'), False, True).addr

    def key_hex(self):
        return binascii.hexlify(self.key)

    def xpub(self, **kw):
        pubk = keyinfo(self, None, False, True).public_key
        xpub_content = self.clone()._replace(version=self.xpub_version_bytes(), ktype=ordsix(pubk[0]), key=pubk[1:])
        return EncodeBase58Check(struct.pack(self.xpriv_fmt, *xpub_content))

    @classmethod
    def b58decode(cls, b58xpriv):
        return cls(*struct.unpack(cls.xpriv_fmt, DecodeBase58Check(b58xpriv)))

    def multi_ckd_xpriv(self, str_path):
        path_split = parse_ckd_path(str_path)
        rev_path_split = path_split[::-1]
        xprivs = [self]
        while rev_path_split:
            children_nrs = rev_path_split.pop()
            xprivs = [parent.ckd_xpriv(child_nr) for parent in xprivs for child_nr in children_nrs]
        return xprivs

    def set_fullpath(self, base, x):
        self.fullpath = base + '/' + ("%d'" % (x - 0x80000000) if x >= 0x80000000 else "%d" % x)
        return self

    def ckd_xpriv(self, *indexes):
        if indexes.__class__ != tuple:
            indexes = [indexes]
        if indexes[0].__class__ != int:
            indexes = list(map(lambda x: x[0], parse_ckd_path(indexes[0])))
        i = indexes[0]
        if i < 0:
            i = 0x80000000 - i
        assert self.ktype == 0
        par_pubk = keyinfo(self, None, False, True).public_key
        seri = struct.pack('>I', i)
        if i >= 0x80000000:
            I = hmac.new(self.cc, b'\x00' + self.key + seri, digestmod=hashlib.sha512).digest()
        else:
            I = hmac.new(self.cc, par_pubk + seri, digestmod=hashlib.sha512).digest()
        il, ir = I[:32], I[32:]
        pk = hex((int(binascii.hexlify(il), 16) + int(binascii.hexlify(self.key), 16)) % _r)[2:].replace('L', '').zfill(
            64)
        child = self.__class__(self.version, self.depth + 1, hash_160(par_pubk)[:4], i, ir, 0,
                               binascii.unhexlify(pk)).set_fullpath(self.fullpath, i)
        if len(indexes) >= 2:
            return child.ckd_xpriv(*indexes[1:])
        return child

    def hprivcontent(self):
        return binascii.hexlify(DecodeBase58Check(self.b58encode()))

    def hpubcontent(self):
        return binascii.hexlify(DecodeBase58Check(self.xpub()))

    def keyinfo(self, network_name='Bitcoin'):
        keyinfo(self, network_name, True, False)
        print()
        keyinfo(self, network_name, True, True)


def dump_bip32_privkeys(xpriv, paths='m/0', fmt='addr', **kw):
    if fmt == 'addr':
        dump_key = lambda x: x.addr
    elif fmt == 'privkey':
        dump_key = lambda x: bytes_to_str(binascii.hexlify(x.secret))
    elif fmt == 'addrprivkey':
        dump_key = lambda x: x.addr + ' ' + bytes_to_str(binascii.hexlify(x.secret))
    elif fmt == 'addrwif':
        dump_key = lambda x: x.addr + ' ' + x.wif
    else:
        dump_key = lambda x: x.wif
    try:
        xpriv = Xpriv.b58decode(xpriv)
    except:
        pass
    for child in xpriv.multi_ckd_xpriv(paths):
        print('%s: %s' % (child.fullpath, dump_key(keyinfo(child, kw.get('network'), False, True))))


class TestPywallet(unittest.TestCase):
    def setUp(self):
        super(TestPywallet, self).setUp()
        warnings.simplefilter('ignore')

    def test_btc_privkey_1(self):
        key = keyinfo('1', network=network_bitcoin, force_compressed=False)
        self.assertEqual(key.addr, '1EHNa6Q4Jz2uvNExL497mE43ikXhwF6kZm')
        self.assertEqual(key.wif, '5HpHagT65TZzG1PH3CSu63k8DbpvD8s5ip4nEB3kEsreAnchuDf')
        self.assertEqual(key.secret, b'\x00' * 31 + b'\x01')
        self.assertFalse(key.compressed)

    def test_btc_privkey_1_from_wif(self):
        key = keyinfo('5HpHagT65TZzG1PH3CSu63k8DbpvD8s5ip4nEB3kEsreAnchuDf', network=network_bitcoin,
                      force_compressed=False)
        self.assertEqual(key.addr, '1EHNa6Q4Jz2uvNExL497mE43ikXhwF6kZm')

    def test_bad_privkey_format(self):
        with self.assertRaises(Exception):
            keyinfo('g', network=network_bitcoin)

    def test_btc_bip32_test_vectors(self):
        self.assertEqual(
            Xpriv.from_seed(binascii.unhexlify('000102030405060708090a0b0c0d0e0f'))
            .ckd_xpriv(0x80000000, 1, -2, 2, 1000000000).xpub(),
            'xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTvXEYBVPamhGW6cFJodrTHy'
        )
        self.assertEqual(
            Xpriv.from_seed(binascii.unhexlify(
                'fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542'))
            .ckd_xpriv(0, -2147483647, 1, -2147483646, 2).xpub(),
            'xpub6FnCn6nSzZAw5Tw7cgR9bi15UV96gLZhjDstkXXxvCLsUXBGXPdSnLFbdpq8p9HmGsApME5hQTZ3emM2rnY5agb9rXpVGyy3bdW6EEgAtqt'
        )
        self.assertEqual(
            Xpriv.from_seed(binascii.unhexlify(
                '4b381541583be4423346c643850da4b320e46a87ae3d2a4e6da11eba819cd4acba45d239319ac14f863b8d5ab5a0d0c64d2e8a1e7d1457df2e5a3c51c73235be'))
            .ckd_xpriv(0x80000000).xpub(),
            'xpub68NZiKmJWnxxS6aaHmn81bvJeTESw724CRDs6HbuccFQN9Ku14VQrADWgqbhhTHBaohPX4CjNLf9fq9MYo6oDaPPLPxSb7gwQN3ih19Zm4Y'
        )

    def test_btc_bip32_2(self):
        xpriv = "xprv9s21ZrQH143K2gCVXRarFj5npbgjtJ7MuNb15AoRYJ92ZMA1hcnoqpxJKfcsiMHP6cNmDKHCTphsC6uzzyzr2MwjXbDxg6U9ivvEupavYUb"
        paths = "m/7-8'/3/99'/38-39"
        keys = Xpriv.b58decode(xpriv).multi_ckd_xpriv(paths)
        for k, privkey in zip(keys, [
            '5ca736abd3b19632d11366c4dd79c227236500879980c6a1fc4e7c1e33933350',
            '8c793bce5319bf04349b5e4d21d091a98c1a1ad632bffc0425a5f4802c999a76',
            '692f2ddb1d5c7213d194643984642df6e9a5c8cd14a1a6b4054571955fcab05f',
            '8739db9026ceb50d7774ef145bd27e899228700f1096072fe9d26f8387378314',
        ]):
            self.assertEqual(k.key, binascii.unhexlify(privkey))

    def test_btc_bip39_test_vectors(self):
        self.assertEqual(
            Xpriv.from_mnemomic(
                'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
                'TREZOR').b58encode(),
            'xprv9s21ZrQH143K3h3fDYiay8mocZ3afhfULfb5GX8kCBdno77K4HiA15Tg23wpbeF1pLfs1c5SPmYHrEpTuuRhxMwvKDwqdKiGJS9XFKzUsAF'
        )
        self.assertEqual(
            Xpriv.from_mnemomic(
                'void come effort suffer camp survey warrior heavy shoot primary clutch crush open amazing screen patrol group space point ten exist slush involve unfold',
                'TREZOR').b58encode(),
            'xprv9s21ZrQH143K39rnQJknpH1WEPFJrzmAqqasiDcVrNuk926oizzJDDQkdiTvNPr2FYDYzWgiMiC63YmfPAa2oPyNB23r2g7d1yiK6WpqaQS'
        )

    def test_btc_key_recovery(self):
        pass


if __name__ == '__main__':
    parser = OptionParser(usage="%prog [options]", version="%prog 1.1")

    parser.add_option("--dump_bip32", nargs=2,
                      help="dump the keys from a xpriv and a path, usage: --dump_bip32 xprv9s21ZrQH143K m/0H/1-2/2H/2-4")

    parser.add_option("--bip32_format",
                      help="format of dumped bip32 keys")

    parser.add_option("--passphrase", dest="passphrase",
                      help="passphrase for the encrypted wallet")

    parser.add_option("--find_address",
                      help="find info about an address")

    parser.add_option("-d", "--dumpwallet", dest="dump", action="store_true",
                      help="dump wallet in json format")

    parser.add_option("--dumpformat", default="all",
                      help="choose what to extract in a wallet dump")

    parser.add_option("--dumpwithbalance", dest="dumpbalance", action="store_true",
                      help="includes balance of each address in the json dump, takes about 2 minutes per 100 addresses")

    parser.add_option("--importprivkey", dest="key",
                      help="import private key from vanitygen")

    parser.add_option("--importhex", dest="keyishex", action="store_true",
                      help="DEPRECATED, useless")

    parser.add_option("--datadir", dest="datadir",
                      help="REMOVED OPTION: put full path in the --wallet option")

    parser.add_option("-w", "--wallet", dest="walletfile",
                      help="wallet filename or directory (if directory is specified, will automatically find wallet.dat files)",
                      default="")

    parser.add_option("--label", dest="label",
                      help="label shown in the adress book (defaults to '')",
                      default="")

    parser.add_option("--testnet", dest="testnet", action="store_true",
                      help="use testnet subdirectory and address type")

    parser.add_option("--namecoin", dest="namecoin", action="store_true",
                      help="use namecoin address type")

    parser.add_option("--eth", dest="ethereum", action="store_true",
                      help="use ethereum address type")

    parser.add_option("--otherversion", dest="otherversion",
                      help="use other network address type, either P2PKH prefix only (e.g. 111) or full network info as 'name,p2pkh,p2sh,wif,segwithrp' (e.g. btc,0,0,0x80,bc)")

    parser.add_option("--info", dest="keyinfo", action="store_true",
                      help="display pubkey, privkey (both depending on the network) and hexkey")

    parser.add_option("--reserve", dest="reserve", action="store_true",
                      help="import as a reserve key, i.e. it won't show in the adress book")

    parser.add_option("--multidelete", dest="multidelete",
                      help="deletes data in your wallet, according to the file provided")

    parser.add_option("--balance", dest="key_balance",
                      help="prints balance of KEY_BALANCE")

    parser.add_option("--recover", dest="recover", action="store_true",
                      help="recover your deleted keys, use with recov_size and recov_device")

    parser.add_option("--recov_device", dest="recov_device",
                      help="device to read (e.g. /dev/sda1 or E: or a file), or directory (will automatically find wallet.dat files)")

    parser.add_option("--recov_size", dest="recov_size",
                      help="number of bytes to read (e.g. 20Mo, 50Gio, 20MB, 50GB, 1TB, 2TiB)")

    parser.add_option("--recov_outputdir", dest="recov_outputdir",
                      help="output directory where the recovered wallet will be put")

    parser.add_option("--output_keys", dest="output_keys",
                      help="output recovered keys to a text file (e.g., keys.txt) instead of creating a wallet (use with --recover)")

    parser.add_option("--recov_passphrase", dest="recov_passphrase",
                      help="passphrase for the recovered wallet (use with --recover and --recov_outputdir)")

    parser.add_option("--clone_watchonly_from", dest="clone_watchonly_from",
                      help="path of the original wallet")

    parser.add_option("--clone_watchonly_to", dest="clone_watchonly_to",
                      help="path of the resulting watch-only wallet")

    parser.add_option("--dont_check_walletversion", dest="dcv", action="store_true",
                      help="don't check if wallet version > %d before running (WARNING: this may break your wallet, be sure you know what you do)" % max_version)

    parser.add_option("--random_key", action="store_true",
                      help="print info of a randomly generated private key")

    parser.add_option("--whitepaper", action="store_true",
                      help="write the Bitcoin whitepaper using bitcoin-cli or blockchain.info")

    parser.add_option("--minimal_encrypted_copy", action="store_true",
                      help="write a copy of an encrypted wallet with only an empty address, *should* be safe to share when needing help bruteforcing the password")

    parser.add_option("--tests", action="store_true",
                      help="run tests")

    #	parser.add_option("--forcerun", dest="forcerun",
    #		action="store_true",
    #		help="run even if pywallet detects bitcoin is running")

    (options, args) = parser.parse_args()

    #	a=Popen("ps xa | grep ' bitcoin'", shell=True, bufsize=-1, stdout=PIPE).stdout
    #	aread=a.read()
    #	nl = aread.count("\n")
    #	a.close()
    #	if nl > 2:
    #		print('Bitcoin seems to be running: \n"%s"'%(aread))
    #		if options.forcerun is None:
    #			exit(0)

    if options.tests:
        unittest.main(argv=sys.argv[:1] + ['TestPywallet'])
        exit()

    if options.dump_bip32:
        print("Warning: single quotes (') may be parsed by your terminal, please use \"H\" for hardened keys")
        dump_bip32_privkeys(*options.dump_bip32, format=options.bip32_format)
        exit()

    if options.whitepaper:
        whitepaper()
        exit()

    if options.passphrase:
        passphrase = options.passphrase

    if not (options.clone_watchonly_from is None) and options.clone_watchonly_to:
        clone_wallet(options.clone_watchonly_from, options.clone_watchonly_to)
        exit(0)

    if options.recover:
        if options.recov_size is None or options.recov_device is None:
            print("You must provide the device and the number of bytes to read")
            exit(0)
        if options.recov_outputdir is None and options.output_keys is None:
            print(
                "You must provide either --recov_outputdir (for wallet creation) or --output_keys (for text file output)")
            exit(0)
        device = options.recov_device
        if len(device) in [2, 3] and device[1] == ':':
            device = "\\\\.\\" + device
            
        # Check if the device is a directory
        if os.path.isdir(device):
            # Search for wallet.dat files in the directory
            wallet_files = find_wallet_files(device)
            
            if not wallet_files:
                print("No wallet.dat files found in directory %s" % repr(os.path.realpath(device)))
                print("Continuing with recovery from the directory as a device...")
            else:
                if len(wallet_files) > 1:
                    print("Found multiple wallet.dat files:")
                    for i, wf in enumerate(wallet_files):
                        print(f"  [{i+1}] {wf}")
                    print("\nUsing the first wallet file found: %s" % wallet_files[0])
                
                device = wallet_files[0]
                print(f"Using wallet file: {device}")
                
        size = read_device_size(options.recov_size)

        # Get passphrases for decryption
        passes = []
        p = ' '
        print('\nEnter the possible passphrases used in your deleted wallets.')
        print("Don't forget that more passphrases = more time to test the possibilities.")
        print('Write one passphrase per line and end with an empty line.')
        while p != '':
            p = getpass.getpass("Possible passphrase: ")
            if p != '':
                passes.append(p)

        print("\nStarting recovery.")

        # Check if device is a wallet file (only if it's named wallet.dat)
        if os.path.isfile(device) and os.path.basename(device).lower() == 'wallet.dat':
            print("Detected wallet file. Attempting to extract keys directly from wallet...")
            try:
                # Try to read the wallet file directly
                recoveredKeys = extract_keys_from_wallet(device, passes)
                if not recoveredKeys:
                    print("No keys found in wallet file. Falling back to raw recovery...")
                    # Use current directory as temporary output dir for recovery process
                    temp_outputdir = options.recov_outputdir if options.recov_outputdir else "."
                    recoveredKeys = recov(device, passes, size, 10240, temp_outputdir)
            except Exception as e:
                print("Error reading wallet file: %s" % e)
                print("Falling back to raw recovery...")
                # Use current directory as temporary output dir for recovery process
                temp_outputdir = options.recov_outputdir if options.recov_outputdir else "."
                recoveredKeys = recov(device, passes, size, 10240, temp_outputdir)
        else:
            # Use current directory as temporary output dir for recovery process
            temp_outputdir = options.recov_outputdir if options.recov_outputdir else "."
            recoveredKeys = recov(device, passes, size, 10240, temp_outputdir)

        recoveredKeys = list(set(recoveredKeys))

        if options.output_keys:
            # Output keys to text file
            print("\n\nWriting recovered keys to file:")
            with open(options.output_keys, 'w') as f:
                f.write("# Recovered private keys\n")
                f.write("# Generated by pywallet recovery\n")
                f.write("# Format: one private key per line (hex format)\n")
                f.write("# Each key is provided in both uncompressed and compressed format\n")
                f.write("# Uncompressed keys are 64 hex characters\n")
                f.write("# Compressed keys are 66 hex characters (ending with '01')\n\n")

                total_keys_written = 0
                for i, sec in enumerate(recoveredKeys):
                    sec_hex = binascii.hexlify(sec)
                    if PY3:
                        sec_hex = sec_hex.decode('ascii')
                    print("Writing key %4d/%d" % (i + 1, len(recoveredKeys)))

                    # Write uncompressed version
                    f.write("%s\n" % sec_hex)
                    total_keys_written += 1

                    # Write compressed version
                    f.write("%s01\n" % sec_hex)
                    total_keys_written += 1

            print("\n\nRecovered %d unique key%s written to %s (%d total including compressed variants)" % (
                len(recoveredKeys), plural(len(recoveredKeys)), options.output_keys, total_keys_written))
        else:
            # Original wallet creation logic
            if len(recoveredKeys) == 0:
                print("\n\nNo keys were recovered. Skipping wallet creation.")
                print("If you expected to find keys, try:")
                print("- Using a larger --recov_size")
                print("- Providing passphrases for encrypted wallets")
                print("- Checking that the device/file path is correct")
            else:
                if options.recov_passphrase:
                    passphraseRecov = options.recov_passphrase
                    print("Using passphrase provided via --recov_passphrase option")
                else:
                    passphraseRecov = None
                    while not passphraseRecov:
                        passphraseRecov = getpass.getpass(
                            "Enter the passphrase for the wallet that will contain all the recovered keys%s: " % (
                                '' if passphraseRecov is None else " (can't be empty)"))
                passphrase = passphraseRecov

                # Ensure passphrase is in bytes format for cryptographic functions
                if isinstance(passphraseRecov, str):
                    passphraseRecov = passphraseRecov.encode('utf-8')

                db_env = create_env(options.recov_outputdir)
                recov_wallet_name = "recovered_wallet_%s.dat" % ts()

                create_new_wallet(db_env, recov_wallet_name, 32500)

                if passphraseRecov != "I don't want to put a password on the recovered wallet and I know what can be the consequences.":
                    db = open_wallet(db_env, recov_wallet_name, True)

                    NPP_salt = os.urandom(8)
                    NPP_rounds = int(50000 + random.random() * 20000)
                    NPP_method = 0
                    NPP_MK = os.urandom(32)
                    crypter.SetKeyFromPassphrase(passphraseRecov, NPP_salt, NPP_rounds, NPP_method)
                    NPP_EMK = crypter.Encrypt(NPP_MK)
                    update_wallet(db, 'mkey', {
                        "encrypted_key": NPP_EMK,
                        'nDerivationIterations': NPP_rounds,
                        'nDerivationMethod': NPP_method,
                        'nID': 1,
                        'otherParams': b'',
                        "salt": NPP_salt
                    })
                    db.close()

                read_wallet(json_db, db_env, recov_wallet_name, True, True, "", False)

                db = open_wallet(db_env, recov_wallet_name, True)

                print("\n\nImporting:")
                for i, sec in enumerate(recoveredKeys):
                    sec = binascii.hexlify(sec)
                    print("Importing key %4d/%d" % (i + 1, len(recoveredKeys)))
                    importprivkey(db, sec, "recovered: %s" % sec, None, False)
                    importprivkey(db, sec + '01', "recovered: %s" % sec, None, False)
                db.close()

                print("\n\nThe new wallet %s/%s contains the %d recovered key%s" % (options.recov_outputdir,
                                                                                    recov_wallet_name,
                                                                                    len(recoveredKeys),
                                                                                    plural(len(recoveredKeys))))

        exit(0)

    if 'bsddb' in missing_dep:
        print("pywallet needs 'bsddb' package to run, please install it")
        exit(0)

    if 'ecdsa' in missing_dep:
        print(
            "Warning: 'ecdsa' package is not installed, so you won't be able to sign/verify messages but everything else will work fine")

    if not (options.dcv is None):
        max_version = 10 ** 9

    if not (options.datadir is None):
        print("Depreacation")
        print("  The --datadir option has been deprecated, now the full path of the wallet file should go to --wallet")
        print(
            "  If you're not sure what to do, concatenating the old --datadir content, then a directory separator, then the old --wallet should do the trick")
        print("  If not, ask for help in the Pywallet thread: https://bitcointalk.org/index.php?topic=34028")

    db_dir = ""
    if options.walletfile:
        if options.datadir: options.walletfile = options.datadir + os.path.sep + options.walletfile
        
        # Check if the walletfile is actually a directory
        if os.path.isdir(options.walletfile):
            # Search for wallet.dat files in the directory
            wallet_files = find_wallet_files(options.walletfile)
            
            if not wallet_files:
                print("ERROR: No wallet.dat files found in directory %s" % repr(os.path.realpath(options.walletfile)))
                exit()
            
            if len(wallet_files) > 1:
                print("Found multiple wallet.dat files:")
                for i, wf in enumerate(wallet_files):
                    print(f"  [{i+1}] {wf}")
                print("\nUsing the first wallet file found: %s" % wallet_files[0])
            
            options.walletfile = wallet_files[0]
            print(f"Using wallet file: {options.walletfile}")
        
        # Check if the file exists
        if not os.path.isfile(options.walletfile):
            print("ERROR: wallet file %s can't be found" % repr(os.path.realpath(options.walletfile)))
            exit()
            
        db_dir, wallet_name = os.path.split(os.path.realpath(options.walletfile))

    if not (options.key_balance is None):
        print(balance(balance_site, options.key_balance))
        exit(0)

    network = network_bitcoin
    if not (options.otherversion is None):
        try:
            network = find_network(options.otherversion)
            if not network:
                network = Network('Unknown network', int(options.otherversion), None, None, None)
                print("Some network info is missing: please use the complete network format")
        except:
            network_info = options.otherversion.split(',')
            parse_int = lambda x: int(x, 16) if x.startswith('0x') else int(x)
            network = Network(network_info[0], parse_int(network_info[1]), parse_int(network_info[2]),
                              parse_int(network_info[3]), network_info[4])
    if options.namecoin:
        network = Network('Namecoin', 52, 13, 180, 'nc')
    elif options.testnet:
        db_dir += "/testnet3"
        network = network_bitcoin_testnet3
    elif options.ethereum:
        network = network_ethereum

    if not (options.keyinfo is None) or options.random_key:
        if not options.keyinfo:
            options.key = binascii.hexlify(os.urandom(32))
        keyinfo(options.key, network, True, False)
        print("")
        keyinfo(options.key, network, True, True)
        exit(0)

    if not db_dir:
        print("A mandatory option is missing\n")
        parser.print_help()
        exit()
    db_env = create_env(db_dir)

    if not (options.multidelete is None):
        filename = options.multidelete
        filin = open(filename, 'r')
        content = filin.read().split('\n')
        filin.close()
        typedel = content[0]
        kd = filter(bool, content[1:])
        try:
            r = delete_from_wallet(db_env, wallet_name, typedel, kd)
            print('%d element%s deleted' % (r, 's' * (int(r > 1))))
        except:
            print("Error: do not try to delete a non-existing transaction.")
            exit(1)
        exit(0)

    if options.minimal_encrypted_copy:
        db = open_wallet(db_env, wallet_name)
        minimal_wallet = wallet_name + '.minimal_for_decrypting.dat'
        assert not os.path.exists(
            os.path.join(db_dir, minimal_wallet)), "There is already a minimal encrypted copy at %s/%s, exiting" % (
            db_dir, minimal_wallet)
        kds = BCDataStream()
        vds = BCDataStream()
        encrypted_keys = []
        mkey = None
        for (key, value) in db.items():
            d = Bdict({})
            kds.clear();
            kds.write(key)
            vds.clear();
            vds.write(value)
            typ = kds.read_string()
            if typ == b'mkey':
                mkey = (key, value)
            if typ != b'ckey': continue
            d['public_key'] = kds.read_bytes(kds.read_compact_size())
            d['__key__'] = key
            d['__value__'] = value
            encrypted_keys.append(d)
        db.close()
        print('''
	Before creating a safe partial wallet you need to check the balance of the following addresses.
	You may check the balance on your wallet or using an online block explorer.
	Just hit Enter if the address is empty and write 'no' if not empty.

			''')
        for pbk in encrypted_keys[::-1]:
            p2pkh, p2wpkh, witaddr, _ = pubkey_info(pbk['public_key'], network)
            for addr in [p2pkh, p2wpkh, witaddr]:
                has_balance = raw_input(addr + ': ') != ''
                if has_balance:
                    print('')
                    break
            if not has_balance:
                if raw_input(
                        "\nAre you REALLY sure the 3 addresses above have an empty balance? (type 'YES') ") == 'YES':
                    output_db = open_wallet(db_env, minimal_wallet, True)
                    output_db.put(*mkey)
                    output_db.put(pbk['__key__'], pbk['__value__'])
                    output_db.close()
                    print('\nMinimal wallet written at %s' % minimal_wallet)
                    exit()
                else:
                    print('\nYou need to input zero character only when the balance is empty, exiting')
                    exit()
        print("\nError: all your addresses seem to be used, pywallet can't create a safe minimal wallet to share")
        exit()

    read_wallet(json_db, db_env, wallet_name, True, True, "", not (options.dumpbalance is None))

    if json_db.get('minversion', 99999999) > max_version:
        print("Version mismatch (must be <= %d)" % max_version)
    # exit(1)

    if options.find_address:
        addr_data = filter(lambda x: x["addr"] == options.find_address, json_db["keys"] + json_db["pool"])
        print(json.dumps(list(addr_data), sort_keys=True, indent=4))
        exit()

    if options.dump:
        if options.dumpformat == 'addr':
            addrs = list(map(lambda x: x["addr"], json_db["keys"] + json_db["pool"]))
            json_db = addrs
        wallet = json.dumps(json_db, sort_keys=True, indent=4)
        print(wallet)
        exit()
    elif options.key:
        if json_db['version'] > max_version:
            print("Version mismatch (must be <= %d)" % max_version)
        elif options.key in private_keys or options.key in private_hex_keys:
            print("Already exists")
        else:
            db = open_wallet(db_env, wallet_name, writable=True)

            if importprivkey(db, options.key, options.label, options.reserve):
                print("Imported successfully")
            else:
                print("Bad private key")

            db.close()
        exit()





