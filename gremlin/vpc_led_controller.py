import os
import subprocess

COMMAND_LIST = ["00 - Set Default",
                "01 - Set Add-boards LED 01", "02 - Set Add-boards LED 02",
                "03 - Set Add-boards LED 03", "04 - Set Add-boards LED 04",
                "05 - Set On-board LED 01", "06 - Set On-board LED 02", "07 - Set On-board LED 03",
                "08 - Set On-board LED 04", "09 - Set On-board LED 05", "10 - Set On-board LED 06",
                "11 - Set On-board LED 07", "12 - Set On-board LED 08", "13 - Set On-board LED 09",
                "14 - Set On-board LED 10", "15 - Set On-board LED 11", "16 - Set On-board LED 12",
                "17 - Set On-board LED 13", "18 - Set On-board LED 14", "19 - Set On-board LED 15",
                "20 - Set On-board LED 16", "21 - Set On-board LED 17", "22 - Set On-board LED 18",
                "23 - Set On-board LED 19", "24 - Set On-board LED 20",
                "25 - Set Slave-board LED 01 ", "26 - Set Slave-board LED 02 ", "27 - Set Slave-board LED 03 ",
                "28 - Set Slave-board LED 04 ", "29 - Set Slave-board LED 05 ", "30 - Set Slave-board LED 06 ",
                "31 - Set Slave-board LED 07 ", "32 - Set Slave-board LED 08 ", "33 - Set Slave-board LED 09 ",
                "34 - Set Slave-board LED 10 ", "35 - Set Slave-board LED 11 ", "36 - Set Slave-board LED 12 ",
                "37 - Set Slave-board LED 13 ", "38 - Set Slave-board LED 14 ", "39 - Set Slave-board LED 15 ",
                "40 - Set Slave-board LED 16 ", "41 - Set Slave-board LED 17 ", "42 - Set Slave-board LED 18 ",
                "43 - Set Slave-board LED 19 ", "44 - Set Slave-board LED 20 "
                ]

directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "vpc-led"))
filepath = os.path.join(directory, "VPC_LED_Control.exe")


def set_color(vid, pid, command, hex_color):
    cmd = commands(command)
    hex_color_red = hex_color[:2]
    hex_color_green = hex_color[2:4]
    hex_color_blue = hex_color[4:6]
    run = f"{filepath} {vid} {pid} {cmd} {hex_color_red} {hex_color_green} {hex_color_blue}"
    subprocess.run(run)
    return True


def commands(command):
    cmd = command[:2]
    return cmd


if __name__ == "__main__":
    # test from here
    set_color("3344", "8130", "01", "408000")
