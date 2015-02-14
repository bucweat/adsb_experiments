#!/usr/bin/env python2


__author__ = 'Oliver Maskery'


import logging
import signal
import adsb
import json


class DecodeRawAdsb(adsb.Client):
    def __init__(self):
        adsb.Client.__init__(self)

    def on_receive_message(self, channel, method, properties, body):
        _ = channel, method, properties

        try:
            raw_message = json.loads(body)

            decoded = adsb.Message.from_encoded(raw_message)

            print("DF: {} CA: {} ICAO: {:x}".format(
                decoded.df, decoded.ca, decoded.icao
            ))

            self.send_blob(decoded.to_json())
        except Exception, ex:
            print("exception occurred: {}".format(ex))


def main():
    logging.basicConfig()
    client = DecodeRawAdsb()
    client.enable_rx_channel('adsb_raw', 'fanout')
    client.enable_tx_channel('adsb_decoded', 'fanout')
    signal.signal(signal.SIGINT, client.handle_sigint)
    client.consume()
    print("exiting")


if __name__ == "__main__":
    main()
