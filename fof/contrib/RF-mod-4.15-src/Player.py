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

import pygame
import Config
import Song
from Language import _

LEFT    = 0x1
RIGHT   = 0x2
UP      = 0x4
DOWN    = 0x8
ACTION1 = 0x10
ACTION2 = 0x20
KEY1    = 0x40
KEY2    = 0x80
KEY3    = 0x100
KEY4    = 0x200
KEY5    = 0x400
CANCEL  = 0x800

PLAYER_2_LEFT    = 0x1000
PLAYER_2_RIGHT   = 0x2000
PLAYER_2_UP      = 0x4000
PLAYER_2_DOWN    = 0x8000
PLAYER_2_ACTION1 = 0x10000
PLAYER_2_ACTION2 = 0x20000
PLAYER_2_KEY1    = 0x40000
PLAYER_2_KEY2    = 0x80000
PLAYER_2_KEY3    = 0x100000
PLAYER_2_KEY4    = 0x200000
PLAYER_2_KEY5    = 0x400000
PLAYER_2_CANCEL  = 0x800000

LEFTS  = [LEFT,PLAYER_2_LEFT]
RIGHTS = [RIGHT,PLAYER_2_RIGHT]
UPS    = [UP,PLAYER_2_UP]
DOWNS  = [DOWN,PLAYER_2_DOWN]
ACTION1S= [ACTION1,PLAYER_2_ACTION1]
ACTION2S= [ACTION2,PLAYER_2_ACTION2]
CANCELS= [CANCEL,PLAYER_2_CANCEL]
KEY5S  = [KEY5,PLAYER_2_KEY5]
KEY1S  = [KEY1,PLAYER_2_KEY1]
KEY2S  = [KEY2,PLAYER_2_KEY2]
KEY3S  = [KEY3,PLAYER_2_KEY3]
KEY4S  = [KEY4,PLAYER_2_KEY4]
KEY5S  = [KEY5,PLAYER_2_KEY5]

SCORE_MULTIPLIER = [0, 10, 20, 30]

# define configuration keys
Config.define("player0", "key_left",     str, "K_LEFT",   text = _("Move left"))
Config.define("player0", "key_right",    str, "K_RIGHT",  text = _("Move right"))
Config.define("player0", "key_up",       str, "K_UP",     text = _("Move up"))
Config.define("player0", "key_down",     str, "K_DOWN",   text = _("Move down"))
Config.define("player0", "key_action1",  str, "K_RETURN", text = _("Pick"))
Config.define("player0", "key_action2",  str, "K_RSHIFT", text = _("Secondary Pick"))
Config.define("player0", "key_1",        str, "K_F1",     text = _("Fret #1"))
Config.define("player0", "key_2",        str, "K_F2",     text = _("Fret #2"))
Config.define("player0", "key_3",        str, "K_F3",     text = _("Fret #3"))
Config.define("player0", "key_4",        str, "K_F4",     text = _("Fret #4"))
Config.define("player0", "key_5",        str, "K_F5",     text = _("Fret #5"))
Config.define("player0", "key_cancel",   str, "K_ESCAPE", text = _("Cancel"))
Config.define("player0", "akey_left",    str, "K_LEFT",   text = _("Alt Move left"))
Config.define("player0", "akey_right",   str, "K_RIGHT",  text = _("Alt Move right"))
Config.define("player0", "akey_up",      str, "K_UP",     text = _("Alt Move up"))
Config.define("player0", "akey_down",    str, "K_DOWN",   text = _("Alt Move down"))
Config.define("player0", "akey_action1", str, "K_RETURN", text = _("Alt Pick"))
Config.define("player0", "akey_action2", str, "K_RSHIFT", text = _("Alt Secondary Pick"))
Config.define("player0", "akey_1",       str, "K_F1",     text = _("Alt Fret #1"))
Config.define("player0", "akey_2",       str, "K_F2",     text = _("Alt Fret #2"))
Config.define("player0", "akey_3",       str, "K_F3",     text = _("Alt Fret #3"))
Config.define("player0", "akey_4",       str, "K_F4",     text = _("Alt Fret #4"))
Config.define("player0", "akey_5",       str, "K_F5",     text = _("Alt Fret #5"))
Config.define("player0", "akey_cancel",  str, "K_ESCAPE", text = _("Alt Cancel"))

