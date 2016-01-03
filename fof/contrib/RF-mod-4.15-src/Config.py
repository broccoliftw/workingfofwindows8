#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
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

from ConfigParser import ConfigParser
import Log
import Resource
import os

encoding  = "iso-8859-1"
config    = None
prototype = {}

class MyConfigParser(ConfigParser):
  def write(self, fp):
      if self._defaults:
        fp.write("[%s]\n" % DEFAULTSECT)
        for (key, value) in self._defaults.items():
          fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
        fp.write("\n")
      sections = sorted(self._sections)
      for section in sections:
        if section == "theme":
          continue
        fp.write("[%s]\n" % section)
        sectList = self._sections[section].items()
        sectList.sort()
        for key, value in sectList:
          if key != "__name__":
            fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
        fp.write("\n")
        
  def writeTheme(self, fp):
      if self._defaults:
        fp.write("[%s]\n" % DEFAULTSECT)
        for (key, value) in self._defaults.items():
          fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
        fp.write("\n")
      sections = sorted(self._sections)
      for section in sections:
        if section != "theme":
          continue
        fp.write("[%s]\n" % section)
        sectList = self._sections[section].items()
        sectList.sort()
        for key, value in sectList:
          if key != "__name__":
            fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
        fp.write("\n")
        
class Option:
  """A prototype configuration key."""
  def __init__(self, **args):
    for key, value in args.items():
      setattr(self, key, value)
      
def define(section, option, type, default = None, text = None, options = None, prototype = prototype):
  """
  Define a configuration key.
  
  @param section:    Section name
  @param option:     Option name
  @param type:       Key type (e.g. str, int, ...)
  @param default:    Default value for the key
  @param text:       Text description for the key
  @param options:    Either a mapping of values to text descriptions
                    (e.g. {True: 'Yes', False: 'No'}) or a list of possible values
  @param prototype:  Configuration prototype mapping
  """
  if not section in prototype:
    prototype[section] = {}
    
  if type == bool and not options:
    options = [True, False]
    
  prototype[section][option] = Option(type = type, default = default, text = text, options = options)

def load(fileName = None, setAsDefault = False):
  """Load a configuration with the default prototype"""
  global config
  c = Config(prototype, fileName)
  if setAsDefault and not config:
    config = c
  return c

class Config:
  """A configuration registry."""
  def __init__(self, prototype, fileName = None):
    """
    @param prototype:  The configuration protype mapping
    @param fileName:   The file that holds this configuration registry
    """
    self.prototype = prototype

    # read configuration
    self.config = MyConfigParser()

    if fileName:
      if not os.path.isfile(fileName):
        path = Resource.getWritableResourcePath()
        fileName = os.path.join(path, fileName)
      self.config.read(fileName)
  
    self.fileName  = fileName
  
    # fix the defaults and non-existing keys
    for section, options in prototype.items():
      if not self.config.has_section(section):
        self.config.add_section(section)
      for option in options.keys():
        type    = options[option].type
        default = options[option].default
        if not self.config.has_option(section, option):
          self.config.set(section, option, str(default))
    
  def get(self, section, option):
    """
    Read a configuration key.
    
    @param section:   Section name
    @param option:    Option name
    @return:          Key value
    """
    try:
      type    = self.prototype[section][option].type
      default = self.prototype[section][option].default
    except KeyError:
      Log.warn("Config key %s.%s not defined while reading." % (section, option))
      type, default = str, None
  
    value = self.config.has_option(section, option) and self.config.get(section, option) or default
    if type == bool:
      value = str(value).lower()
      if value in ("1", "true", "yes", "on"):
        value = True
      else:
        value = False
    else:
      try:
        value = type(value)
      except:
        value = None
      
    #Log.debug("%s.%s = %s" % (section, option, value))
    return value

  def set(self, section, option, value):
    """
    Set the value of a configuration key.
    
    @param section:   Section name
    @param option:    Option name
    @param value:     Value name
    """
    try:
      prototype[section][option]
    except KeyError:
      Log.warn("Config key %s.%s not defined while writing." % (section, option))
    
    if not self.config.has_section(section):
      self.config.add_section(section)

    if type(value) == unicode:
      value = value.encode(encoding)
    else:
      value = str(value)

    self.config.set(section, option, value)
    
    f = open(self.fileName, "w")
    self.config.write(f)
    f.close()

  def getModOptions1(self, twoChord, hopo8th, compact = False):
    #For use with single digit flags
    #Do not change the order

    #0    
    #Value 0 not used / 1 used
    if twoChord > 0:
      twoChordUsed = 1
    else:
      twoChordUsed = 0

    #1      
    #Value 0 off / 1 on
    disableVBPMUsed = int(self.get("game", "disable_vbpm"))

    #2    
    #Value 0 on / 1 on
    if self.get("game", "tapping") == False:
      hopoDisableUsed = 0
    else:
      hopoDisableUsed = 1

    #3
    #Value 0 FoF / 1 RFmod
    hopoMarks = int(self.get("game", "hopo_mark"))

    #4    
    #Value 0 FoF / 1 RFmod / 2 RFmod2
    hopoStyle = int(self.get("game", "hopo_style"))

    #5    
    #Value 0 FoF / 1 GH / 2 Custom
    pov = int(self.get("game", "pov"))

    #6    
    #Value 0 FoF / 1 Capo
    margin = int(self.get("game", "margin"))

    #7    
    #Value 0 no / 1 yes
    hopo8thUsed = int(hopo8th)

    #8    
    #Value 0 bpm / 1 difficulty
    boardSpeed = int(self.get("game", "board_speed"))

    encode = "%d%d%d%d%d%d%d%d%d" % (twoChordUsed, disableVBPMUsed, hopoDisableUsed, hopoMarks, hopoStyle, pov, margin, hopo8thUsed, boardSpeed)
    return encode
  def getModOptions2(self):
    #For use with more than single digit flags
    #Do not change order
    #Will be used for some of the Cmod values
    encode = ""
    boardSpeedMult = self.get("game", "board_speed")
    return encode
    

  def prettyModOptions(self, modOptions):
    encode = ""
    
    modOptions1, mod2 = modOptions.split(',', 2)

    if modOptions1 != "" and modOptions1 != "Default":
      if modOptions1[0] == '1':
        encode += "2"
      if modOptions1[1] == '1':
        encode += "v"
      if modOptions1[2] == '1':
        encode += "h"
      if modOptions1[3] == '1':
        encode += "m"
      if modOptions1[4] == '1':
        encode += "k"
      elif modOptions1[4] == '2':
        encode += "K"
      if modOptions1[5] == '1':
        encode += "p"
      elif modOptions1[5] == '2':
        encode += "P"
      if modOptions1[6] == '1':
        encode += "C"
      if modOptions1[7] == '1':
        encode += "9"
      if modOptions1[8] == '1':
        encode += "d"

    if mod2 != "" and mod2 != "Default":
      encode += ","
      modOptions2 = mod2.split(',')
      if modOptions2[0] != "":
        encode += "BS=%s" % (modOptions2[0])
    return encode
  
def get(section, option):
  """
  Read the value of a global configuration key.
  
  @param section:   Section name
  @param option:    Option name
  @return:          Key value
  """
  global config
  return config.get(section, option)
  
def set(section, option, value):
  """
  Write the value of a global configuration key.
  
  @param section:   Section name
  @param option:    Option name
  @param value:     New key value
  """
  global config
  return config.set(section, option, value)
