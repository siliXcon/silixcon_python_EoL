import swtools
import yos_device
import sys
from swtools import swtools_connection_options as conn

DEVICE_ADDRESS = 0
MSGCONF_STRING = "3:4"  # CAN speed 500 kbps

swt = swtools.swtools(
    conn=conn(
        interface="usb",
        addr=DEVICE_ADDRESS,
        msgconf_str=MSGCONF_STRING,
        credentials="login:password",
    )
)
device = yos_device.yos_device(swt)


def example():
    print("SN: " + device.get_sn())
    print("HWID: " + device.get_hwid())
    print("SWID: " + device.get_swid())
    print("CAN settings: " + device.get_msgconf(3))

    print("Controller temperature: " + str(device.get_var("/driver/temp")))

    print("Restore default config:")
    device.restore()
    print("Push config:")
    swt.yosctl_push(file="config.yc")

    print("Run YOS script:")
    ret = swt.script_std("esc3-selftest.ys")
    print()
    print("Script return code: " + str(ret))


# Check if device is connected and do interface clain
if device.is_NOT_on(fast=True):
    print("Device is not connected")
    sys.exit(1)

# Login to device
device.login()
swt.conn.set_if("usb")

example()

print()
print("Changing interface to kvaser and do the same over again")
print("=======================================================")

swt.conn.set_if("kvaser")
# # After you change interface, it is necesary run "yosctl id claim".
# This is done inside function "is_NOT_on"

if device.is_NOT_on(fast=True):
    print("Unable to connect using kvaser")
    sys.exit(1)

example()


print("Example finished")
sys.exit(0)
