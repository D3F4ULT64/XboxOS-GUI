import pygame
import sys
import time
import math
import array


def create_beep():
    frequency = 800
    duration = 0.2
    sample_rate = 44100

    samples = array.array(
        "h",
        [
            int(
                32767 *
                math.sin(
                    2 * math.pi * frequency * i / sample_rate
                )
            )
            for i in range(int(sample_rate * duration))
        ]
    )

    return pygame.mixer.Sound(buffer=samples)


def run():

    if len(sys.argv) < 4:
        print("Usage:")
        print("xboxos sound beep <seconds>")
        return

    if sys.argv[2] != "beep":
        print("Unknown sound command")
        return

    try:
        seconds = int(sys.argv[3])
    except:
        print("Invalid time")
        return


    pygame.init()
    pygame.mixer.init()

    print(f"Beeping for {seconds} seconds")

    beep = create_beep()

    end = time.time() + seconds

    while time.time() < end:
        beep.play()
        time.sleep(0.25)

    pygame.quit()

    print("Done!")