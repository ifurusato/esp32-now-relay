
import sys
from machine import I2C

from i2c_scanner import I2CScanner

# force module reload
for mod in ['scan', 'i2c_scanner']:
    if mod in sys.modules:
        del sys.modules[mod]

# create I2C bus ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

print('configuring I2C bus…')
_i2c_id    =  1
_scl       = 22
_sda       = 21
_i2c_baud_rate = 400_000
_i2c = I2C(_i2c_id, scl=_scl, sda=_sda, freq=_i2c_baud_rate)

scanner = I2CScanner(i2c=_i2c)
scanner.i2cdetect()

