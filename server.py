import struct
import socket
import math
from telescope import NexStar8

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 10001              # Arbitrary non-privileged port
telescope = NexStar8("/dev/cu.usbserial-D30HB8OX")

def read_requested_ra_dec(sock):
    try:
        _ = struct.unpack("H", sock.recv(2))[0]
        _ = struct.unpack("H", sock.recv(2))[0]
        _ = struct.unpack("Q", sock.recv(8))[0]
        ran = struct.unpack("I", sock.recv(4))[0]
        decn = struct.unpack("i", sock.recv(4))[0]

        ra = 180 * (ran / 0x80000000)
        dec = 90 * (decn / 0x40000000)
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

    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        conn.settimeout(4)
        while True:
            ra, dec = read_requested_ra_dec(conn)
            if ra is not None and dec is not None:
                telescope.goto_ra_dec(ra, dec)
            send_actual_ra_dec(conn)
