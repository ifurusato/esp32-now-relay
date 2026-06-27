
import espnow

# Check the maximum supported packet length
max_len = espnow.MAX_DATA_LEN
print("Max Data Length: {0} bytes".format(max_len))

if max_len > 250:
    print("ESP-NOW V2.0 is available.")
else:
    print("ESP-NOW V1.0 is available.")

