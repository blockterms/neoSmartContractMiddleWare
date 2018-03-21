#!/usr/bin/env python3


import sys
sys.path.append('../neo-python')

from neorpc.Client import RPCClient
from neorpc.Settings import SettingsHolder


def main():
    s = SettingsHolder()
    s.setup(["http://0.0.0.0:8082"])
    client = RPCClient(config=s)
    # blockchain_block = client.get_block(1274378)
    # print(blockchain_block)
    to = client.get_transaction("5c614786554f19a3fe04fbf7473f3dda5d89f8b1fcad9ef19c2e1fff3466589d")
    print(to)


if __name__ == "__main__":
    main()