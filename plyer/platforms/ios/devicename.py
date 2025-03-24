'''
Module of macOS API for plyer.devicename.
'''

from pyobjus import autoclass
from pyobjus.dylib_manager import load_framework

from plyer.facades import DeviceName

load_framework('/System/Library/Frameworks/UIKit.framework')


class IosDeviceName(DeviceName):
    '''
    Implementation of IOS DeviceName API.
    '''

    def _get_device_name(self):
        UIDevice = autoclass('UIDevice')
        device = UIDevice.currentDevice()
        device_name = device.name.UTF8String()
        return device_name


def instance():
    '''
    Instance for facade proxy.
    '''
    return IosDeviceName()