Config.define("player1", "player_2_key_left",     str, "K_LEFT",     text = _("Player 2 Move left"))
Config.define("player1", "player_2_key_right",    str, "K_RIGHT",    text = _("Player 2 Move right"))
Config.define("player1", "player_2_key_up",       str, "K_UP",       text = _("Player 2 Move up"))
Config.define("player1", "player_2_key_down",     str, "K_DOWN",     text = _("Player 2 Move down"))
Config.define("player1", "player_2_key_action1",  str, "K_PAGEDOWN", text = _("Player 2 Pick"))
Config.define("player1", "player_2_key_action2",  str, "K_PAGEUP",   text = _("Player 2 Secondary Pick"))
Config.define("player1", "player_2_key_1",        str, "K_F8",       text = _("Player 2 Fret #1"))
Config.define("player1", "player_2_key_2",        str, "K_F9",       text = _("Player 2 Fret #2"))
Config.define("player1", "player_2_key_3",        str, "K_F10",      text = _("Player 2 Fret #3"))
Config.define("player1", "player_2_key_4",        str, "K_F11",      text = _("Player 2 Fret #4"))
Config.define("player1", "player_2_key_5",        str, "K_F12",      text = _("Player 2 Fret #5"))
Config.define("player1", "player_2_key_cancel",   str, "K_F7",       text = _("Player 2 Cancel"))

Config.define("player1", "aplayer_2_key_left",     str, "K_LEFT",     text = _("Player 2 Move left"))
Config.define("player1", "aplayer_2_key_right",    str, "K_RIGHT",    text = _("Player 2 Move right"))
Config.define("player1", "aplayer_2_key_up",       str, "K_UP",       text = _("Player 2 Move up"))
Config.define("player1", "aplayer_2_key_down",     str, "K_DOWN",     text = _("Player 2 Move down"))
Config.define("player1", "aplayer_2_key_action1",  str, "K_PAGEDOWN", text = _("Player 2 Pick"))
Config.define("player1", "aplayer_2_key_action2",  str, "K_PAGEUP",   text = _("Player 2 Secondary Pick"))
Config.define("player1", "aplayer_2_key_1",        str, "K_F8",       text = _("Player 2 Fret #1"))
Config.define("player1", "aplayer_2_key_2",        str, "K_F9",       text = _("Player 2 Fret #2"))
Config.define("player1", "aplayer_2_key_3",        str, "K_F10",      text = _("Player 2 Fret #3"))
Config.define("player1", "aplayer_2_key_4",        str, "K_F11",      text = _("Player 2 Fret #4"))
Config.define("player1", "aplayer_2_key_5",        str, "K_F12",      text = _("Player 2 Fret #5"))
Config.define("player1", "aplayer_2_key_cancel",   str, "K_F7",       text = _("Player 2 Cancel"))

Config.define("player0", "name",         str, "")
Config.define("player0", "difficulty",   int, Song.EASY_DIFFICULTY)
Config.define("player0", "part",         int, Song.GUITAR_PART)

Config.define("player1", "name",         str, "")
Config.define("player1", "difficulty",   int, Song.EASY_DIFFICULTY)
Config.define("player1", "part",         int, Song.GUITAR_PART)

