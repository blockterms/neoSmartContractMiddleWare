#!/usr/bin/env python3


import sys
sys.path.append('../neo-python')

from neorpc.Client import RPCClient
from neorpc.Settings import SettingsHolder


def main():
    s = SettingsHolder()
    s.setup(["http://localhost:8082"])
    client = RPCClient(config=s)
    blockchain_height = client.get_height()
    print("blockchain height %s" % blockchain_height)


if __name__ == "__main__":
    main()