import uuid

import RPi.GPIO as gpio

from speech import TextToSpeech
from verbal_log import Recorder
from log import tlog
from tracking import Tracking
from state import RunningState, CurrentTaskState, DescriptionState, ButtonIdState
import time

# Ignore warning for now
gpio.setwarnings(False)
gpio.setmode(gpio.BOARD)

# Map to gpio, follows board format (1 - ...)
# Run 'pinout' on shell in rpi to get mappings.
pin_out = {
    'email': 3,  # GPIO2
    'call': 13,  # GPIO27
    'meeting': 11,  # GPIO2
    'admin': 5,  # GPIO3
    'stop': 7,  # GPIO17
    'tracking_led': 23
}

timecamp_task_id = {
    'email': 90658387,
    'call': 96440757,
    'meeting': 96440756,
    'admin': 96440755,
}

bounce_ms = 1000


class GlobalState:
    def __init__(self):
        self.running = RunningState()
        self.task = CurrentTaskState()
        self.description = DescriptionState()
        self.button = ButtonIdState()


global_state = GlobalState()


class InputHandler:
    def __init__(self):
        self.recorder = Recorder(channels=1)
        self.speech = TextToSpeech()
        self.tracking = Tracking()
        self.audio_filename = "recordings/recording-" + str(uuid.uuid4()) + ".wav"
        self.recfile2 = None

    def init(self):
        tlog('Starting InputHandler thread.')

        # Idle is the state where this loop does nothing so after each action, set it to idle
        while True:
            if global_state.running.get() == 'pressed':
                tlog("pressed")
                with self.recorder.open(self.audio_filename, 'wb') as self.recfile2:
                    tlog("start recording")
                    self.recfile2 = self.recfile2.start_recording()
                    # time.sleep(5.0)
                    # self.recfile2.stop_recording()
                    global_state.running.set('recording')

            elif global_state.running.get() == 'released':
                tlog("released and stopping recording")
                self.recfile2 = self.recfile2.stop_recording()
                global_state.running.set('idle')
            elif global_state.running.get() == 'stop':
                tlog("stopping")
                global_state.running.set('idle')


class Tia:
    def __init__(self):
        pass

    def rising(self, button_id, task_id):
        tlog("released - button id: " + str(button_id))

        # Set state for monitor to pick up on
        global_state.running.set('released')
        global_state.task.set(task_id)
        global_state.button.set(button_id)

        # Reset button so that it can be used again.
        gpio.remove_event_detect(button_id)
        gpio.add_event_detect(button_id, gpio.FALLING, callback=lambda x: self.falling(button_id, task_id),
                              bouncetime=bounce_ms)

        # Convert audio to text
        # self.recfile2.stop_recording()

        # converted_text = self.speech.convert(self.audio_filename)
        # converted_text = 'testxxxx'
        # tlog('converted text: ' + converted_text)
        #
        # # Start timer for job with speech conversion in description
        # self.tracking.start(converted_text, task_id)

    def falling(self, button_id, task_id):
        tlog("pressed - button id: " + str(button_id))

        # Set state for monitor to pick up on
        global_state.running.set('pressed')
        global_state.task.set(task_id)
        global_state.button.set(button_id)
        gpio.remove_event_detect(button_id)

        # Reset button so that it can be used again.
        gpio.add_event_detect(button_id, gpio.RISING, callback=lambda x: self.rising(button_id, task_id),
                              bouncetime=bounce_ms)

        # self.recorder.start_recording()
        # self.recfile2.start_recording()

    def stop(self):
        tlog("stopping")
        # self.tracking.stop()

    def run(self):
        # TODO put this in a loop...
        gpio.setup(pin_out['email'], gpio.IN, pull_up_down=gpio.PUD_UP)
        gpio.setup(pin_out['call'], gpio.IN, pull_up_down=gpio.PUD_UP)
        gpio.setup(pin_out['meeting'], gpio.IN, pull_up_down=gpio.PUD_UP)
        gpio.setup(pin_out['admin'], gpio.IN, pull_up_down=gpio.PUD_UP)
        gpio.setup(pin_out['stop'], gpio.IN, pull_up_down=gpio.PUD_UP)

        gpio.setup(pin_out['tracking_led'], gpio.OUT)

        gpio.add_event_detect(pin_out['email'], gpio.FALLING,
                              callback=lambda x: self.falling(pin_out['email'], timecamp_task_id['email']),
                              bouncetime=bounce_ms)

        gpio.add_event_detect(pin_out['call'], gpio.FALLING,
                              callback=lambda x: self.falling(pin_out['call'], timecamp_task_id['call']),
                              bouncetime=bounce_ms)

        gpio.add_event_detect(pin_out['meeting'], gpio.FALLING,
                              callback=lambda x: self.falling(pin_out['meeting'], timecamp_task_id['meeting']),
                              bouncetime=bounce_ms)

        gpio.add_event_detect(pin_out['admin'], gpio.FALLING,
                              callback=lambda x: self.falling(pin_out['admin'], timecamp_task_id['admin']),
                              bouncetime=bounce_ms)

        gpio.add_event_detect(pin_out['stop'], gpio.RISING, callback=lambda x: self.stop(), bouncetime=bounce_ms)

        # start monitoring and acting on button state changes
        # self.recorder.clear_recordings()
        tlog("Tia is starting up.")  # Run until someone presses enter
        handler = InputHandler()
        handler.init()

        gpio.cleanup()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    tia = Tia()
    tia.run()
