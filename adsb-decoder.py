#!/usr/bin/env python2


__author__ = 'Oliver Maskery'


import logging
import signal
import adsb
import json


class AdsbDecoderClient(adsb.Client):
    def __init__(self):
        adsb.Client.__init__(self)

    def handle_received(self, message):
        raw_message = json.loads(message)

        decoded = adsb.Message.from_encoded(raw_message)

        print("DF: {} CA: {} ICAO: {:x}".format(
            decoded.df, decoded.ca, decoded.icao
        ))

        self.send_blob(decoded.to_json())


def main():
    logging.basicConfig()
    client = AdsbDecoderClient()
    client.enable_tx_channel('adsb_decoded', 'fanout')
    client.enable_rx_channel('adsb_raw', 'fanout')
    signal.signal(signal.SIGINT, client.handle_sigint)
    client.consume_in_worker()
    print("exiting")


if __name__ == "__main__":
    main()
