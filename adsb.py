__author__ = 'Oliver Maskery'


import subprocess
import threading
import signal
import json
import pika


class Receiver(object):
    def __init__(self, callback, exit_callback):
        self._callback = callback
        self._exit_callback = exit_callback

        self._process = subprocess.Popen(
            ['rtl_adsb', '-Q', '2', '-S', '-e', '0'], stdout=subprocess.PIPE, stderr=open('/dev/null', 'w')
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

        self._tx_connection = None
        self._rx_connection = None
        self._rx_exchange_name = None
        self._tx_exchange_name = None
        self._tx_channel = None
        self._rx_channel = None
        self._rx_queue_name = None
        self._received = None
        self._rx_consumer_tag = None

    def should_exit(self):
        return self._received_sigint

    def enable_tx_channel(self, tx_exchange_name, exchange_type):
        self._tx_connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'
        ))
        self._tx_exchange_name = tx_exchange_name
        self._tx_channel = self._tx_connection.channel()
        self._tx_channel.exchange_declare(
            exchange=self._tx_exchange_name, exchange_type=exchange_type
        )

    def enable_rx_channel(self, rx_exchange_name, exchange_type):
        self._rx_connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'
        ))
        self._rx_exchange_name = rx_exchange_name
        self._rx_channel = self._rx_connection.channel()
        self._rx_channel.exchange_declare(
            exchange=self._rx_exchange_name, exchange_type=exchange_type
        )
        result = self._rx_channel.queue_declare(exclusive=True)
        self._rx_queue_name = result.method.queue
        self._rx_channel.queue_bind(
            exchange=self._rx_exchange_name,
            queue=self._rx_queue_name
        )

        self._rx_consumer_tag = self._rx_channel.basic_consume(
            self.on_receive_message,
            queue=self._rx_queue_name,
            no_ack=True
        )

        return self._rx_consumer_tag

    def on_receive_message(self, channel, method, properties, body):
        _ = channel, method, properties

        if self._received is not None:
            self._received.append(body)
        else:
            self.handle_received(body)

        if self.should_exit():
            print "cancelling data rx"
            self._rx_channel.stop_consuming(self._rx_consumer_tag)

    def handle_received(self, message):
        pass

    def next_message(self):
        if len(self._received) < 1:
            return None
        return self._received.pop(0)

    def handle_sigint(self, signum, frame):
        _ = signum, frame

        print "sigint caught"
        self._received_sigint = True

    def consume_in_worker(self):
        worker = threading.Thread(
            target=self.consume,
            name="worker-consumer"
        )

        self._received = []

        worker.start()

        while not self.should_exit():
            message = self.next_message()
            if message is not None:
                self.handle_received(message)

        worker.join()

    def consume(self):
        while not self.should_exit():
            try:
                self._rx_channel.start_consuming()
            except Exception, ex:
                if not self.should_exit():
                    raise
                else:
                    print "exception whilst exiting: {}".format(ex)

    def send_blob(self, message, routing_key=''):
        blob = json.dumps(message)
        self._tx_channel.basic_publish(
            exchange=self._tx_exchange_name,
            routing_key=routing_key,
            body=blob
        )


class Message(object):
    def __init__(self, df, ca, icao, raw):
        self.df = df
        self.ca = ca
        self.icao = icao
        self.raw = raw

    def type_description(self):
        if self.df == 17:
            return "ADS-B (air)"
        elif self.df == 18:
            return "ADS-B (gnd)"
        else:
            return "unknown"

    def to_json(self):
        return {
            'df': self.df,
            'ca': self.ca,
            'icao': self.icao,
            'raw': self.raw
        }

    @staticmethod
    def from_json(blob_str):
        blob = json.loads(blob_str)

        df = blob['df']
        ca = blob['ca']
        icao = blob['icao']
        raw = blob['raw']

        return Message(
            df, ca, icao, raw
        )

    @staticmethod
    def from_encoded(encoded):
        start = encoded.find("*")
        end = encoded.find(";")
        if -1 in (start, end):
            return None

        def decode_hex_str(hex_str):
            return [int(hex_str[i:i+2], 16) for i in range(0, len(hex_str), 2)]

        def bin_padded(value, length=8):
            binary = bin(value)[2:]
            missing = length - len(binary)
            if missing > 0:
                binary = ("0" * missing) + binary
            return binary

        byte_string = encoded[start+1:end]
        if len(byte_string) % 2 != 0:
            return None
        byte_values = decode_hex_str(byte_string)
        bit_string = "".join([bin_padded(value) for value in byte_values])

        def bits(offset, length):
            return int(bit_string[offset:offset+length], 2)

        def bytes(offset, length):
            return int(bit_string[offset*8:(offset*8)+(length*8)], 2)

        df = bits(0, 5)
        ca = bits(6, 3)
        icao = bytes(1, 3)

        return Message(df, ca, icao, byte_string)
