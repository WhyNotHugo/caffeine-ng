#!/usr/bin/env python

import xml.etree.ElementTree as xml
import commands


version = open("VERSION").readline().strip()
print version
revno = int(commands.getoutput("bzr revno lp:caffeine"))
revno += 1
revno = str(revno)
print revno

glade_file = "share/caffeine/glade/GUI.glade"

tree = xml.parse(glade_file)

rootElement = tree.getroot()

for elem in rootElement:
    
    if elem.get("id") == "aboutdialog":

        for child in elem:
            if child.get("name") == "version":

                child.text = version+" (bzr "+revno+")"


tree.write(glade_file)
