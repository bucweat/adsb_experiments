
A collection of scripts for watching ADS-B plane data go by, with an RTL-SDR dongle as the receiver and using RabbitMQ for communicating between the scripts.

Requirements:
- RabbitMQ server on local machine
- RTL-SDR dongle connected, with correct drivers, and rtl_adsb available on command line
- Probably only works on linux (sorry!)
- pika library for python2

Running the scripts in any order should, however, work just as well - due to their reliance on RabbitMQ for communication.

Usage overview:
- First run the adsb-source.py (which expects to be able to run "rtl_adsb" on command line and read it's stdout)
- Run the adsb-decoder.py script to perform some decoding of the messages.
- Run either/all of adsb-targeted.py / adsb-icao-frequency.py

