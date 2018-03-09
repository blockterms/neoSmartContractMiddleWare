<p align="center">
  <img
    src="https://blockterms.com/blockterms.png"
    width="225px;">
</p>

## Python interface to call smartcontracts

Note: This is a work in progress.

##setup

Check out this project in the same folder as neo-python

Wallet dependency in neo-python is not ideal to have a generic invokeContract API.

The api I would like to achieve looks as follows.

invokeContract(contracthash, account_public_key, account_privatekey, command, args)


#
# References:
#

https://github.com/imusify/blockchain-middleware