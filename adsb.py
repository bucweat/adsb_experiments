__author__ = 'Oliver Maskery'


import subprocess
import signal
import json
import pika


class Receiver(object):
    def __init__(self, callback, exit_callback):
        self._callback = callback
        self._exit_callback = exit_callback

        self._process = subprocess.Popen(
            ['rtl_adsb'], stdout=subprocess.PIPE, stderr=open('/dev/null', 'w')
        )

    def run(self):
        while self._process.poll() is None:
            received = self._process.stdout.readline().decode()
            if -1 in (received.find("*"), received.find(";")):
                message = None
            else:
                message = received.strip()

                if self._exit_callback():
                    self.terminate()
            self._callback(message)

    def terminate(self):
        self._process.send_signal(signal.SIGINT)


class Client(object):
    def __init__(self):
        self._received_sigint = False
        self._rx_exchange_name = None
        self._tx_exchange_name = None
        self._tx_channel = None
        self._rx_channel = None
        self._rx_queue_name = None

        self._connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'
        ))

    def should_exit(self):
        return self._received_sigint

    def enable_tx_channel(self, tx_exchange_name, exchange_type):
        self._tx_exchange_name = tx_exchange_name
        self._tx_channel = self._connection.channel()
        self._tx_channel.exchange_declare(
            exchange=self._tx_exchange_name, exchange_type=exchange_type
        )

    def enable_rx_channel(self, rx_exchange_name, exchange_type):
        self._rx_exchange_name = rx_exchange_name
        self._rx_channel = self._connection.channel()
        self._rx_channel.exchange_declare(
            exchange=self._rx_exchange_name, exchange_type=exchange_type
        )
        result = self._rx_channel.queue_declare(exclusive=True)
        self._rx_queue_name = result.method.queue
        self._rx_channel.queue_bind(
            exchange=self._rx_exchange_name,
            queue=self._rx_queue_name
        )

        self._rx_channel.basic_consume(
            self.on_receive_message,
            queue=self._rx_queue_name,
            no_ack=True
        )

    def on_receive_message(self, channel, method, properties, body):
        _ = self, channel, method, properties, body
        pass

    def handle_sigint(self, signum, frame):
        _ = signum, frame
        self._received_sigint = True

    def consume(self):
        while not self._received_sigint:
            try:
                self._rx_channel.start_consuming()
            except Exception, ex:
                if not self._received_sigint:
                    raise

    def send_blob(self, message):
        blob = json.dumps(message)
        self._tx_channel.basic_publish(
            exchange=self._tx_exchange_name,
            routing_key='',
            body=blob
        )


class Message(object):
    def __init__(self, df, ca, icao):
        self.df = df
        self.ca = ca
        self.icao = icao

    def to_json(self):
        return {
            'df': self.df,
            'ca': self.ca,
            'icao': self.icao,
        }

    @staticmethod
    def from_json(blob_str):
        blob = json.loads(blob_str)

        df = blob['df']
        ca = blob['ca']
        icao = blob['icao']

        return Message(
            df, ca, icao
        )

    @staticmethod
    def from_encoded(encoded):
        start = encoded.find("*")
        end = encoded.find(";")
        if -1 in (start, end):
            return None

        byte_string = encoded[start+1:end]
        byte_values = [int(byte_string[i:i+2], 16) for i in range(0, len(byte_string), 2)]
        bit_string = "".join([bin(value)[2:] for value in byte_values])

        def bits(offset, length):
            return int(bit_string[offset:offset+length], 2)

        def bytes(offset, length):
            return int(bit_string[offset*8:(offset*8)+(length*8)], 2)

        df = bits(0, 5)
        ca = bits(6, 3)
        icao = bytes(1, 3)

        return Message(df, ca, icao)
