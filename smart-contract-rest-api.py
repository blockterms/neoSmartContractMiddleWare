"""
Example of running a NEO node, receiving smart contract notifications and
integrating a simple REST API.

Smart contract events include Runtime.Notify, Runtime.Log, Storage.*,
Execution.Success and several more. See the documentation here:
http://neo-python.readthedocs.io/en/latest/smartcontracts.html

This example requires the environment variable NEO_REST_API_TOKEN, and can
optionally use NEO_REST_LOGFILE and NEO_REST_API_PORT.

Example usage (with "123" as valid API token):

    NEO_REST_API_TOKEN="123" python examples/smart-contract-rest-api.py

Example API calls:

    $ curl localhost:8080
    $ curl -H "Authorization: Bearer 123" localhost:8080/echo/hello123
    $ curl -X POST -H "Authorization: Bearer 123" -d '{ "hello": "world" }' localhost:8080/echo-post

The REST API is using the Python package 'klein', which makes it possible to
create HTTP routes and handlers with Twisted in a similar style to Flask:
https://github.com/twisted/klein
"""

import sys
sys.path.append('../neo-python')

import os
import threading
import argparse
import json
from time import sleep

from logzero import logger
from twisted.internet import reactor, task, endpoints
from twisted.web.server import Request, Site
from klein import Klein, resource
from neo.api.JSONRPC.JsonRpcApi import JsonRpcApi
from neo.Network.NodeLeader import NodeLeader
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Settings import settings

from neo.Network.api.decorators import json_response, gen_authenticated_decorator, catch_exceptions
from neo.contrib.smartcontract import SmartContract
from blockterms.Partnership import Partnership
from blockterms.BContract import BContract
from neocore.UInt256 import UInt256


# Default REST API port is 8080, and can be overwritten with an env var:
API_PORT = os.getenv("NEO_REST_API_PORT", 8081)

# If you want to enable logging to a file, set the filename here:
LOGFILE = "./smartcontractapilogs.log"

# Internal: if LOGFILE is set, file logging will be setup with max
# 100 MB per file and 30 rotations:
if LOGFILE:
    settings.set_logfile(LOGFILE, max_bytes=1e8, backup_count=30)

# Set the PID file
PID_FILE = "/tmp/neopython-api-server.pid"


def write_pid_file():
    """ Write a pid file, to easily kill the service """
    f = open(PID_FILE, "w")
    f.write(str(os.getpid()))
    f.close()


# Internal: get the API token from an environment variable
API_AUTH_TOKEN = os.getenv("NEO_REST_API_TOKEN", None)
if not API_AUTH_TOKEN:
    raise Exception("No NEO_REST_API_TOKEN environment variable found!")

# Set the hash of your contract here:
SMART_CONTRACT_HASH = "0x1185f3c0dde8136966b30bed835b78917a78fd96"
WALLET_FILE_PATH = "../wallets/new_first"
WALLET_PASSWORD = "1234567890"

# Internal: setup the smart contract instance
smart_contract = SmartContract(SMART_CONTRACT_HASH)

# Internal: setup the klein instance
app = Klein()

# Internal: generate the @authenticated decorator with valid tokens
authenticated = gen_authenticated_decorator(API_AUTH_TOKEN)

bcontract = BContract(SMART_CONTRACT_HASH, WALLET_FILE_PATH, WALLET_PASSWORD)


# Smart contract event handler for Runtime.Notify events
#
@smart_contract.on_notify
def sc_notify(event):
    logger.info("SmartContract Runtime.Notify event: %s", event)

    # Make sure that the event payload list has at least one element.
    if not len(event.event_payload):
        return

    # The event payload list has at least one element. As developer of the smart contract
    # you should know what data-type is in the bytes, and how to decode it. In this example,
    # it's just a string, so we decode it with utf-8:
    logger.info("- payload part 1: %s", event.event_payload[0].decode("utf-8"))


#
# Custom code that runs in the background
#
def custom_background_code():
    """ Custom code run in a background thread. Prints the current block height.

    This function is run in a daemonized thread, which means it can be instantly killed at any
    moment, whenever the main thread quits. If you need more safety, don't use a  daemonized
    thread and handle exiting this thread in another way (eg. with signals and events).
    """
    while True:
        logger.info("Block %s / %s", str(Blockchain.Default().Height), str(Blockchain.Default().HeaderHeight))
        sleep(15)


#
# REST API Routes
#
@app.route('/')
def home(request):
    logger.info("GET /")
    return "REST API to interact with smart contract"


@app.route('/partnership/<adr>')
@catch_exceptions
@authenticated
@json_response
def partnership(request, adr):
    #
    # this API returns the partnership information
    # for the given address
    #
    res = {}
    try:
        res["tx"] = bcontract.info(adr)
    except Exception as e:
        res["error"] = True
        res["message"] = e
    return res


