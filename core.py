
import gtk
import pynotify

import dbus
import threading

class Caffeine(object):

    def __init__(self):
        
        self.sleepPrevented = False
        self.screenSaverCookie = None
        self.powerManagementCookie = None
        self.timer = None
    

    def notify(self, message, icon, title="Caffeine"):
        """Easy way to use pynotify"""
        try:
            pynotify.init("Caffeine")
            n = pynotify.Notification(title, message, icon)
            n.show()
        except:
            print "Exception occurred"
            print message


    def getActivated(self):
        return self.sleepPrevented

    def toggleActivated(self, busFailures=0):
        attemptResult = self._toggleActivated()
        if attemptResult == False:
            busFailures += 1
            if busFailures < 12:
                print "Failed to establish a connection with a required bus (" + str(busFailures) + " failures so far)"
                print "This may be due to the required subsystem not having completed its initialization. Will try again in 10 seconds."
                failTimer = threading.Timer(10, self.toggleActivated,
                        args=[busFailures])
                failTimer.start()
            else:
                print "Could not connect to the bus, even after repeated attempts. This program will now terminate."
                errMsg = "Error: couldn't find bus to allow inhibiting of the screen saver.\n\n" \
                    "Please visit the web-site listed in the 'About' dialog of this application " \
                    "and check for a newer version of the software."
                errDlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=errMsg)
                errDlg.run()
                errDlg.destroy()
                sys.exit(2)
        else:
            if busFailures != 0:
                print "Connection to the bus succeeded; resuming normal operation"


    def _toggleActivated(self):
        """This function may fail to peform the toggling,
        if it cannot find the required bus. In this case, it
        will return False."""

        bus = dbus.SessionBus()

        ssProxy = None
        pmProxy = None
        bus_names = bus.list_names()

        probableWindowManager = ""
        # For Gnome
        if 'org.gnome.ScreenSaver' in bus_names:
            ssProxy = bus.get_object('org.gnome.ScreenSaver',
                    '/org/gnome/ScreenSaver')

            probableWindowManager = "Gnome"

        # For KDE
        elif ('org.freedesktop.ScreenSaver' in bus_names and
            'org.freedesktop.PowerManagement.Inhibit' in bus_names):

            ssProxy = bus.get_object(
                    'org.freedesktop.ScreenSaver',
                    '/ScreenSaver')

            pmProxy = bus.get_object(
                    'org.freedesktop.PowerManagement.Inhibit',
                    '/org/freedesktop/PowerManagement/Inhibit')

            probableWindowManager = "KDE"
        else:
            print 111
            return False

        if self.sleepPrevented:
            
            if self.screenSaverCookie != None:
                ssProxy.UnInhibit(self.screenSaverCookie)

            self.sleepPrevented = False
            print "Caffeine is now dormant; powersaving is re-enabled"

            # If the user clicks on the full coffee-cup to disable 
            # sleep prevention, it should also
            # cancel the timer for timed activation.

            if self.timer != None and self.timer.name != "Expired":

                self.notify(message, EMPTY_ICON_PATH)
                self.timer.cancel()
                self.timer = None

            elif self.timer != None and self.timer.name == "Expired":

                self.notify(message, EMPTY_ICON_PATH)
                self.timer = None
        else:

            if pmProxy:
                powerManagementCookie = pmProxy.Inhibit("Caffeine",
                    "User has requested that Caffeine disable"+
                    " the powersaving modes")

            self.screenSaverCookie = ssProxy.Inhibit("Caffeine",
                "User has requested that Caffeine disable the screen saver")

            self.sleepPrevented = True
            print ("Caffeine is now preventing powersaving modes"+
                " and screensaver activation (" +
                probableWindowManager + ")")

        return True


