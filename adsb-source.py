#!/usr/bin/env python2


__author__ = 'Oliver Maskery'


import datetime
import argparse
import logging
import signal
import adsb


def main():
    logging.basicConfig()

    args = get_args()
    client = adsb.Client()

    def on_data_receive(data):
        if data is not None:
            print "data:", data
            if args.log is not None:
                timestamp = datetime.datetime.now()
                args.log.write("{} {}\n".format(
                    timestamp, data
                ))
            client.send_blob(data)

    receiver = adsb.Receiver(on_data_receive, client.should_exit)
    client.enable_tx_channel('adsb_raw', 'fanout')

    signal.signal(signal.SIGINT, client.handle_sigint)
    receiver.run()

    print("exiting")


def get_args():
    parser = argparse.ArgumentParser(
        description='utility for capturing ADSB data from rtl_adsb and broadcasting to RabbitMQ'
    )
    parser.add_argument(
        '-l', '--log', type=argparse.FileType('a'),
        help='log file to record all received ADSB messages to'
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
