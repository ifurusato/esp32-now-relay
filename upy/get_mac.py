
import network
import ubinascii

# Initialize the station interface to activate the radio
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Retrieve the hardware MAC address
mac_bytes = wlan.config('mac')

# Format into a readable hex string format
mac_hex = ubinascii.hexlify(mac_bytes, ':').decode('utf-8')

# Output both formats
print("Raw Bytes format (for code): {}".format(mac_bytes))
print("Hex String format:           {}".format(mac_hex))
