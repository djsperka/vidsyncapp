# rPI gpio stuff
from gpiod import Chip, LineSettings
from gpiod.line import Direction, Value, Bias


# piGPIO.py - a simple wrapper around gpiod to read the input and set the LED output. 
# This is not really necessary, but it makes the code cleaner and more modular. 
# It also allows us to easily change the GPIO library in the future if we want to.
class RPiVidSyncGPIO():
    
    def __init__(self, chip_id: str, led_line_id: str, input_line_id: str):

        self._chip = Chip(chip_id)
        self._led_offset = self._chip.line_offset_from_id(led_line_id)
        self._input_offset = self._chip.line_offset_from_id(input_line_id)
        self._line_settings = {
            self._led_offset: LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
            self._input_offset: LineSettings(direction=Direction.INPUT, bias=Bias.PULL_DOWN)
        }
        self._lines = self._chip.request_lines(consumer="MyGPIO", config=self._line_settings)
        self._encoder = None
        
    def __del__(self):
        self._chip.close()

    def get_input(self) -> int:
        return 1 if (self._lines.get_value(self._input_offset) == Value.ACTIVE) else 0
        
    def set_led(self, v: int) -> None:
        self._lines.set_value(self._led_offset, Value.ACTIVE if v>0 else Value.INACTIVE)
