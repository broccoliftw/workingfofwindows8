#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
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

from Scene import SceneServer, SceneClient
import Player
import Dialogs
import Song
import Config
from Language import _

import os
# save chosen song into config file
Config.define("game", "selected_library",  str, "")
Config.define("game", "selected_song",     str, "")

class SongChoosingScene:
  pass

class SongChoosingSceneServer(SongChoosingScene, SceneServer):
  pass

class SongChoosingSceneClient(SongChoosingScene, SceneClient):
  def createClient(self, libraryName = None, songName = None):
    self.wizardStarted = False
    self.libraryName   = libraryName
    self.songName      = songName

  def freeResources(self):
    self.songs = None
    self.cassette = None
    self.folder = None
    self.label = None
    self.song = None
    self.background = None
    
  def run(self, ticks):
    SceneClient.run(self, ticks)
    players = 1

    if not self.wizardStarted:
      self.wizardStarted = True


      if self.engine.cmdPlay == 1:
        self.songName = Config.get("game", "selected_song")
        self.libraryName = Config.get("game", "selected_library")
        self.engine.cmdPlay = 2
        
      if not self.songName:
        while True:
          self.libraryName, self.songName = \
            Dialogs.chooseSong(self.engine, \
                               selectedLibrary = Config.get("game", "selected_library"),
                               selectedSong    = Config.get("game", "selected_song"))

          if self.libraryName == None:
            newPath = Dialogs.chooseFile(self.engine, masks = ["*/songs"], prompt = _("Choose a new songs directory."), dirSelect = True)
            if newPath != None:
              Config.set("game", "base_library", os.path.dirname(newPath))
              Config.set("game", "selected_library", "songs")
              Config.set("game", "selected_song", "")
            
          if not self.songName:
            self.session.world.finishGame()
            return

          Config.set("game", "selected_library", self.libraryName)
          Config.set("game", "selected_song",    self.songName)
          
          info = Song.loadSongInfo(self.engine, self.songName, library = self.libraryName)

          selected = False
          escape = False
          escaped = False
          while True:
            if len(info.parts) > 1:
              p = Dialogs.chooseItem(self.engine, info.parts, "%s \n %s" % (info.name, _("Player 1 Choose a part:")), selected = self.player.part)
            else:
              p = info.parts[0]
            if p:
              self.player.part = p
            else:
              break;
            while True:
              if len(info.difficulties) > 1:
                d = Dialogs.chooseItem(self.engine, info.difficulties,
                                     "%s \n %s" % (info.name, _("Player 1 Choose a difficulty:")), selected = self.player.difficulty)
              else:
                d = info.difficulties[0]
              if d:
                self.player.difficulty = d
              else:
                if len(info.parts) <= 1:
                  escape = True
                break
              while True:
                if self.engine.config.get("game", "players") > 1:               
                  p = Dialogs.chooseItem(self.engine, info.parts + ["Party Mode"] + ["No Player 2"], "%s \n %s" % (info.name, _("Player 2 Choose a part:")), selected = self.player2.part)
                  if p and p == "No Player 2":
                    players = 1
                    selected = True
                    self.player2.part = p
                    break
                  elif p and p == "Party Mode":
                    players = -1
                    selected = True
                    self.player2.part = p
                    break
                  elif p and p != "No Player 2" and p != "Party Mode":
                    players = 2
                    self.player2.part = p

                  else:
                    if len(info.difficulties) <= 1:
                      escaped = True
                    if len(info.parts) <= 1:
                      escape = True
                    break
                  while True:                    
                    if len(info.difficulties) > 1:
                      d = Dialogs.chooseItem(self.engine, info.difficulties, "%s \n %s" % (info.name, _("Player 2 Choose a difficulty:")), selected = self.player2.difficulty)
                    else:
                      d = info.difficulties[0]
                    if d:
                      self.player2.difficulty = d
                    else:
                      break
                    selected = True
                    break
                else:
                  selected = True
                  break
                if selected:
                  break
              if selected or escaped:
                break
            if selected or escape:
              break

          if (not selected) or escape:
            continue
          break
      else:
        info = Song.loadSongInfo(self.engine, self.songName, library = self.libraryName)

      if self.engine.cmdPlay == 2:
        if len(info.difficulties) >= self.engine.cmdDiff:
          self.player.difficulty = info.difficulties[self.engine.cmdDiff]
        if len(info.parts) >= self.engine.cmdPart:
          self.player.part = info.parts[self.engine.cmdPart]
          
      # Make sure the difficulty we chose is available
      if not self.player.difficulty in info.difficulties:
        self.player.difficulty = info.difficulties[0]
      if not self.player.part in info.parts:
        self.player.part = info.parts[0]

      if not self.player.difficulty in info.difficulties:
        self.player.difficulty = info.difficulties[0]
      if not self.player.part in info.parts:
        self.player.part = info.parts[0]   
        
      self.session.world.deleteScene(self)
      self.session.world.createScene("GuitarScene", libraryName = self.libraryName, songName = self.songName, Players = players)
