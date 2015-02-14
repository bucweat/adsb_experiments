
A collection of scripts for watching ADS-B plane data go by, with an RTL-SDR dongle as the receiver and using RabbitMQ for communicating between the scripts.

Requirements:
- RabbitMQ server on local machine
- RTL-SDR dongle connected, with correct drivers, and rtl_adsb available on command line
- Probably only works on linux (sorry!)
- pika library for python2

To play with these scripts first run the adsb-source.py, which expects to be able to run "rtl_sdr" on command line and read it's stdout. Next run the adsb-decoder.py script to perform some decoding of the messages.

Running the scripts in any order should, however, work just as well - due to their reliance on RabbitMQ for communication. Ensure you have a RabbitMQ server running on the local machine for these to work!

