import time

from swtools import SwtoolsError, swtools


class yos_device:
    def __init__(self, swt: swtools = swtools()):
        self.swt = swt  # swtools instance

    def save(self):
        # save and return hash
        return self.swt.cmd(["save", "-y"])

    def save_b(self):
        return self.swt.cmd(["save", "-yb"])

    def load_b(self):
        return self.swt.cmd(["load", "-yb"])

    def load(self):
        return self.swt.cmd(["load", "-y"])

    def shutdown(self):
        return self.swt.cmd(["shutdown"], asyn=True)

    def set_addr(self, addr):
        self.swt.cmd(["setaddr", "-y", str(addr)])
        return True

    def get_addr(self):
        return self.swt.cmd(["version", "-a"])

    def restore(self):
        return self.swt.cmd(["restore", "-y"])

    def hash(self):
        return self.swt.cmd(["save", "-d"])

    def reset(self):
        self.swt.yosctl(["pwr", "reboot", "single"])

    def isbl(self):
        # is bootloader
        return self.swt.yosctl_parse(["id", "parse", "app"])

    def swt(self) -> swtools:
        return self.swt

    def set_var(self, var, value):
        var = str(var)
        value = str(value)
        data = ["var", "set", var, value]
        if self.swt.yosctl_check(data, attempts=4):
            raise SwtoolsError("Param set fail: {}".format(var))
        else:
            return

    def get_var(self, var, intt=True):
        # intt = return integer, not float
        # co kdyz je to pole?
        var = str(var)
        data = ["var", "get", var]
        ret = self.swt.yosctl_parse(data, attempts=4)

        try:
            x = ret.split(",")[0]
            x = float(x)
            if intt:
                return int(x)
            else:
                return x

        except IndexError:
            raise SwtoolsError("Yosctl get var |{}| - index error: {}".format(var, ret))
        except ValueError:
            raise SwtoolsError(
                "Yosctl get var |{}| - is not digit: {}".format(var, ret)
            )

    def set_msgconf(self, interface="", option="-1"):
        try:
            option = int(option)
            if interface:
                interface = int(interface)  # to check if it is a digit
                opt = [str(interface), str(option)]
            else:
                opt = [str(option)]

            return self.swt.cmd(["msgconf", "-y", *opt])
        except ValueError:
            raise SwtoolsError(
                "Msgconf error, interface: {}, options: {}".format(interface, option)
            )

    def get_msgconf(self, interface):
        interface = str(interface)
        if interface.isdigit():
            return str(self.swt.cmd(["msgconf", str(interface)]))
        print("Msgconf error, interface: {}".format(interface))
        return

    def get_sn(self):
        sn = self.swt.yosctl_parse(["id", "parse", "sn"], attempts=2)

        if not sn:
            return
        sn = str(sn)
        sn = sn.strip()

        if 10 > len(sn):
            print("SN is to short - " + sn)
            return
        return sn

    def get_uuid(self):
        uuid = self.swt.yosctl_parse(["id", "info", "uuid"], attempts=2)

        if not uuid:
            return 0
        uuid = str(uuid)
        uuid = uuid.strip()

        return uuid

    def default_hash(self):
        self.restore()
        hash = self.hash()
        self.load()
        return hash

    def get_swid(self):
        return self.swt.yosctl_parse(["id", "info", "swid"], attempts=2)

    def is_vector(self):
        if self.get_swid().split("_")[0] == "VECTOR":
            return 1
        else:
            return 0

    def get_basename(self):
        return self.swt.yosctl_parse(["id", "info", "name"], attempts=2)

    def get_hwid(self):
        return self.swt.yosctl_parse(["id", "info", "hwid"], attempts=2)

    def login(self):
        # If not succesfull, raise exception
        self.swt.login()

    def is_NOT_on(self, fast=False):
        # Check if controller is connected
        ex = 0
        for x in range(15):
            isbl = 1
            try:
                self.swt.claim()
                isbl = int(self.isbl())
            except SwtoolsError:
                ex += 1
            if isbl == 0:
                time.sleep(0.1)
                return 0
            time.sleep(0.1)
            if ex > 13:
                return 1
            if ex > 1 and fast:
                return 1
            if x == 6:  # reset and try again
                self.reset()
                time.sleep(2)

        return 1
