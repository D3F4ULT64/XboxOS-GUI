import pygame
import time
from pynput.mouse import Button, Controller


# Buttons
A = 0
B = 1
X = 2
Y = 3
LB = 4
RB = 5

# Axes
LEFT_X = 0
LEFT_Y = 1

RIGHT_X = 2
RIGHT_Y = 3

LT = 4
RT = 5

DEADZONE = 0.15


mouse = Controller()


def deadzone(value):
    if abs(value) < DEADZONE:
        return 0
    return value


def trigger(value):
    return value > 0.5


def run():

    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No controller found.")
        return

    controller = pygame.joystick.Joystick(0)
    controller.init()

    speed = 12
    precision = False
    turbo = False
    dragging = False

    old_rt = False
    old_lt = False

    print("=" * 45)
    print("           XboxOS Mouse Mode")
    print("=" * 45)

    print("Controller:", controller.get_name())

    print("""
Controls
--------
Left Stick : Move Mouse
RT         : Left Click
LT         : Right Click
A          : Double Click
X          : Middle Click
Y          : Drag Toggle
RB         : Scroll Up
LB         : Scroll Down

D-Pad Up   : Faster
D-Pad Down : Slower
D-Pad Left : Precision
D-Pad Right: Turbo

Right Stick: Scroll
B          : Exit
""")

    print("Mouse Mode Active!")

    clock = pygame.time.Clock()

    running = True

    while running:

        pygame.event.pump()

        # ---------------------
        # Left stick movement
        # ---------------------

        x = deadzone(controller.get_axis(LEFT_X))
        y = deadzone(controller.get_axis(LEFT_Y))

        current_speed = speed

        if precision:
            current_speed = 3

        if turbo:
            current_speed = 25


        if x or y:
            mouse.move(
                x * current_speed,
                y * current_speed
            )


        # ---------------------
        # Triggers
        # ---------------------

        rt = trigger(controller.get_axis(RT))
        lt = trigger(controller.get_axis(LT))


        if rt and not old_rt:
            mouse.click(Button.left)


        if lt and not old_lt:
            mouse.click(Button.right)


        old_rt = rt
        old_lt = lt



        # ---------------------
        # Right stick scrolling
        # ---------------------

        ry = deadzone(controller.get_axis(RIGHT_Y))

        if ry:
            mouse.scroll(
                int(-ry * 3),
                0
            )



        # ---------------------
        # Buttons
        # ---------------------

        for event in pygame.event.get():

            if event.type == pygame.JOYBUTTONDOWN:

                # B exit
                if event.button == B:
                    running = False


                # A double click
                elif event.button == A:
                    mouse.click(Button.left, clicks=2)


                # X middle click
                elif event.button == X:
                    mouse.click(Button.middle)



                # Y drag toggle
                elif event.button == Y:

                    dragging = not dragging

                    if dragging:
                        mouse.press(Button.left)
                        print("Drag: ON")

                    else:
                        mouse.release(Button.left)
                        print("Drag: OFF")



                # RB scroll up
                elif event.button == RB:
                    mouse.scroll(3, 0)


                # LB scroll down
                elif event.button == LB:
                    mouse.scroll(-3, 0)



            # ---------------------
            # D-Pad
            # ---------------------

            elif event.type == pygame.JOYHATMOTION:

                hat = event.value


                if hat == (0, 1):
                    speed += 2
                    print("Speed:", speed)


                elif hat == (0, -1):
                    speed = max(2, speed - 2)
                    print("Speed:", speed)


                elif hat == (-1, 0):
                    precision = True
                    turbo = False
                    print("Mode: Precision")


                elif hat == (1, 0):
                    turbo = True
                    precision = False
                    print("Mode: Turbo")

                elif hat == (0, 0):
                    if precision or turbo:
                        print("Mode: Normal")
                    precision = False
                    turbo = False



        clock.tick(120)



    if dragging:
        mouse.release(Button.left)

    pygame.quit()

    print("Exited XboxOS Mouse Mode.")