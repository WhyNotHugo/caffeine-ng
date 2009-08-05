#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2009 The Caffeine Developers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import os.path
import time
 
 
#class used to handle one application instance mechanism
class ApplicationInstance:
 
	#specify the file used to save the application instance pid
	def __init__( self, pid_file ):
		self.pid_file = pid_file
		self.check()
		self.startApplication()
 
	#check if the current application is already running
	def check( self ):
		#check if the pidfile exists
		if not os.path.isfile( self.pid_file ):
			return
 
		#read the pid from the file
		pid = 0
		try:
			file = open( self.pid_file, 'rt' )
			data = file.read()
			file.close()
			pid = int( data )
		except:
			pass
 
		#check if the process with specified by pid exists
		if 0 == pid:
			return
 
		try:
			os.kill( pid, 0 )	#this will raise an exception if the pid is not valid
		except:
			return
 
		#exit the application
		print "The application is already running !"
		exit(0) #exit raise an exception so don't put it in a try/except block
 
	#called when the single instance starts to save it's pid
	def startApplication( self ):
		file = open( self.pid_file, 'wt' )
		file.write( str( os.getpid() ) )
		file.close()
 
	#called when the single instance exit ( remove pid file )
	def exitApplication( self ):
		try:
			os.remove( self.pid_file )
		except:
			pass
