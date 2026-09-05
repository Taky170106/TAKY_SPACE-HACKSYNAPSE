"""
I2C (PCF8574 backpack) HD44780 LCD driver for MicroPython.
Works with the common 16x2 LCD + I2C piggyback board. You do not edit this.
(Standard community I2cLcd implementation.)
"""
import time
from lcd_api import LcdApi

# PCF8574 pin bit positions
MASK_RS = 0x01
MASK_E = 0x04
SHIFT_BACKLIGHT = 3
SHIFT_DATA = 4


class I2cLcd(LcdApi):
    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.i2c.writeto(self.i2c_addr, bytes([0]))
        time.sleep_ms(20)
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        time.sleep_ms(5)
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        time.sleep_ms(1)
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        time.sleep_ms(1)
        self.hal_write_init_nibble(self.LCD_FUNCTION)
        time.sleep_ms(1)
        LcdApi.__init__(self, num_lines, num_columns)
        cmd = self.LCD_FUNCTION
        if num_lines > 1:
            cmd |= self.LCD_FUNCTION_2LINES
        self.hal_write_command(cmd)

    def hal_write_init_nibble(self, nibble):
        byte = ((nibble >> 4) & 0x0F) << SHIFT_DATA
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))

    def hal_backlight_on(self):
        self.i2c.writeto(self.i2c_addr, bytes([1 << SHIFT_BACKLIGHT]))

    def hal_backlight_off(self):
        self.i2c.writeto(self.i2c_addr, bytes([0]))

    def hal_write_command(self, cmd):
        b = ((self.backlight << SHIFT_BACKLIGHT) | (((cmd >> 4) & 0x0F) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([b | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([b]))
        b = ((self.backlight << SHIFT_BACKLIGHT) | ((cmd & 0x0F) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([b | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([b]))
        if cmd <= 3:
            time.sleep_ms(5)

    def hal_write_data(self, data):
        b = (MASK_RS | (self.backlight << SHIFT_BACKLIGHT) |
             (((data >> 4) & 0x0F) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([b | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([b]))
        b = (MASK_RS | (self.backlight << SHIFT_BACKLIGHT) |
             ((data & 0x0F) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([b | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([b]))
