
import serial
import threading
import struct

from color import Color

class SerialInterface:
    def __init__(self, port, baudrate, callback):
        self.serial_port = serial.Serial(port, baudrate)
        self.callback = callback
        self.read_thread = threading.Thread(target=self.read_loop)
        self.read_thread.daemon = True
        self.read_thread.start()

    def __del__(self):
        if self.serial_port.is_open:
            self.serial_port.close()

    def read_loop(self):
        while True:
            data = self.serial_port.readline()#.decode('ascii')
            self.callback(data)

    def open(self):
        self.serial_port.open()

    def close(self):
        self.serial_port.close()

    def set_box_color(self, row, col, color: Color):
        red = (color >> 16) & 0xFF
        green = (color >> 8) & 0xFF
        blue = color & 0xFF
        cmd = struct.pack('!BBBBBBBBB', 0xAA, 0x01, row, col, red, green, blue, 0x55, 0x0A)
        self.serial_port.write(cmd)

    def set_relay(self, state: bool):
        cmd = struct.pack('!BBBBB', 0xAA, 0x02, 0x01 if state else 0x00, 0x55, 0x0A)
        self.serial_port.write(cmd)
        
    def light_boxes(self):
        cmd = struct.pack('!BBBB', 0xAA, 0x04, 0x55, 0x0A)
        self.serial_port.write(cmd)

    def clear_display(self):
        cmd = struct.pack('!BBBB', 0xAA, 0x03, 0x55, 0x0A)
        self.serial_port.write(cmd)

    def print_received_data(self, data):
        print(data)