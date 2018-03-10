
import os
from logzero import logger
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from twisted.internet import reactor, task
from neo.Prompt.Commands.Invoke import TestInvokeContract, test_invoke
from neocore.Fixed8 import Fixed8
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Network.NodeLeader import NodeLeader


class BContract(object):

    def __init__(self, contract_hash, wallet_file_path, wallet_password):
        logger.info("Initializes a BContract Instance")
        self.contract_hash = contract_hash
        if not os.path.exists(wallet_file_path):
            logger.error("Wallet file not found.")
            raise RuntimeError('Wallet File Not found')

        password_key = to_aes_key(wallet_password)

        try:
            self.Wallet = UserWallet.Open(wallet_file_path, password_key)

            self._walletdb_loop = task.LoopingCall(self.Wallet.ProcessBlocks)
            self._walletdb_loop.start(1)
            logger.info("Opened wallet at %s" % wallet_file_path)
        except Exception as e:
            logger.error("Could not open wallet: %s" % e)
            raise RuntimeError("Could not open wallet: %s" % e)

    def invoke_contract(self, command, args):
        logger.info("Invoking a smart contract")

        if not self.wallet.IsSynced:
            logger.error("Node is still catching up with blockchain.")
            raise RuntimeError('Node is still catching up with blockchain.')

        params = [self.contract_hash, command,args]

        tx, fee, results, num_ops = TestInvokeContract(self.Wallet, params,parse_params=False)

        if tx is not None and results is not None:
            result = InvokeContract(self.Wallet, tx, fee)
            return result
        else:
            logger.error("Invoking a smart contract went wrong")
            raise RuntimeError('Something went wrong during TestInvoke')

    def create(self,partnership):
        args = [partnership.currency,partnership.flatfees_partners,partnership.percentage_partners,partnership.webpage]
        return self.invoke_contract("create",args)

    def info(self,address):
        return self.invoke_contract("info",[address])

    def update(self,address, property, new_value):
        cmd = "set_flatfees"
        if property == "webpage":
            cmd = "set_webpage"
        elif property == "set_partnership":
            cmd = "set_partnership"
        return self.invoke_contract(cmd, [address,new_value])

    def delete(self,address):
        return self.invoke_contract("delete", [address])

    def transfer(self,from_address,to_address):
        return self.invoke_contract("transfer", [from_address,to_address])


def InvokeContract(wallet, tx, fee=Fixed8.Zero()):

    wallet_tx = wallet.MakeTransaction(tx=tx, fee=fee, use_standard=True)

#    pdb.set_trace()

    if wallet_tx:

        context = ContractParametersContext(wallet_tx)

        wallet.Sign(context)

        if context.Completed:

            wallet_tx.scripts = context.GetScripts()

            relayed = False

#            print("SENDING TX: %s " % json.dumps(wallet_tx.ToJson(), indent=4))

            relayed = NodeLeader.Instance().Relay(wallet_tx)

            if relayed:
                logger.info("Relayed Tx: %s " % wallet_tx.Hash.ToString())

                wallet.SaveTransaction(wallet_tx)

                return wallet_tx
            else:
                logger.error("Could not relay tx %s " % wallet_tx.Hash.ToString())
                raise RuntimeError("Could not relay tx %s " % wallet_tx.Hash.ToString())
        else:
            logger.error("Incomplete signature")
            raise RuntimeError('Incomplete signature')

    else:
        logger.error("Insufficient funds")
        raise RuntimeError('Insufficient funds')

    return False