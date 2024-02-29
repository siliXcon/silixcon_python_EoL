import ctypes
import os
import subprocess
import time
from pathlib import Path
from subprocess import DEVNULL, PIPE


def run_no_output(command):
    cmd = subprocess.run(command, stdout=PIPE, stderr=PIPE)
    return cmd


def run_ret_output(command):
    cmd = subprocess.run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    return cmd


def run_std(command):
    cmd = subprocess.run(command, stderr=PIPE, universal_newlines=True)
    ret = ctypes.c_int32(cmd.returncode).value

    if (
        len(str(cmd.stdout)) < 2
    ):  # Asi fail, protoze chci stdout, a ten neni, tak vypisu i stderr
        print("FAIL")
        print(cmd.stderr)
        print(cmd.stdout)
        print("^^ return code: {}".format(ret), False)
    else:
        print("^^ return code: {}".format(ret), False)
    return ret


def run_check(command, ret_val=0, stdin=None):
    # spusti cmd a vypise stdout pouze pokud navratova hodnota se nerovna ocekavane
    # If ok, return false
    # If NOT ok return true
    cmd = subprocess.run(
        command, stdout=PIPE, stderr=PIPE, input=stdin, universal_newlines=True
    )

    ret = ctypes.c_int32(cmd.returncode).value

    if ret_val == ret:
        return False
    else:
        print("FAIL")
        print(str(command))
        if len(cmd.stdout) < 2:
            print(cmd.stderr)
        else:
            print(cmd.stdout)
        print("^^ return code: {}, expected: {}".format(ret, ret_val), False)
        return True


def run_ch(command, ret_val):
    # spusti cmd a vypise stdout pouze pokud navratova hodnota se nerovna ocekavane
    # return true - ok /false
    process = subprocess.Popen(command, stdout=PIPE, universal_newlines=True)
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            print("done cmd")
            break
        if output:
            print(output.strip())
    ret = process.poll()
    ret = ctypes.c_int32(ret).value
    return ret


class SwtoolsError(Exception):
    pass


SWTOOL_VERBOSITY_NONE = "0"
SWTOOL_DEBUG_NONE = "0"


