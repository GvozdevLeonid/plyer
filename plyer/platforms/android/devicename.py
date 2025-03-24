'''
Module of Android API for plyer.devicename.
'''

from jnius import autoclass
from plyer.facades import DeviceName


class AndroidDeviceName(DeviceName):
    '''
    Implementation of Android devicename API.
    '''

    def _get_device_name(self):
        """
        Method to get the device name aka model in an android environment.

        Changed the implementation from 'android.provider.Settings.Global' to
        'android.os.Build' because 'android.provider.Settings.Global' was
        introduced in API 17 whereas 'android.os.Build' is present since API 1

        Thereby making this method more backward compatible.
        """

        Build = autoclass('android.os.Build')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        SettingsGlobal = autoclass('android.provider.Settings$Global')

        context = PythonActivity.mActivity
        name = SettingsGlobal.getString(context.getContentResolver(), SettingsGlobal.DEVICE_NAME)

        if not name:
            name = Build.MODEL

        return name


def instance():
    '''
    Instance for facade proxy.
    '''
    return AndroidDeviceName()
