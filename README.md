# NexStar8 Control
> A program designed to control the ORIGINAL Celestron NexStar 5 and 8 telescope mounts and optionally interface with Stellarium's telescope server. Most of the software using the original antiquated RS-232 protocol is incompatible with modern astronomy software, and this project aims to provide a simple (and quite basic) solution.

## Requirements
1. A Celestron NexStar 5 or 8 telescope mount. Note: this will **NOT** work with the 8SE, 8i, 8 GPS, etc., only the original models. See image of model number:

   ![endcap model number 8 of NexStar OTA](./photos/model.jpeg).
3. The [`telescope.py`](./telescope.py) file, a working installation of Python 3, and the [`pyserial`](https://pyserial.readthedocs.io/en/latest/pyserial.html) module (`pip3 install pyserial`).
4. A RS-232 Serial adapter cable. The [one I used is from Amazon](https://www.amazon.com/gp/product/B08KRSKD2C/) and works quite well. Make sure to get one that uses the FTDI chipset for best results!

## Setup
(for more detailed code install instructions: follow along step-by-step with issue [#1](https://github.com/cole-wilson/nexstar8/issues/1) or make a new issue)

1. Connect the RS-232 serial/USB cable to the RJ9 jack at the bottom of the Hand Controller:

   ![RJ9 Jack on hand controller](./photos/rs232port.jpeg)
3. Alignment:

    1. **RA/DEC:** If you want to use the RA/DEC (right ascension/declination) mode instead of ONLY alt/az control (required for Stellarium!), you must go through the entire auto-align/2-star-align process as usual without a computer connection first.
        
    2. **Alt/Az:** If you don't care about RA/DEC and just want an easy Alt/Az setup, you can point the telescope due North and level before powering on, and hit the `UNDO` button to skip alignment.
5. **RS-232 Mode:** Enable computer control by hitting `MENU (3)`, then scrolling down to RS-232 Mode (using `DOWN (9)`, not the arrow buttons which will just slew the scope), and hitting `ENTER`. Note that if you want auto/sidereal tracking turned off while your scope if under computer control, you must first disable this before entering RS-232 mode.

   ![RS-232 Mode](./photos/mode.jpeg)
7. Determine the serial port your telescope is using on your computer. On unix/mac systems you can run `ls /dev` to see all connected devices with the telescope unplugged, and again when it is plugged in. There should be a difference in the list, and your connection port is one of those paths. On my mac, there are two files that appear: `/dev/cu.usbserial-D30HB8OX` and `/dev/tty.usbserial-D30HB8OX`. Pick whatever ISN'T the `tty` one, so my serial port is `/dev/cu.usbserial-D30HB8OX` (will very likely be different for you!).
8. You are all ready to use the program! For [usage info](#Usage), see below. For instructions on the [Stellarium setup](#Stellarium), see farther below.

## Usage
```bash
$ python3 telescope.py --help

usage: telescope.py [-h] (--altaz ALTITUDE AZIMUTH | --relative ALTITUDE AZIMUTH | --radec RA DEC | --get-radec | --get-altaz | --stellarium PORT | --interactive) SERIAL_PORT

Provides control functions for the Original Celestron NexStar 5 and 8 models through the hand controller RS-232 port. All angles are in DEGREES!

positional arguments:
  SERIAL_PORT           the serial port of the telescope

options:
  -h, --help            show this help message and exit
  --altaz ALTITUDE AZIMUTH
                        slew to a specific altitude and azimuth
  --relative ALTITUDE AZIMUTH
                        slew in-place relative to the current position
  --radec RA DEC        slew to a specific right-ascension and declination
  --get-radec           get the current RA, Dec in degrees of the telescope
  --get-altaz           get current Alt, Az in degrees of the telescope
  --stellarium PORT     run a stellarium telescope server on the designated port
  --interactive         interactive slew control with keyboard

cole wilson 2024
```

### Examples
- Slew to 45 degrees Altitude, at an Azimuth of 270 degrees (due West):
    ```bash
    $ python3 telescope.py --altaz 45 270
    # True (False if error)
    ```
- Slew to a Right Ascension of 42.324 degrees (2.8h 19m 26.4s), and a Declination of 87.123 degrees (87°7'22.8"):
    ```bash
    $ python3 telescope.py --radec 42.324 87.123
    # True (False if error)
    ```
- Move up 1 degree of altitude and right 3 degrees of azimuth:
    ```bash
    $ python3 telescope.py --relative 1 3
    # True (False if error)
    ```
- Get the current Altitude and Azimuth position of the mount (in degrees):
    ```bash
    $ python3 telescope.py --get-altaz
    # (45.0, 270.0)
    ```
- Get the current Right Ascension and Declination position of the mount (in degrees):
    ```bash
    $ python3 telescope.py --get-radec
    # (42.324, 87.123)
    ```
- Enter a (beta) interactive mode in which the arrow and WASD keys are linked to the relative contol mode. Note that as with all commands, the program will hang until each slew is completed, which can take several seconds. This makes it not very responsive...:
    ```bash
    $ python3 telescope.py --interactive
    ```
- Run a telescope control TCP server on the given port for Stellarium telescope control (see below for more info on how to configure!):
    ```bash
    $ python3 telescope.py --stellarium 10001 # <-- recommended port!
    ```

### Notes
While in RS-232 mode, you can change rate, slew and otherwise control your telescope but when a command is processing (even if it is just a get location command), the buttons on the controller are locked until the command completes.

## Stellarium
Stellarium is awesome software, and now thanks to this project you can control your NexStar 5/8 Mount with it!

### Setup
1. Open Stellarium, go to Configuration (wrench icon on left side of screen) > Plugins > Telescope Control, and hit `Load at startup`:
    ![plugin setup](./photos/plugin.png)
2. Hit `Configuration` for the plugin, and then `Add A New Telescope`
3. Choose the `External software or a remote computer` option, give your scope a name, select the port you chose earlier, and optionally select `Start/connect at startup`:
    ![port config](./photos/config.jpg)
4. Hit `OK` and then `Connect`. You should see a "connected" message appear in your terminal where you are running `python3 telescope.py --stellarium PORT`.

### Usage
Stellarium has extensive explanations of the telescope control program, but here is an brief overview.

You should see a moving orange reticle showing your telescopes position in the sky. The position updates every 4-5 seconds, or after a slew. If you select an object and hit `Ctrl+1` (or `Command+1` on Mac), the telescope will slew to that location!

![example](./photos/example.jpg)