class Controls:
  def __init__(self):
    def keycode(name, player):
      playerstring = "player" + str(player)
      k = Config.get(playerstring, name)
      try:
        return int(k)
      except:
        return getattr(pygame, k)
    
    self.flags = 0
    prefix = ""
    useAltKeySet = Config.get("game", "alt_keys")
    if useAltKeySet == True:
      prefix = "a"
    self.controlMapping = {
      keycode("%skey_left" % (prefix), 0):      LEFT,
      keycode("%skey_right" % (prefix), 0):     RIGHT,
      keycode("%skey_up" % (prefix), 0):        UP,
      keycode("%skey_down" % (prefix), 0):      DOWN,
      keycode("%skey_action1" % (prefix), 0):   ACTION1,
      keycode("%skey_action2" % (prefix), 0):   ACTION2,
      keycode("%skey_1" % (prefix), 0):         KEY1,
      keycode("%skey_2" % (prefix), 0):         KEY2,
      keycode("%skey_3" % (prefix), 0):         KEY3,
      keycode("%skey_4" % (prefix), 0):         KEY4,
      keycode("%skey_5" % (prefix), 0):         KEY5,
      keycode("%skey_cancel" % (prefix), 0):    CANCEL,
      
      keycode("%splayer_2_key_action1" % (prefix), 1):   PLAYER_2_ACTION1,
      keycode("%splayer_2_key_action2" % (prefix), 1):   PLAYER_2_ACTION2,
      keycode("%splayer_2_key_1" % (prefix), 1):         PLAYER_2_KEY1,
      keycode("%splayer_2_key_2" % (prefix), 1):         PLAYER_2_KEY2,
      keycode("%splayer_2_key_3" % (prefix), 1):         PLAYER_2_KEY3,
      keycode("%splayer_2_key_4" % (prefix), 1):         PLAYER_2_KEY4,
      keycode("%splayer_2_key_5" % (prefix), 1):         PLAYER_2_KEY5,
      keycode("%splayer_2_key_left" % (prefix), 1):      PLAYER_2_LEFT,
      keycode("%splayer_2_key_right" % (prefix), 1):     PLAYER_2_RIGHT,
      keycode("%splayer_2_key_up" % (prefix), 1):        PLAYER_2_UP,
      keycode("%splayer_2_key_down" % (prefix), 1):      PLAYER_2_DOWN,
      keycode("%splayer_2_key_cancel" % (prefix), 1):    PLAYER_2_CANCEL,
    }

    self.reverseControlMapping = dict((value, key) for key, value in self.controlMapping.iteritems() )
      
    # Multiple key support
    self.heldKeys = {}

  def getMapping(self, key):
    return self.controlMapping.get(key)
  def getReverseMapping(self, control):
    return self.reverseControlMapping.get(control)

  def keyPressed(self, key):
    c = self.getMapping(key)
    if c:
      self.toggle(c, True)
      if c in self.heldKeys and not key in self.heldKeys[c]:
        self.heldKeys[c].append(key)
      return c
    return None

  def keyReleased(self, key):
    c = self.getMapping(key)
    if c:
      if c in self.heldKeys:
        if key in self.heldKeys[c]:
          self.heldKeys[c].remove(key)
          if not self.heldKeys[c]:
            self.toggle(c, False)
            return c
        return None
      self.toggle(c, False)
      return c
    return None

  def toggle(self, control, state):
    prevState = self.flags
    if state:
      self.flags |= control
      return not prevState & control
    else:
      self.flags &= ~control
      return prevState & control

  def getState(self, control):
    return self.flags & control

class Player(object):
  def __init__(self, owner, name, number):
    self.owner    = owner
    self.controls = Controls()
    self.reset()
    self.playerstring = "player" + str(number)
    
  def reset(self):
    self.score         = 0
    self._streak       = 0
    self.notesHit      = 0
    self.longestStreak = 0
    self.cheating      = False
    self.twoChord      = 0
    
  def getName(self):
    return Config.get(self.playerstring, "name")
    
  def setName(self, name):
    Config.set(self.playerstring, "name", name)
    
  name = property(getName, setName)
  
  def getStreak(self):
    return self._streak
    
  def setStreak(self, value):
    self._streak = value
    self.longestStreak = max(self._streak, self.longestStreak)
    
  streak = property(getStreak, setStreak)
    
  def getDifficulty(self):
    return Song.difficulties.get(Config.get(self.playerstring, "difficulty"))
    
  def setDifficulty(self, difficulty):
    Config.set(self.playerstring, "difficulty", difficulty.id)

  def getPart(self):
    part = Config.get(self.playerstring, "part")
    if part == -1:
      return "Party Mode"
    elif part == -2:
      return "No Player 2"
    else:
      return Song.parts.get(part)
    
  def setPart(self, part):
    if part == "Party Mode":
      Config.set(self.playerstring, "part", -1)
    elif part == "No Player 2":
      Config.set(self.playerstring, "part", -2)
    else:
      Config.set(self.playerstring, "part", part.id)    
    
  difficulty = property(getDifficulty, setDifficulty)
  part = property(getPart, setPart)
  
  def addScore(self, score):
    self.score += score * self.getScoreMultiplier()
    
  def getScoreMultiplier(self):
    try:
      return SCORE_MULTIPLIER.index((self.streak / 10) * 10) + 1
    except ValueError:
      return len(SCORE_MULTIPLIER)
