#!/usr/bin/env python

import kaa.metadata
import commands
import sys

if __name__ == "__main__":

    try:
        output = commands.getoutput("pgrep -f flashplayer | xargs -I PID find /proc/PID/fd -lname '/tmp/Flash*'")
        if not bool(output):
            print 1
            sys.exit(1)
        for filepath in output.split("\n"):
            if filepath != "":
                meta = kaa.metadata.parse(filepath)
                url = meta.url
                length = meta.length
                print url[7:]+" "+str(length).split(".")[0]

    except Exception, data:
        print 1
        sys.exit(1)
