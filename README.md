<p align="center">
  <img
    src="https://blockterms.com/blockterms.png"
    width="225px;">
</p>

## Python interface to call smartcontracts

Note: this is still work in progress.

REST API is useful when invoking private functions of a smart contract that can be invoked only by the contract owner.
For all other usecases, the rpcserver-client is much simpler interface.

How to run an rpc server
https://gist.github.com/metachris/2be27cdff9503ebe7db1c27bfc60e435

How to use rpc client
https://github.com/CityOfZion/neo-python-rpc

##Setup

Check out this project in the same folder as neo-python

make sure you have python 3.6 environment

For the REST api set correct smartcontracthash, wallet_file_path and wallet_password 

Copy the Chains folder from neo-python or ~/.neopython to current folder

Start the python server using

NEO_REST_API_TOKEN="123" python smart-contract-rest-api.py -t --port-rpc 8082 --port-rest 8081

This starts both REST api and json RPC server.

#
# Guidelines for writing a smartcontract api client
#
Please note that invoking smartcontract api repeatedly wont work, you need to have some sort of queue on the client side and if
invoking fails, try again.

With the current implementation of this project, you are limited to having one smartcontract invoke per block. 

#
# References:
#

https://github.com/imusify/blockchain-middleware
https://gist.github.com/metachris/2be27cdff9503ebe7db1c27bfc60e435
https://github.com/CityOfZion/neo-python-rpc

