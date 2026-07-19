import ctypes
import sys
import time


# Load Windows XInput
try:
    xinput = ctypes.WinDLL("xinput1_4.dll")
except:
    try:
        xinput = ctypes.WinDLL("xinput1_3.dll")
    except:
        xinput = None


class XINPUT_VIBRATION(ctypes.Structure):
    _fields_ = [
        ("wLeftMotorSpeed", ctypes.c_ushort),
        ("wRightMotorSpeed", ctypes.c_ushort)
    ]


def set_vibration(strength):
    if xinput is None:
        print("XInput not available.")
        return False

    # Convert 0-100 to 0-65535
    value = int((strength / 100) * 65535)

    vibration = XINPUT_VIBRATION()
    vibration.wLeftMotorSpeed = value
    vibration.wRightMotorSpeed = value

    result = xinput.XInputSetState(
        0,
        ctypes.byref(vibration)
    )

    return result == 0


def stop_vibration():
    if xinput is None:
        return

    vibration = XINPUT_VIBRATION()
    vibration.wLeftMotorSpeed = 0
    vibration.wRightMotorSpeed = 0

    xinput.XInputSetState(
        0,
        ctypes.byref(vibration)
    )


def run():

    strength = 100

    # xboxos vibrate 50
    if len(sys.argv) > 2:
        try:
            strength = int(sys.argv[2])
        except:
            print("Usage: xboxos vibrate <0-100>")
            return


    strength = max(0, min(100, strength))

    print("=" * 35)
    print("     XboxOS Vibrate")
    print("=" * 35)

    print("Strength:", strength, "%")


    if set_vibration(strength):
        print("Vibration started!")

        time.sleep(1)

        stop_vibration()

        print("Done.")

    else:
        print("Could not vibrate controller.")