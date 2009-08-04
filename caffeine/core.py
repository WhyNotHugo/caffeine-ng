
import gtk
import gobject
import os
import pynotify

import dbus
import threading

import caffeine

## TODO: These variables should be defined in on place for the 
## whole program.

class Caffeine(gobject.GObject):

    def __init__(self):
        
        gobject.GObject.__init__(self)

        self.sleepPrevented = False
        self.screenSaverCookie = None
        self.powerManagementCookie = None
        self.timer = None
    
    ### This stuff is hard to follow, it needs some comments - Isaiah H.
    def mconcat(self, base, sep, app):
        return (base + sep + app if base else app) if app else base

    def spokenConcat(self, ls):
        txt, n = '', len(ls)
        for w in ls[0:n-1]:
            txt = self.mconcat(txt, ', ', w)
        return self.mconcat(txt, ' and ', ls[n-1])

    def decline(self, name, nb):
        plural = ('s' if nb > 1 and nb != 0 else '')
        return ('%d %s%s' % (nb, name, plural) if nb >= 1 else '')

    def timeDisplay(self, sec):
        names = ['hour', 'minute', 'second']
        tvalues = sec/3600, sec/60 % 60, sec % 60
        ls = list(self.decline(name, n) for name, n in zip(names, tvalues))
        return self.spokenConcat(ls)


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

    def timedActivation(self, time):
        """Calls toggleActivated after the number of seconds
        specified by time has passed.
        """
        message = ("Timed activation set; "+
            "Caffeine will prevent powersaving for the next " +
            self.timeDisplay(time))

        self.notify(message, caffeine.FULL_ICON_PATH)
        
        ## activate
        if not self.getActivated():
            self.toggleActivated()
        
        ## and deactivate after time has passed.
        self.timer = threading.Timer(time, self.toggleActivated)
        self.timer.start()


    def toggleActivated(self, busFailures=0):
        print "toggleActivated"
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

                message = ("Timed activation cancelled (was set for " +
                        self.timeDisplay(self.timer.interval) + ")")

                self.notify(message, caffeine.EMPTY_ICON_PATH)
                self.timer.cancel()
                self.timer = None

            elif self.timer != None and self.timer.name == "Expired":

                message = (self.timeDisplay(self.timer.interval) + 
                    " have elapsed; powersaving is re-enabled")

                self.notify(message, caffeine.EMPTY_ICON_PATH)
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


## register a signal
gobject.signal_new("activation-toggled", Caffeine,
        gobject.SIGNAL_RUN_FIRST, None, [bool])


