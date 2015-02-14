#!/usr/bin/env python2


__author__ = 'Oliver Maskery'


import datetime
import logging
import signal
import adsb


def main():
    logging.basicConfig()

    client = RecentlySeen()
    client.enable_rx_channel('adsb_decoded', 'fanout')
    signal.signal(signal.SIGINT, client.handle_sigint)
    client.consume()

    print("exiting")


class PlaneSeen(object):
    def __init__(self, icao):
        self._icao = icao
        self._last_seen = datetime.datetime.now()
        self._count = 1
        self._count_this_track = 1
        self._interest_period = datetime.timedelta(seconds=5)
        self._first_seen = self._last_seen
        self._forget_period = datetime.timedelta(minutes=2)

    def icao(self):
        return self._icao

    def count(self):
        return self._count

    def count_this_track(self):
        return self._count_this_track

    def first_seen(self):
        return self._first_seen

    def seen(self):
        self._count += 1
        timestamp = datetime.datetime.now()
        if self.time_since_seen() >= self._forget_period:
            self._first_seen = timestamp
            self._count_this_track = 1
        else:
            self._count_this_track += 1
        self._last_seen = timestamp

    def time_since_seen(self):
        return datetime.datetime.now() - self._last_seen

    def tracking_since(self):
        return datetime.datetime.now() - self._first_seen

    def is_interesting(self):
        return self.time_since_seen() < self._interest_period


class RecentlySeen(adsb.Client):
    def __init__(self):
        adsb.Client.__init__(self)
        self._seen = {}
        self._update_period = datetime.timedelta(seconds=5)
        self._next_update = datetime.datetime.now()
        self._ignored = 0
        self._total = 0

    def handle_received(self, message):
        decoded = adsb.Message.from_json(message)
        self._total += 1

        if decoded.df in (17, 18):
            if decoded.icao not in self._seen.keys():
                self._seen[decoded.icao] = PlaneSeen(decoded.icao)
            else:
                self._seen[decoded.icao].seen()
        else:
            self._ignored += 1

        if datetime.datetime.now() >= self._next_update:
            self._next_update = datetime.datetime.now() + self._update_period
            interest = False
            for seen in sorted(self._seen.values(), key=lambda x: x.icao()):
                if seen.is_interesting():
                    if not interest:
                        print "\n" * 100
                        print "seen {} (ign: {}/{}):".format(datetime.datetime.now(), self._ignored, self._total)
                        interest = True
                    print "  {:06X}: count={} ({}) {}s ago ({}s, since: {})".format(
                        seen.icao(),
                        seen.count_this_track(),
                        seen.count(),
                        round(seen.time_since_seen().total_seconds(), 2),
                        round(seen.tracking_since().total_seconds(), 2),
                        seen.first_seen().strftime('%d/%m/%Y %H:%M:%S')
                    )
            self._ignored = 0
            self._total = 0


if __name__ == "__main__":
    main()
