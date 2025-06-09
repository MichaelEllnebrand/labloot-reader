# labloot-reader
Read and display voltage data from Labloot multimeter
![demo](demo.png)

## Installation
Quick-start
```
apt-get install python3-serial
git clone https://github.com/gbyx3/labloot-reader.git
python3 server.py
```
This should start the server listening on port 8000

Navigate to http://<IP>:8000


## Labloot instructions
### Communication interface settings
Press the front panel Utility key, press the Next softkey to access the communication interface setting menu.

Press the Baud softkey to select the desired baud rate from 2400, 4800, 9600, 19200, 38400, 57600 or 115200. The default is 115200. Make sure that the baud rate matches that of the computer.

Press the Parity softkey, select the parity from None, Odd or Even. The default is None.

### Baud rate issues
It seems the device resets the baud rate each time you turn it off or on, the correct value is shown in the menu but no connection can be made until the baud rate is reapplied


