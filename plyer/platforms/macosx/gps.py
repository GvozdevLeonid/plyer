from pyobjus.dylib_manager import load_framework
from threading import Thread
from multiprocessing import (
    Process,
    Pipe,
)
from pyobjus import (
    autoclass,
    protocol,
)

load_framework('/System/Library/Frameworks/CoreLocation.framework')
load_framework('/System/Library/Frameworks/Foundation.framework')
CLLocationManager = autoclass('CLLocationManager')
NSRunLoop = autoclass('NSRunLoop')


class GPS:
    '''
    GPS facade.
    '''

    def configure(self, on_location, on_status=None):
        '''
        Configure the GPS object. This method should be called before
        :meth:`start`.

        :param on_location: Function to call when receiving a new location
        :param on_status: Function to call when a status message is received
        :type on_location: callable, multiples keys/value will be passed.
        :type on_status: callable, args are "message-type", "status"

        .. warning::

            The `on_location` and `on_status` callables might be called from
            another thread than the thread used for creating the GPS object.
        '''
        self.on_location = on_location
        self.on_status = on_status
        self._configure()

    def start(self, minTime=1000, minDistance=1):
        '''
        Start the GPS location updates.
        Expects 2 parameters:
            minTime: milliseconds.  (float)
            minDistance: meters. (float)
        '''
        self._start(minTime=minTime, minDistance=minDistance)

    def stop(self):
        '''
        Stop the GPS location updates.
        '''
        self._stop()

    # private

    def _configure(self):
        raise NotImplementedError()

    def _start(self, **kwargs):
        raise NotImplementedError()

    def _stop(self):
        raise NotImplementedError()


class LocationManager:
    def _run_location_manager(connection, **kwargs):
        LocationManager(connection).start(**kwargs)

    def __init__(self, pipe) -> None:
        self.pipe = pipe
        self._location_manager = CLLocationManager.alloc().init()

    def start(self, **kwargs):
        self._location_manager.setDelegate_(self)
        self._location_manager.requestWhenInUseAuthorization()
        self._location_manager.startUpdatingLocation()
        NSRunLoop.currentRunLoop().run()

    def stop(self):
        self._location_manager.stopUpdatingLocation()

    @protocol('CLLocationManagerDelegate')
    def locationManager_didChangeAuthorizationStatus_(self, manager, status):
        s_status = ''
        provider_status = ''
        provider = 'standard-macos-provider'
        if status == 0:
            provider_status = 'provider-disabled'
            s_status = 'notDetermined'
        elif status == 1:
            provider_status = 'provider-enabled'
            s_status = 'restricted'
        elif status == 2:
            provider_status = 'provider-disabled'
            s_status = 'denied'
        elif status == 3:
            provider_status = 'provider-enabled'
            s_status = 'authorizedAlways'
        elif status == 4:
            provider_status = 'provider-enabled'
            s_status = 'authorizedWhenInUse'

        self.pipe.send({'on_status': (provider_status, '{}: {}'.format(provider, s_status))})

    @protocol('CLLocationManagerDelegate')
    def locationManager_didUpdateLocations_(self, manager, locations):
        location = manager.location

        description = location.description().UTF8String()
        split_description = description.split('<')[-1].split('>')[0].split(',')

        lat, lon = [float(coord) for coord in split_description]
        acc = float(description.split(' +/- ')[-1].split('m ')[0])

        speed = location.speed
        altitude = location.altitude
        course = location.course

        self.pipe.send({'on_location': {'lat': lat, 'lon': lon, 'speed': speed, 'course': course, 'altitude': altitude, 'acc': acc}})


class OSXGPS(GPS):
    def _configure(self):
        self._connection_1, self._connection_2 = Pipe()
        self._process = Process(target=LocationManager._run_location_manager, args=[self._connection_2])
        self._thread = Thread(target=self._run_thread_pipe_checker)

    def _start(self, **kwargs):
        self._process.start()
        self._thread.start()

    def _stop(self, **kwargs):
        self._process.kill()

    def _run_thread_pipe_checker(self):
        while self._process.is_alive():
            if self._connection_1.poll(.1):
                callback = self._connection_1.recv()
                if 'on_status' in callback and self.on_status:
                    self.on_status(*callback['on_status'])
                elif 'on_location' in callback:
                    self.on_location(**callback['on_location'])


def instance():
    return OSXGPS()
