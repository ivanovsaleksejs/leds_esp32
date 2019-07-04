import _thread
import gc

import globals
import time
import machine
import math
import random

from neopixel import neopixel_write

#
# Returns time in ms
#
def time_ms():

    return int(time.time()%1000*1000)

#
# Calculates the offset of current zone by summing up the lengths of all previous zones
#
def sum_lengths(stripData, index):

    sum = 0

    for i in range(0, index):
        sum += stripData[i]["animation_data"]["zoneLength"] * stripData[i]["animation_data"]["stripLength"]

    return sum

#
# Thread that runs through animation data and updates np list
#
def redraw_thread(np, config, stripData):

    enum = list(enumerate(stripData))

    pin = machine.Pin(26)
    # pwm = machine.PWM(pin)
    # pwm.freq(78125)

    for index, strip in enum:
        strip["animation_data"]["offset"] = sum_lengths(stripData, index)

    msPerFrame = int(1000/config["frameRate"])
    frameCount = 0

    while globals.redraw_active:
        frameStart = time.ticks_ms()

        for index, strip in enum:
            if strip["animation_name"] == "blink":
                blink(np, config, index, strip["animation_data"])
            if strip["animation_name"] == "blinkrng":
                blinkrng(np, config, index, strip["animation_data"])
            if strip["animation_name"] == "blink_solid":
                blink(np, config, index, strip["animation_data"], True, False, True)
            if strip["animation_name"] == "blinkrng_solid":
                blinkrng(np, config, index, strip["animation_data"], True, False, True)
            if strip["animation_name"] == "solid":
                solid(np, config, index, strip["animation_data"])

        np.write()
        frameCount += 1
        if frameCount > 5:
            break


        frameTime = time.ticks_diff(time.ticks_ms(), frameStart)

        if frameTime <= msPerFrame:
            time.sleep_ms(msPerFrame - frameTime)


#
# ANIMATION FUNCTIONS
#

#
# Solid color function
#
def solid(np, config, strip_number, animation_data):
    if not "drawn" in animation_data or not animation_data["drawn"]:
        animation_data["totalLength"] = animation_data["zoneLength"] * animation_data["stripLength"]
        current_color = animation_data["color"]
        color = [0] * 3
        color[np.ORDER[0]] = config["gamma"][int(current_color[0])]
        color[np.ORDER[1]] = config["gamma"][int(current_color[1])]
        color[np.ORDER[2]] = config["gamma"][int(current_color[2])]
        while True:
            try:
                color = bytearray(color * animation_data["totalLength"])
                np.buf[animation_data["offset"] * np.bpp : (animation_data["offset"] + animation_data["totalLength"]) * np.bpp] = color
                animation_data["drawn"] = True
            except MemoryError:
                gc.collect()
                print("here")
                continue
            break

#
# Simple blink function
# Fades from given color to the value defined by quot parameter
#
def blink(np, config, strip_number, animation_data, half=True, pulse=False, solid=False):

    if not "quotient" in animation_data or not animation_data["quotient"]:
        animation_data["totalLength"] = animation_data["zoneLength"] * animation_data["stripLength"]

        animation_time = animation_data["speed"]
        
        # For random blinking - resets full cycle counter
        animation_data["fullCycle"] = 0

        frameCount = int(config["frameRate"] * animation_time / 1000)
        animation_data["frameCount"] = frameCount

        current_color = animation_data["color"]
        color = [0] * 3
        color[np.ORDER[0]] = config["gamma"][int(current_color[0])]
        color[np.ORDER[1]] = config["gamma"][int(current_color[1])]
        color[np.ORDER[2]] = config["gamma"][int(current_color[2])]

        #color = bytearray(color)

        if solid:
            animation_data["frames"] = [color for _ in range (0, frameCount+1)]

        else:
            animation_data["frames"] = [color]

            startColor = max(animation_data["color"])
            stopColor = startColor*animation_data["quot"]


            for i in range(0, frameCount):
                # Sinusoidal function that generates quotients used to divide start color on them
                quotient = 2 * startColor / (math.cos(i * math.pi / frameCount) * (startColor - stopColor) + startColor + stopColor)

                color = [0] * 3
                color[np.ORDER[0]] = config["gamma"][int(current_color[0] / quotient)]
                color[np.ORDER[1]] = config["gamma"][int(current_color[1] / quotient)]
                color[np.ORDER[2]] = config["gamma"][int(current_color[2] / quotient)]
                #color = bytearray(color)

                animation_data["frames"].append(color)
        
        animation_data["quotient"] = True





    # When direction is true the animation goes from black to the original color
    if not "direction" in animation_data:
        animation_data["direction"] = False
    direction = animation_data["direction"]

    if not "position" in animation_data:
        animation_data["position"] = 0
    position = animation_data["position"]

    if direction and position == 0:
        direction = False
        animation_data["fullCycle"] += 1

        if solid:
            animation_data["fullCycle"] = 10

    if (not direction) and position >= animation_data["frameCount"] - 1:
        direction = True

    animation_data["direction"] = direction

    # Infinite loop that will repeat an action until no exception is caught
    while True:
        try:
            color = bytearray(animation_data["frames"][position] * animation_data["totalLength"])
            np.buf[animation_data["offset"] * np.bpp : (animation_data["offset"] + animation_data["totalLength"]) * np.bpp] = color
        except MemoryError:
            gc.collect()
            continue
        break

    
    if direction:
        position -= 1
    else:
        position += 1

    animation_data["position"] = position

    gc.collect()

def blinkrng(np, config, strip_number, animation_data, half=True, pulse=False, solid=False):
    if not "fullCycle" in animation_data:
        animation_data["fullCycle"] = 0

    if animation_data["fullCycle"] >= 10:
        color = (0, 0, 0)
        while max(color) < 252:
            color = (random.randint(0,4) * 63, random.randint(0,4) * 63, random.randint(0,4) * 63)
        animation_data["speed"] = animation_data["speed"] if solid else random.randint(9, 36) * 200
        animation_data["color"] = color

        animation_data["quotient"] = False

    blink(np, config, strip_number, animation_data, half=half, pulse=pulse, solid=solid)
