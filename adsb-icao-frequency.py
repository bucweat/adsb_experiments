#!/usr/bin/env python2


__author__ = 'Oliver Maskery'


import datetime
import logging
import signal
import adsb


class PlaneSeen(object):
    def __init__(self, icao):
        self._icao = icao
        self._last_seen = datetime.datetime.now()
        self._count = 1
        self._interest_period = datetime.timedelta(seconds=30)

    def icao(self):
        return self._icao

    def count(self):
        return self._count

    def seen(self):
        self._count += 1
        self._last_seen = datetime.datetime.now()

    def time_since_seen(self):
        return datetime.datetime.now() - self._last_seen

    def is_interesting(self):
        return self.time_since_seen() < self._interest_period


class RecentlySeen(adsb.Client):
    def __init__(self):
        adsb.Client.__init__(self)
        self._seen = {}
        self._ignored = 0

    def handle_received(self, message):
        decoded = adsb.Message.from_json(message)

        if (decoded.df, decoded.ca) == (17, 5):
            if decoded.icao not in self._seen.keys():
                self._seen[decoded.icao] = PlaneSeen(decoded.icao)
            else:
                self._seen[decoded.icao].seen()

            interest = False
            for seen in self._seen.values():
                if seen.is_interesting():
                    if not interest:
                        print "seen {} (ignored {} messages):".format(datetime.datetime.now(), self._ignored)
                        interest = True
                    print "  {:X}: count={} ({} seconds ago)".format(
                        seen.icao(),
                        seen.count(),
                        round(seen.time_since_seen().total_seconds(), 2)
                    )

            self._ignored = 0
        else:
            self._ignored += 1


def main():
    logging.basicConfig()
    client = RecentlySeen()
    client.enable_rx_channel('adsb_decoded', 'fanout')
    signal.signal(signal.SIGINT, client.handle_sigint)
    client.consume()
    print("exiting")


if __name__ == "__main__":
    main()
