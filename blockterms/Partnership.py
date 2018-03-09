"""
blockterms partnership smart contract interface
======================================
Author: Anil Kumar
Email: yak@fastmail.com
Date: Dec 22 2018
"""

from neo.Blockchain import GetBlockchain
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.VM.OpCode import *
from neo.Prompt.Commands.Invoke import DEFAULT_MIN_FEE
from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage


SMART_CONTRACT_HASH = "0x1185f3c0dde8136966b30bed835b78917a78fd96"


class Partnership(object):

    def __init__(self, address):
        print("Initializes a partnership")
        self.address = address

    @staticmethod
    def create(info):
        print("this creates a new partnership")
        return True

    @staticmethod
    def invoke_contract(command, args):
        bc = GetBlockchain()
        contract = bc.GetContract(SMART_CONTRACT_HASH)
        sb = ScriptBuilder()

        argsHex = []
        for arg in args:
            argsHex.append(binascii.hexlify(arg.encode('utf-8')))

        argsHex.reverse()
        argsLength = len(argsHex)
        for ah in argsHex:
            sb.push(ah)
        sb.push(argsLength)
        sb.Emit(PACK)
        commandHex = binascii.hexlify(command.encode('utf-8'))
        sb.push(commandHex)
        sb.EmitAppCall(contract.Code.ScriptHash().Data)
        script = sb.ToArray()
        outputs = []

        # After this a new call is being made to test_invoke
        tx = InvocationTransaction()
        tx.outputs = outputs
        tx.inputs = []
        tx.Version = 1
        tx.scripts = []
        tx.Script = binascii.unhexlify(script)





    def info(self):
        print("method calls the smart contract to get the information for given address %s" % self.address)

        ##
        #1. Take the input parameters convert them to hex and push them to script builder
        ##
        params = [["addr1"],'info']



        sb.push([self.address])
        sb.push("info")

        sb.EmitAppCall(contract.Code.ScriptHash().Data)
        script = sb.ToArray()
        minfee = DEFAULT_MIN_FEE

        sn = bc._db.snapshot()

        tx = InvocationTransaction()
        tx.outputs = []
        tx.inputs = []
        tx.Version = 1
        tx.scripts = []
        tx.Script = binascii.unhexlify(script)
        tx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script,
                                              data=Crypto.ToScriptHash(contract.Script, unhex=False).Data)]
        #
        # 1. Calculate tx and fee
        #
        return {
            "address" : self.address
        }

    def update(self):
        print("method updates the smartcontract with address %s" % self.address)

    def delete(self):
        print("method deletes the smartcontract with address %s" % self.address)