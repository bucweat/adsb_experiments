#!/usr/bin/env python2


__author__ = 'Oliver Maskery'


import logging
import signal
import adsb


def main():
    logging.basicConfig()

    client = adsb.Client()

    def on_data_receive(data):
        if data is not None:
            print "data:", data
            client.send_blob(data)

    receiver = adsb.Receiver(on_data_receive, client.should_exit)
    client.enable_tx_channel('adsb_raw', 'fanout')

    signal.signal(signal.SIGINT, client.handle_sigint)
    receiver.run()

    print("exiting")


if __name__ == "__main__":
    main()