@app.route('/transaction/<tx>')
@catch_exceptions
@authenticated
@json_response
def transaction(request, tx):
    #
    # this API returns the details of transaction
    # for the given address
    #
    res = {}
    try:
        txid = UInt256.ParseString(tx)
        tx, height = Blockchain.Default().GetTransaction(txid)
        if height > -1:
            res = tx.ToJson()
            res['height'] = height
            res['unspents'] = [uns.ToJson(tx.outputs.index(uns)) for uns in
                               Blockchain.Default().GetAllUnspent(txid)]
            # tokens = [(Token.Command, json.dumps(jsn, indent=4))]
            # print_tokens(tokens, self.token_style)
            # print('\n')
    except Exception as e:
        res["error"] = True
        res["message"] = e
        logger.error("Could not find transaction from tx: %s (%s)" % (e, tx))
    return res


@app.route('/partnership', methods=['POST'])
@catch_exceptions
@authenticated
@json_response
def create_partnership(request):
    # Parse POST JSON body
    body = json.loads(request.content.read().decode("utf-8"))
    p = Partnership(body["address"],body["currency"],body["flatfees_partners"],body["percentage_partners"],body["webpage"])
    res = {}
    try:
        tx = bcontract.create(p)
        res["tx"] = tx
    except Exception as e:
        res["error"] = True
        res["message"] = e
    return res

#
# Main method which starts everything up
#


def main():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-m", "--mainnet", action="store_true", default=False,
                       help="Use MainNet instead of the default TestNet")
    group.add_argument("-t", "--testnet", action="store_true", default=False,
                       help="Use TestNet instead of the default TestNet")
    group.add_argument("-p", "--privnet", action="store_true", default=False,
                       help="Use PrivNet instead of the default TestNet")
    group.add_argument("--coznet", action="store_true", default=False,
                       help="Use the CoZ network instead of the default TestNet")
    group.add_argument("-c", "--config", action="store", help="Use a specific config file")

    parser.add_argument("--port-rpc", type=int, help="port to use for the json-rpc api (eg. 10332)")
    parser.add_argument("--port-rest", type=int, help="port to use for the rest api (eg. 80)")

    args = parser.parse_args()

    if not args.port_rpc and not args.port_rest:
        print("Error: specify at least one of --port-rpc / --port-rest")
        parser.print_help()
        return

    if args.port_rpc == args.port_rest:
        print("Error: --port-rpc and --port-rest cannot be the same")
        parser.print_help()
        return

    # Setup depending on command line arguments. By default, the testnet settings are already loaded.
    if args.config:
        settings.setup(args.config)
    elif args.mainnet:
        settings.setup_mainnet()
    elif args.testnet:
        settings.setup_testnet()
    elif args.privnet:
        settings.setup_privnet()
    elif args.coznet:
        settings.setup_coznet()

    # Write a PID file to easily quit the service
    write_pid_file()

    # Setup the blockchain
    blockchain = LevelDBBlockchain(settings.LEVELDB_PATH)
    Blockchain.RegisterBlockchain(blockchain)
    dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
    dbloop.start(.1)

    NodeLeader.Instance().Start()

    # Disable smart contract events for external smart contracts
    settings.set_log_smart_contract_events(False)

    # Open a wallet otherwise exit.
    try:
        bcontract.start_db_loop()
    except Exception as e:
        logger.error("Error starting the custom neo node. wallet file and correct password are necessary %s" %e)
        exit(1)

    #
    # Start a thread with custom code
    #
    d = threading.Thread(target=custom_background_code)
    d.setDaemon(True)  # daemonizing the thread will kill it when the main thread is quit
    d.start()

    host = "0.0.0.0"

    if args.port_rpc:
        logger.info("Starting json-rpc api server on http://%s:%s" % (host, args.port_rpc))
        api_server_rpc = JsonRpcApi(args.port_rpc)
        endpoint_rpc = "tcp:port={0}:interface={1}".format(args.port_rpc, host)
        endpoints.serverFromString(reactor, endpoint_rpc).listen(Site(api_server_rpc.app.resource()))

    if args.port_rest:
        logger.info("Starting smartcontract api server on http://%s:%s" % (host, args.port_rest))
        endpoint_description = "tcp:port={0}:interface={1}".format(args.port_rest, host)
        endpoint = endpoints.serverFromString(reactor, endpoint_description)
        endpoint.listen(Site(app.resource()))

    # app.run(host, 9999)
    # Run all the things (blocking call)
    logger.info("Everything is setup and running. Waiting for events...")
    reactor.run()
    logger.info("Shutting down.")


if __name__ == "__main__":
    main()
