#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#####################################################################
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Ky�stil�                                  #
#                                                                   #
# This program is free software; you can redistribute it and/or     #
# modify it under the terms of the GNU General Public License       #
# as published by the Free Software Foundation; either version 2    #
# of the License, or (at your option) any later version.            #
#                                                                   #
# This program is distributed in the hope that it will be useful,   #
# but WITHOUT ANY WARRANTY; without even the implied warranty of    #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the     #
# GNU General Public License for more details.                      #
#                                                                   #
# You should have received a copy of the GNU General Public License #
# along with this program; if not, write to the Free Software       #
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,        #
# MA  02110-1301, USA.                                              #
#####################################################################

"""
Main game executable.
"""

# Register the latin-1 encoding
import codecs
import encodings.iso8859_1
import encodings.utf_8
codecs.register(lambda encoding: encodings.iso8859_1.getregentry())
codecs.register(lambda encoding: encodings.utf_8.getregentry())
assert codecs.lookup("iso-8859-1")
assert codecs.lookup("utf-8")

from GameEngine import GameEngine
from MainMenu import MainMenu
import Log
import Config
import Version

import getopt
import sys
import os
import codecs
import Resource

usage = """%(prog)s [options]
Options:
  --verbose, -v                     Verbose messages
  --debug,   -d                     Write Debug file
  --config=, -c [configfile]        Use this instead of fretsonfire.ini
  --play=,   -p [SongDir]           Play a song from the commandline
  --diff=,   -D [difficulty number] Use this difficulty
  --part=,   -P [part number]       Use this part
""" % {"prog": sys.argv[0] }

if __name__ == "__main__":
  try:
    opts, args = getopt.getopt(sys.argv[1:], "vdc:p:D:P:", ["verbose", "debug", "config=", "play=", "diff=", "part="])
  except getopt.GetoptError:
    print usage
    sys.exit(1)
    
  playing = None
  configFile = None
  debug = False
  difficulty = 0
  part = 0
  for opt, arg in opts:
    if opt in ["--verbose", "-v"]:
      Log.quiet = False
    if opt in ["--debug", "-d"]:
      debug = True
    if opt in ["--config", "-c"]:
      configFile = arg
    if opt in ["--play", "-p"]:
      playing = arg
    if opt in ["--diff", "-D"]:
      difficulty = arg      
    if opt in ["--part", "-P"]:
      part = arg
      
  while True:
    if configFile != None:
      if configFile.lower() == "reset":
        fileName = os.path.join(Resource.getWritableResourcePath(), Version.appName() + ".ini")
        os.remove(fileName)
        config = Config.load(Version.appName() + ".ini", setAsDefault = True)
      else:
        config = Config.load(configFile, setAsDefault = True)
    else:
      config = Config.load(Version.appName() + ".ini", setAsDefault = True)
    engine = GameEngine(config)
    engine.cmdPlay = 0
    
    if playing != None:
      Config.set("game", "selected_library", "songs")
      Config.set("game", "selected_song", playing)
      engine.cmdPlay = 1
      engine.cmdDiff = int(difficulty)
      engine.cmdPart = int(part)

    if debug == True:
      engine.setDebugModeEnabled(not engine.isDebugModeEnabled())
      engine.debugLayer.debugOut(engine)
      engine.quit()
      break
      
    encoding = Config.get("game", "encoding")
    if encoding != None:
      reload(sys)
      sys.setdefaultencoding(encoding)
    engine.setStartupLayer(MainMenu(engine))

    try:
      import psyco
      psyco.profile()
    except:
      Log.warn("Unable to enable psyco.")

    try:
      while engine.run():
        pass
    except KeyboardInterrupt:
        pass
    if engine.restartRequested:
      Log.notice("Restarting.")
      engine.audio.close()
      try:
        # Determine whether were running from an exe or not
        if hasattr(sys, "frozen"):
          if os.name == "nt":
            os.execl("FretsOnFire.exe", "FretsOnFire.exe", *sys.argv[1:])
          else:
            os.execl("./FretsOnFire", "./FretsOnFire", *sys.argv[1:])
        else:
          if os.name == "nt":
            bin = "c:/python24/python"
          else:
            bin = "/usr/bin/python"
          os.execl(bin, bin, "FretsOnFire.py", *sys.argv[1:])
      except:
        Log.warn("Restart failed.")
        raise
      break
    else:
      break
  engine.quit()
