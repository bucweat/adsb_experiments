#!/usr/bin/env python2


__author__ = 'Oliver Maskery'


import argparse
import datetime
import logging
import signal
import adsb


def main():
    logging.basicConfig()

    args = get_args()

    client = Targeted(args.targets)
    client.enable_rx_channel('adsb_decoded', 'fanout')
    signal.signal(signal.SIGINT, client.handle_sigint)
    client.consume()

    print("exiting")


def get_args():
    parser = argparse.ArgumentParser(
        description='tool to display ADSB data from specific planes identified by ICAO'
    )
    parser.add_argument(
        'targets', nargs='+', help='target ICAO numbers (in hex) to track'
    )
    return parser.parse_args()


class Targeted(adsb.Client):
    def __init__(self, targets):
        adsb.Client.__init__(self)
        self._targets = [
            int(target, 16)
            for target in targets
        ]

    def handle_received(self, message):
        decoded = adsb.Message.from_json(message)

        if decoded.icao in self._targets:
            timestamp = datetime.datetime.now().strftime(
                '%d/%m/%Y %H:%M:%S'
            )
            print "[{}] icao {:06X} -> {}".format(
                timestamp, decoded.icao, decoded.raw
            )


if __name__ == "__main__":
    main()
