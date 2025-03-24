'''
Module of MacOSX API for plyer.devicename.
'''

from pyobjus import autoclass
from pyobjus.dylib_manager import INCLUDE, load_framework

from plyer.facades import DeviceName

load_framework(INCLUDE.Foundation)


class OSXDeviceName(DeviceName):
    '''
    Implementation of MacOSX DeviceName API.
    '''

    def _get_device_name(self):
        NSHost = autoclass('NSHost')
        current_host = NSHost.currentHost()
        name = current_host.localizedName.UTF8String()
        return name


def instance():
    '''
    Instance for facade proxy.
    '''
    return OSXDeviceName()
