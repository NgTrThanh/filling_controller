import time
import RPi.GPIO as GPIO
from hx711 import HX711

# define GPIO pins for input and output signals
INPUT_0_PIN = 21
INPUT_1_PIN = 20
INPUT_2_PIN = 16
INPUT_4_PIN = 26
INPUT_5_PIN = 19
INPUT_6_PIN = 13
OUTPUT_1_PIN = 17
OUTPUT_2_PIN = 27
OUTPUT_3_PIN = 22
OUTPUT_4_PIN = 23
OUTPUT_5_PIN = 24
OUTPUT_6_PIN = 25
OUTPUT_7_PIN = 12
OUTPUT_8_PIN = 6
OUTPUT_9_PIN = 18

# define target weight and tolerance
TARGET_WEIGHT = 50  # kg
TOLERANCE = 0.2  # kg
coarse_feed_cut = TARGET_WEIGHT * 0.8

max_filling_time = 300  # maximum time to reach target weight (in seconds)
push_delay = 0.5  # delay after bag push-out signal (in seconds)
some_delay1 = 0.5  # delay before lifting cylinder 1 (in seconds)
some_delay2 = 0.5  # delay after turning off scanner cylinder (in seconds)



# initialize GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(INPUT_0_PIN, GPIO.IN)
GPIO.setup(INPUT_1_PIN, GPIO.IN)
GPIO.setup(INPUT_2_PIN, GPIO.IN)
GPIO.setup(INPUT_4_PIN, GPIO.IN)
GPIO.setup(INPUT_5_PIN, GPIO.IN)
GPIO.setup(INPUT_6_PIN, GPIO.IN)
GPIO.setup(OUTPUT_1_PIN, GPIO.OUT)
GPIO.setup(OUTPUT_2_PIN, GPIO.OUT)
GPIO.setup(OUTPUT_3_PIN, GPIO.OUT)
GPIO.setup(OUTPUT_4_PIN, GPIO.OUT)
GPIO.setup(OUTPUT_5_PIN, GPIO.OUT)
GPIO.setup(OUTPUT_6_PIN, GPIO.OUT)
GPIO.setup(OUTPUT_7_PIN, GPIO.OUT)
GPIO.setup(OUTPUT_8_PIN, GPIO.OUT)
GPIO.setup(OUTPUT_9_PIN, GPIO.OUT)

# initialize HX711 loadcell amplifier

# It initializes the HX711 load cell amplifier by setting the dout and pd_sck pins, setting the reading format, reference unit, and then resetting the HX711 and performing a tare operation.

# However, it is important to note that the dout and pd_sck pins may need to be adjusted based on the specific wiring configuration of the load cell amplifier. Additionally, the reference unit value may need to be adjusted based on the specific load cell being used.

hx = HX711(dout=5, pd_sck=6)
print("HX711 initialized.")
hx.set_reading_format("MSB", "MSB")
print("Reading format set.")
hx.set_reference_unit(1)
print("Reference unit set to 1.")
hx.reset()
print("HX711 reset.")
hx.tare()
print("Tare operation performed.")


# function to read input signals
def read_input(pin):
    return GPIO.input(pin)

# function to write output signals
def write_output(pin, value):
    GPIO.output(pin, value)

# function to calculate the filling speed
def calculate_filling_speed(weight, time):
    return weight / time

# function to predict the timing for the cut-off point
def predict_cutoff_time(weight, filling_speed):

    time_to_cutoff = (TARGET_WEIGHT - coarse_feed_cut - weight) / filling_speed
    return time_to_cutoff
    
# main loop
while True:
    # read input signals
    input_0 = read_input(INPUT_0_PIN)
    input_1 = read_input(INPUT_1_PIN)
    input_2 = read_input(INPUT_2_PIN)
    input_4 = read_input(INPUT_4_PIN)
    input_5 = read_input(INPUT_5_PIN)
    input_6 = read_input(INPUT_6_PIN)

    # check process initiation
    if input_2 == GPIO.HIGH and input_4 == GPIO.HIGH:
        # send signal to scanner cylinder down
        write_output(OUTPUT_1_PIN, GPIO.HIGH)
        # start valve 2 for detecting bag
        write_output(OUTPUT_2_PIN, GPIO.HIGH)
        # wait for 0.5 sec
        time.sleep(0.5)
        # read pressure switch signal
        pressure_switch_signal = input_5

        if pressure_switch_signal == GPIO.HIGH:
            # start open dosing cylinder 100%
            GPIO.output(OUTPUT_5_PIN, GPIO.HIGH)
            GPIO.output(OUTPUT_6_PIN, GPIO.HIGH)
            GPIO.output(OUTPUT_7_PIN, GPIO.HIGH)

            # start filling motor, aeration ring
            GPIO.output(OUTPUT_8_PIN, GPIO.HIGH)
            GPIO.output(OUTPUT_9_PIN, GPIO.HIGH)

            # read weight data from load cell via HX711
            current_weight = hx.get_weight_mean(5)

            # monitoring weight, calculate filling speed
            fill_start_time = time.time()
            while current_weight < coarse_feed_cut:
                current_weight = hx.get_weight_mean(5)
                fill_time = time.time() - fill_start_time
                fill_speed = current_weight / fill_time

            # start open dosing cylinder 30%
            GPIO.output(OUTPUT_5_PIN, GPIO.HIGH)
            GPIO.output(OUTPUT_6_PIN, GPIO.LOW)
            GPIO.output(OUTPUT_7_PIN, GPIO.HIGH)

            # continue to monitor weight increase and calculate feeding speed
            while current_weight < target_weight:
                current_weight = hx.get_weight_mean(5)
                fill_time = time.time() - fill_start_time
                fill_speed = current_weight / fill_time

                # predict the timing for cut-off point for best accuracy of target weight
                time_to_target = (target_weight - current_weight) / fill_speed
                if time_to_target < max_filling_time:
                    cutoff_time = fill_start_time + time_to_target - 0.5
                    break

            # stop filling motor
            GPIO.output(OUTPUT_8_PIN, GPIO.LOW)
            GPIO.output(OUTPUT_9_PIN, GPIO.LOW)

            # close dosing cylinder
            GPIO.output(OUTPUT_5_PIN, GPIO.LOW)
            GPIO.output(OUTPUT_6_PIN, GPIO.LOW)
            GPIO.output(OUTPUT_7_PIN, GPIO.LOW)

            # wait for bag push out signal
            while True:
                input_6_state = GPIO.input(INPUT_6_PIN)
                if input_6_state == True:
                    time.sleep(push_delay)
                    break

            # lift cylinder 1 and turn off scanner cylinder
            GPIO.output(OUTPUT_1_PIN, GPIO.LOW)
            time.sleep(some_delay1)
            GPIO.output(OUTPUT_3_PIN, GPIO.HIGH)
            time.sleep(some_delay2)
            GPIO.output(OUTPUT_3_PIN, GPIO.LOW)

            # read weight and record it
            weight = hx711.get_weight_mean(10)
            weights.append(weight)

            # reset all parameters
            # reset all parameters
            GPIO.output(output_5_pin, GPIO.LOW)
            GPIO.output(output_6_pin, GPIO.LOW)
            GPIO.output(output_7_pin, GPIO.LOW)
            GPIO.output(output_8_pin, GPIO.LOW)
            GPIO.output(output_9_pin, GPIO.LOW)
            time.sleep(reset_delay)    