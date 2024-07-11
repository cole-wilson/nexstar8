import math
import curses
import serial
import struct
import socket
import argparse

HOST = ''
PORT = 10001

class NexStar8:
    """RS-232 control features of the original Celestron NexStar 8 Telescope"""
    ser: serial.Serial
    fmt = ">h"

    def __init__(self, port) -> None:
        self.ser = serial.Serial(port, 9600)

    def initialization(self):
        """internatl initialization method"""
        self.ser.write(b"?")
        return self.read(1) == b"#"

    def goto_ra_dec(self, ra, dec):
        """move scope to designated Right Acension and Declination (degrees, scope must be aligned first)"""
        self.initialization()
        self.ser.write(b"R")

        if ra > 180:
            ra = 0 - (360 - ra)

        ran, decn = self.angle_to_number(ra), self.angle_to_number(dec)

        rab = struct.pack(self.fmt, ran)
        decb = struct.pack(self.fmt, decn)

        self.ser.write(rab + decb)

        return self.read(1) == b"@"

    def goto_alt_az(self, alt, az):
        """move scope to designated altitude and azimuth (degrees)"""
        self.initialization()
        self.ser.write(b"A")

        altn, azn = self.angle_to_number(alt), self.angle_to_number(az)
        aznb = struct.pack(self.fmt, azn)
        altb = struct.pack(self.fmt, altn)


        self.ser.write(aznb + altb)
        return self.read(1) == b"@"

    def get_ra_dec(self):
        """get Right Acension and Declination position of scope (degrees, scope must be aligned first)"""
        self.initialization()
        self.ser.write(b"E")

        d = self.read(4)

        ran = struct.unpack(self.fmt, d[:2])[0]
        decn = struct.unpack(self.fmt,d[2:])[0]

        ra, dec = self.number_to_angle(ran), self.number_to_angle(decn)
        if ra < 0:
            ra += 360
        return ra, dec

    def get_alt_az(self):
        """get altitude and azimuth position of scope (degrees)"""
        self.initialization()
        self.ser.write(b"Z")

        d = self.read(4)

        azn = struct.unpack(self.fmt, d[:2])[0]
        altn = struct.unpack(self.fmt,d[2:])[0]

        alt, az = self.number_to_angle(altn), self.number_to_angle(azn)
        return alt, az

    def slew_relative(self, alt_increment, az_increment):
        """slew alt/az relative to current position, for emulating hand control"""
        alt, az = self.get_alt_az()
        return self.goto_alt_az(alt+alt_increment, az+az_increment)

    def read(self, x):
        """unused proxy method for serial read()... (for logging)"""
        value = self.ser.read(x)
        return value

    def number_to_angle(self, number):
        """formats a raw value from the telescope to be in degrees"""
        return 180 * (number / 32768)

    def angle_to_number(self, angle):
        """formats a degree angle to be a raw number sendable to the telescope"""
        return math.floor(((angle) / 180) * 32768)

class NexStar5(NexStar8):
    """RS-232 control features of the original Celestron NexStar 5 Telescope"""
    pass



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    description='Provides control functions for the Original Celestron NexStar 5 and 8 models through the hand controller RS-232 port. All angles are in DEGREES!',
                    epilog='cole wilson 2024')

    parser.add_argument("port", metavar="SERIAL_PORT", help="the serial port of the telescope")
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("--altaz", nargs=2, type=float, metavar=('ALTITUDE', 'AZIMUTH'), help="slew to a specific altitude and azimuth")
    group.add_argument("--relative", nargs=2, type=float, metavar=('ALTITUDE', 'AZIMUTH'), help="slew in-place relative to the current position")
    group.add_argument("--radec", nargs=2, metavar=('RA', 'DEC'), help="slew to a specific right-ascension and declination")
    group.add_argument("--get-radec", action="store_true", help="get the current RA, Dec in degrees of the telescope")
    group.add_argument("--get-altaz", action="store_true", help="get current Alt, Az in degrees of the telescope")
    group.add_argument("--stellarium", nargs=1, metavar="PORT", type=int, default=1001, help="run a stellarium telescope server on the designated port")
    group.add_argument("--interactive", action="store_true", help="interactive slew control with keyboard")

    args = parser.parse_args()
    telescope = NexStar8(args.port)

    # input(args)

    if args.get_altaz:
        print(telescope.get_alt_az())
    elif args.get_radec:
        print(telescope.get_ra_dec())
    elif args.altaz:
        print(telescope.goto_alt_az(*args.altaz))
    elif args.radec:
        print(telescope.goto_ra_dec(*args.radec))
    elif args.relative:
        print(telescope.slew_relative(*args.relative))
    elif args.interactive:
        screen = curses.initscr()
        def prog(screen):
            inc = 2
            screen.addstr("use the arrow or WASD keys to control altitude and azimuth of the telescope. use ctrl+c to exit. (may be slow because you have to wait for it to slew before next increment is performed...)")
            while True:
                a = screen.getch()
                screen.refresh()
                if a in (curses.KEY_UP, 'w'):
                    telescope.slew_relative(inc, 0)
                elif a in (curses.KEY_DOWN, 's'):
                    telescope.slew_relative(-inc, 0)
                elif a in (curses.KEY_LEFT, 'a'):
                    telescope.slew_relative(0, -inc)
                elif a in (curses.KEY_RIGHT, 'd'):
                    telescope.slew_relative(0, inc)
                print(a)
        curses.wrapper(prog)
    elif args.stellarium:
        def read_requested_ra_dec(sock):
            try:
                _ = struct.unpack("H", sock.recv(2))[0]
                _ = struct.unpack("H", sock.recv(2))[0]
                _ = struct.unpack("Q", sock.recv(8))[0]
                ran = struct.unpack("I", sock.recv(4))[0]
                decn = struct.unpack("i", sock.recv(4))[0]

                ra = 180 * (ran / 0x80000000)
                dec = 90 * (decn / 0x40000000)

                print(f"got command from stellarium: slew to (ra={ra}deg, dec={dec}deg)")
                return ra, dec
            except TimeoutError:
                return None, None

        def send_actual_ra_dec(sock):
            ra, dec = telescope.get_ra_dec()
            ran = (ra/180) * 0x80000000
            decn = (dec/90) * 0x40000000

            size = struct.pack("H", 24)
            typ = struct.pack("H", 0)
            time = struct.pack("Q", 0)
            rab = struct.pack("I", math.floor(ran))
            decb = struct.pack("i", math.floor(decn))
            status = struct.pack("i", 0)

            sock.sendall(size + typ + time + rab + decb + status)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen(1)
            print(f'no specific commands requested, starting stellarium telescope server...\nlistening on port {PORT}, host `{HOST}`...')

            conn, addr = s.accept()
            with conn:
                print('connection from', addr)
                conn.settimeout(4)
                while True:
                    ra, dec = read_requested_ra_dec(conn)
                    if ra is not None and dec is not None:
                        telescope.goto_ra_dec(ra, dec)
                    send_actual_ra_dec(conn)