def get_swtools_path():
    # where term
    try:
        result = subprocess.run(
            ["where", "term"],
            universal_newlines=True,
            stderr=DEVNULL,
            stdout=PIPE,
            shell=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        raise SwtoolsError("Unable to find term")
    path = result.stdout
    path = Path(os.path.dirname(os.path.dirname(path)))
    if not path.exists():
        raise SwtoolsError("Unable to find swtools: {}".format(path))
    return path


def interface_valid(interface):
    valid_interfaces = ["usb", "kvaser", "dmsg", "umsg", "usbdk", ""]
    if interface in valid_interfaces:
        return interface
    else:
        raise SwtoolsError("Unknown interface: {}".format(interface))


# Conver interfaces in str to numbers
def convert_if_to_num(interface: str):
    if interface == "usb":
        return 7
    elif interface == "kvaser":
        return 3
    elif interface == "umsg":
        return 1
    return None


# Function to convert string like this: "3:8,0,4;1:0" into dict like this: {"3": "8, 0, 4", "1" : "0"}
def parse_msgconf_from_string(conf: str):
    if not conf:
        return {}
    conf = conf.replace(" ", "")
    if conf == "-1":
        return {}
    can_meta_dict = {}
    for item in conf.split(";"):
        if item:
            key, value = item.split(":")
            can_meta_dict[key] = value
    return can_meta_dict


class swtools_connection_options:
    def __init__(
        self,
        interface: str = "",
        addr: str = "",
        msgconf_str: str = "",
        sw_path: str = get_swtools_path(),
    ) -> None:
        if interface:
            interface_valid(interface)
        self.interface = interface
        self.addr = addr
        self.msgconf = parse_msgconf_from_string(msgconf_str)
        self.sw_path = sw_path

    def set_if(self, interface: str):
        interface_valid(interface)
        self.interface = interface

    def __str__(self) -> str:
        return f"""
                Interface: {self.interface}, Addr: {self.addr}, Msgconf: {self.msgconf}\n
                Options: {self.get_if()}
                """

    def update_msgconf(self, msgconf_str: str):
        self.msgconf.update(parse_msgconf_from_string(msgconf_str))

    def get_if(self) -> list:
        # return list
        # -i - interface options
        # -o - opts
        # -a - address
        # - l - local
        # - m - mesh

        ret = list()
        if self.interface:
            ret.append("-i{}\\if\\msg_{}.dll".format(self.sw_path, self.interface))

            opt = self.msgconf.get(str(convert_if_to_num(self.interface)))

            if opt is not None:
                if self.interface == "kvaser":
                    opt = "0," + opt
                ret.append("-o" + opt)
            else:
                ret.append("-o0")

        if self.addr:
            ret.append("-a" + self.addr)
        ret.append("-l7")  # local 7
        # ret.append("-m0")  # mesh 0

        return ret


# ################# CLASSES ##################
class swtools:
    def __init__(
        self,
        conn: swtools_connection_options = swtools_connection_options(),
        swtools_verbosity=SWTOOL_VERBOSITY_NONE,
        swtools_debug_lvl=SWTOOL_DEBUG_NONE,
        tm=time,
    ):
        # interface = yOS device interface
        self.conn = conn
        self.swtools_verbosity = str(swtools_verbosity)  # verbosity level
        self.swtools_debug_lvl = str(swtools_debug_lvl)  # debug level
        self.tm = tm
        self.claim()

    def __str__(self):
        return f"Swtools:\n{self.conn.interface} \n{self.conn}, Option str: {self.get_options()}"

    def get_options(self):
        ret = list()
        if self.conn:
            ret = self.conn.get_if()

        ret.append("-v" + self.swtools_verbosity)
        ret.append("-z" + self.swtools_debug_lvl)
        return ret

    def srm_upgrade(self, swid=""):
        return run_no_output(
            [
                "srm.cmd",
                "-s" + globals.INTRANET_URL,
                *self.get_options(),
                "UPGRADE:{}".format(swid),
            ]
        )

    def login(self):
        # login everywhere to controller
        # return true if ok
        file = "login.ys"
        path = file
        command = ("term.cmd", *self.get_options(), path)

        x = 0
        while run_check(command, ret_val=123):
            x += 1
            print("Term login fail, trying again..")
            if x > 4:
                raise SwtoolsError("Term login failed")
            self.sleep(0.5)
        command = ("yosctl.cmd", *self.get_options(), "var", "login")
        if run_check(command, ret_val=0):
            raise SwtoolsError("Yosctl var login login failed")
        command = ("yosctl.cmd", *self.get_options(), "cmd", "login")
        if run_check(command, ret_val=0):
            raise SwtoolsError("Yosctl var login login failed")

        return 1

    def yosctl_ret_std(self, data, check=True):
        cmd = ["yosctl.cmd", *self.get_options(), *data]
        ret = run_ret_output(cmd)

        if ret.returncode and check:
            raise SwtoolsError(
                "Yosctl std error, ret_val: {}, cmd:{}".format(
                    ret.returncode, str(data)
                )
            )

        return ret.stdout

    def yosctl_parse(self, data=["id", "info", "name"], attempts=1):
        # sn, app, id, info, name, hwid
        # return last line of stdout
        cmd = ["yosctl.cmd", *self.get_options(), *data]
        for x in range(attempts):
            ret = run_ret_output(cmd)
            if not ret.returncode:
                if x:
                    print("No. attempts: {}".format(x))
                break

        if ret.returncode:
            raise SwtoolsError(
                "Yosctl error, ret_val: {}, cmd:{}, attempts {}".format(
                    ctypes.c_int32(ret.returncode).value, str(data), x
                )
            )

        result = ret.stdout.split("\n")
        # Pokud je zapnuty debug, tak v nekterych pripadech to co chceme neni na posledni radce
        if (result[-2][0]) == "[":
            result = result[-3]
        else:
            result = result[-2]

        result = result.strip()
        return result

    def get_vars_from_list(self, vars_list):
        # go trough list of vars and fetch them from device, return dictionary
        out = dict()
        for var in vars_list:
            out = {**out, **self.get_vars(var)}
        return out

    def get_vars(self, prefix="/vars/o_"):
        # get variables from controler folder and store them to dictionary
        #
        out = dict()

        if not prefix:
            return out

        cmd = [
            "yosctl.cmd",
            *self.get_options(),
            "var",
            "pull",
            "-Tall",
            "-h",
            "-",
            f"{prefix}",
        ]
        vars = run_ret_output(cmd).stdout
        vars = vars.split("\n")

        x = ""
        for var in vars:
            x = var.split(":")
            if type(x) is list and len(x) == 2:
                out.update({x[0].strip('" '): x[1].strip('" ')})
        return out

    def script_check(self, file, ret_val=0):
        path = file
        command = ("term.cmd", *self.get_options(), path)
        return run_check(command, ret_val)

    def script_std(self, file):
        path = file
        command = ("term.cmd", *self.get_options(), path)
        return run_std(command)

    def yosctl(self, cmd):
        cmd = list(map(str, cmd))
        command = ("yosctl.cmd", *self.get_options(), *cmd)
        ret = run_no_output(command).returncode
        ret = ctypes.c_int32(ret).value
        return ret

    def yosctl_check(self, cmd, ret_val=0, attempts=1):
        command = ("yosctl.cmd", *self.get_options(), *cmd)
        for x in range(attempts):
            ret = run_check(command, ret_val)
            if ret == ret_val:
                if x:
                    print("No. attempts: {}".format(x))
                return
        return 1

    def claim(self):
        # po zmene interface zavolat
        command = ["yosctl.cmd", *self.get_options(), "if", "claim"]
        ret = run_no_output(command).returncode
        ret = ctypes.c_int32(ret).value
        return ret

    def yosctl_push(self, file="", stdin=None):
        # true = error
        cmd = ["yosctl.cmd", *self.get_options(), "var", "push"]

        if file:
            if not os.path.isfile(file):
                raise SwtoolsError("Config is not file: {}".format(file))

            # download configuration file from controller
            cmd.append(file)

        return run_check(cmd, 0, stdin)

    def yosctl_pull(self, file="", non_default_values=False, type=""):
        # true = error
        # download configuration file from controller

        cmd = ["yosctl.cmd", *self.get_options(), "var", "pull", "-h"]
        if non_default_values:
            cmd.append("-d")
        if type:
            cmd.append(f"-T{str(type)}")
        if file:
            cmd.append(file)
        out = run_ret_output(cmd)

        if out.returncode:
            raise SwtoolsError(f"Yosctl pull end with error: {out.returncode}")
        return out.stdout

    def yosctl_cmd_exec(self, cmd=[]):
        out = ["yosctl.cmd", *self.get_options(), "cmd", "exec"]
        if cmd is type(list):
            out.extend(cmd)
        else:
            out.append(str(cmd))

        return run_ret_output(out)

    def cmd(self, cmd, exit_code=12345, asyn=False):
        if cmd is not list:
            cmd = list(cmd)
        cmd = list(map(str, cmd))

        if exit_code:
            cmd = ["-r{}".format(exit_code), *cmd]
        if asyn:
            cmd = ["-b", *cmd]

        command = ("yosctl.cmd", *self.get_options(), "cmd", "exec", *cmd)

        retval = run_no_output(command)
        ret = retval.returncode
        ret = ctypes.c_int32(ret).value

        if ret == int(exit_code):
            print("Yosctl failed! cmd: {}, ret: {}".format(str(cmd), ret))
            print(("Stderr:"))
            print(str(retval.stderr))
            print(("Stdout:"))
            print(str(retval.stdout))
            # input("Zmackni cokoli pro pokracovani")
            raise SwtoolsError("Yosctl failed! cmd: {}, ret: {}".format(str(cmd), ret))
        return ret


def resetconn():
    subprocess.run(
        ["resetconn"], stdout=DEVNULL, stderr=DEVNULL, check=False, shell=True
    )
