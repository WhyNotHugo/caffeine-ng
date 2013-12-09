import kaa.metadata
import commands
import sys
import os
import stat

if __name__ == "__main__":

    try:
        output = commands.getoutput("pgrep -f flashplayer | xargs -I PID find /proc/PID/fd -lname '/tmp/Flash*'")
        if not bool(output):
            print 1
            sys.exit(1)

        for filepath in output.split("\n"):
            if filepath != "":
                meta = kaa.metadata.parse(filepath)
                url = meta.url[7:]
                length = str(meta.length)
                iden = str(os.stat(url).st_ino) + length
                print iden+" "+length.split(".")[0]

    except Exception, data:
        print 2
        print data
        sys.exit(2)
