
import serial
import threading
import struct

from color import Color

class SerialInterface:
    def __init__(self, port, baudrate, callback):
        self.port = port
        self.baud = baudrate
        self.callback = callback
        self.ser = None
        self.relay_on = False
        self.stop_event = None

    def __del__(self):
        if self.stop_event is not None:
            self.stop_event.set()

        if self.ser is not None and self.ser.is_open:
            self.ser.close()

    def read_loop(self, stop_event: threading.Event):
        while not stop_event.is_set():
            try:
                data = self.ser.readline()#.decode('ascii')
            finally:
                if data is not None:
                    self.callback(data)

    def open(self):
        if self.ser is None:
            self.ser = serial.Serial(self.port, self.baud)
        else:
            self.ser.open()

        self.stop_event = threading.Event()

        self.read_thread = threading.Thread(target=self.read_loop, args=(self.stop_event,))
        self.read_thread.daemon = True
        self.read_thread.start()

    def close(self):
        if self.ser is not None:
            self.stop_event.set()
            self.ser.close()

    def set_box_color(self, row, col, color: Color):
        # Get integer value from enum
        color = color.value

        red = (color >> 16) & 0xFF
        green = (color >> 8) & 0xFF
        blue = color & 0xFF
        cmd = struct.pack('!BBBBBBBBB', 0xAA, 0x01, row, col, red, green, blue, 0x55, 0x0A)
        print(f"CMD: {cmd}")
        self.ser.write(cmd)
        self.relay_on = True

    def set_box_color_rgb(self, row, col, r, g, b):
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            raise ValueError(f"r ({r}), g ({g}), and b ({b}) must be integers between 0 and 255")
        
        cmd = struct.pack('!BBBBBBBBB', 0xAA, 0x01, row, col, r, g, b, 0x55, 0x0A)
        self.ser.write(cmd)

    def set_relay(self, state: bool):
        cmd = struct.pack('!BBBBB', 0xAA, 0x02, 0x01 if state else 0x00, 0x55, 0x0A)
        self.ser.write(cmd)
        self.relay_on = state

    def light_boxes(self):
        cmd = struct.pack('!BBBB', 0xAA, 0x04, 0x55, 0x0A)
        self.ser.write(cmd)

    def clear_display(self):
        cmd = struct.pack('!BBBB', 0xAA, 0x03, 0x55, 0x0A)
        self.ser.write(cmd)

def print_received_data(data):
    print(data)