"""
blockterms partnership smart contract interface
======================================
Author: Anil Kumar
Email: yak@fastmail.com
Date: Dec 22 2018
"""


class Partnership(object):

    def __init__(self, address, currency, flatfees_partners, percentage_partners, webpage=""):
        print("Initializes a partnership")
        self.address = address
        self.currency = currency

        if len(flatfees_partners) == 0:
            self.flatfees_partners = "none"
        else:
            self.flatfees_partners = flatfees_partners

        if len(percentage_partners) == 0:
            self.percentage_partners = "none"
        else:
            self.percentage_partners = percentage_partners

        self.webpage = webpage

