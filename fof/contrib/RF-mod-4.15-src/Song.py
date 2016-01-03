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

import midi
import Log
import Audio
import Config
import os
import re
import shutil
import Config
import sha
import binascii
import Cerealizer
import urllib
import Version
import Theme
import copy
from Language import _

DEFAULT_LIBRARY         = "songs"

AMAZING_DIFFICULTY      = 0
MEDIUM_DIFFICULTY       = 1
EASY_DIFFICULTY         = 2
SUPAEASY_DIFFICULTY     = 3

FOF_TYPE                = 0
GH1_TYPE                = 1
GH2_TYPE                = 2

GUITAR_PART             = 0
RHYTHM_PART             = 1
BASS_PART               = 2
LEAD_PART               = 3

class Part:
  def __init__(self, id, text):
    self.id   = id
    self.text = text
    
  def __str__(self):
    return self.text

  def __repr__(self):
    return self.text

parts = {
  GUITAR_PART: Part(GUITAR_PART, _("Guitar")),
  RHYTHM_PART: Part(RHYTHM_PART, _("Rhythm Guitar")),
  BASS_PART:   Part(BASS_PART,   _("Bass Guitar")),
  LEAD_PART:   Part(LEAD_PART,   _("Lead Guitar")),
}

class Difficulty:
  def __init__(self, id, text):
    self.id   = id
    self.text = text
    
  def __str__(self):
    return self.text

  def __repr__(self):
    return self.text

difficulties = {
  SUPAEASY_DIFFICULTY: Difficulty(SUPAEASY_DIFFICULTY, _("Supaeasy")),
  EASY_DIFFICULTY:     Difficulty(EASY_DIFFICULTY,     _("Easy")),
  MEDIUM_DIFFICULTY:   Difficulty(MEDIUM_DIFFICULTY,   _("Medium")),
  AMAZING_DIFFICULTY:  Difficulty(AMAZING_DIFFICULTY,  _("Amazing")),
}

class SongInfo(object):
  def __init__(self, infoFileName):
    self.songName      = os.path.basename(os.path.dirname(infoFileName))
    self.fileName      = infoFileName
    self.info          = Config.MyConfigParser()
    self._difficulties = None
    self._parts        = None

    try:
      self.info.read(infoFileName)
    except:
      pass
      
    # Read highscores and verify their hashes.
    # There ain't no security like security throught obscurity :)
    self.highScores = {}
    
    scores = self._get("scores", str, "")
    scores_ext = self._get("scores_ext", str, "")
    if scores:
      scores = Cerealizer.loads(binascii.unhexlify(scores))
      if scores_ext:
        scores_ext = Cerealizer.loads(binascii.unhexlify(scores_ext))
      for difficulty in scores.keys():
        try:
          difficulty = difficulties[difficulty]
        except KeyError:
          continue
        for i, base_scores in enumerate(scores[difficulty.id]):
          score, stars, name, hash = base_scores
          if scores_ext != "":
            #Someone may have mixed extended and non extended
            try:
              hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, modOptions1, modOptions2 =  scores_ext[difficulty.id][i]
              scoreExt = (notesHit, notesTotal, noteStreak, modVersion, modOptions1, modOptions2)
            except:
              hash_ext = 0
              scoreExt = (0, 0, 0 , "RF-mod", "Default", "Default")
          if self.getScoreHash(difficulty, score, stars, name) == hash:
            if scores_ext != "" and hash == hash_ext:
              self.addHighscore(difficulty, score, stars, name, part = parts[GUITAR_PART], scoreExt = scoreExt)
            else:
              self.addHighscore(difficulty, score, stars, name, part = parts[GUITAR_PART])
          else:
            Log.warn("Weak hack attempt detected. Better luck next time.")

    self.highScoresRhythm = {}
    
    scores = self._get("scores_rhythm", str, "")
    if scores:
      scores = Cerealizer.loads(binascii.unhexlify(scores))
      for difficulty in scores.keys():
        try:
          difficulty = difficulties[difficulty]
        except KeyError:
          continue
        for score, stars, name, hash in scores[difficulty.id]:
          if self.getScoreHash(difficulty, score, stars, name) == hash:
            self.addHighscore(difficulty, score, stars, name, part = parts[RHYTHM_PART])
          else:
            Log.warn("Weak hack attempt detected. Better luck next time.")

    self.highScoresBass = {}
    
    scores = self._get("scores_bass", str, "")
    if scores:
      scores = Cerealizer.loads(binascii.unhexlify(scores))
      for difficulty in scores.keys():
        try:
          difficulty = difficulties[difficulty]
        except KeyError:
          continue
        for score, stars, name, hash in scores[difficulty.id]:
          if self.getScoreHash(difficulty, score, stars, name) == hash:
            self.addHighscore(difficulty, score, stars, name, part = parts[BASS_PART])
          else:
            Log.warn("Weak hack attempt detected. Better luck next time.")

    self.highScoresLead = {}
    
    scores = self._get("scores_lead", str, "")
    if scores:
      scores = Cerealizer.loads(binascii.unhexlify(scores))
      for difficulty in scores.keys():
        try:
          difficulty = difficulties[difficulty]
        except KeyError:
          continue
        for score, stars, name, hash in scores[difficulty.id]:
          if self.getScoreHash(difficulty, score, stars, name) == hash:
            self.addHighscore(difficulty, score, stars, name, part = parts[LEAD_PART])
          else:
            Log.warn("Weak hack attempt detected. Better luck next time.")            
            
  def _set(self, attr, value):
    if not self.info.has_section("song"):
      self.info.add_section("song")
    if type(value) == unicode:
      value = value.encode(Config.encoding)
    else:
      value = str(value)
    self.info.set("song", attr, value)
    
  def getObfuscatedScores(self, part = parts[GUITAR_PART]):
    s = {}
    if part == parts[GUITAR_PART]:
      highScores = self.highScores
    elif part == parts[RHYTHM_PART]:
      highScores = self.highScoresRhythm
    elif part == parts[BASS_PART]:
      highScores = self.highScoresBass
    elif part == parts[LEAD_PART]:
      highScores = self.highScoresLead
    else:
      highScores = self.highScores
      
    for difficulty in highScores.keys():
      s[difficulty.id] = [(score, stars, name, self.getScoreHash(difficulty, score, stars, name)) for score, stars, name, scores_ext in highScores[difficulty]]
    return binascii.hexlify(Cerealizer.dumps(s))

  def getObfuscatedScoresExt(self, part = parts[GUITAR_PART]):
    s = {}
    if part == parts[GUITAR_PART]:
      highScores = self.highScores
    elif part == parts[RHYTHM_PART]:
      highScores = self.highScoresRhythm
    elif part == parts[BASS_PART]:
      highScores = self.highScoresBass
    elif part == parts[LEAD_PART]:
      highScores = self.highScoresLead
    else:
      highScores = self.highScores
      
    for difficulty in highScores.keys():
      s[difficulty.id] = [(self.getScoreHash(difficulty, score, stars, name), stars) + scores_ext for score, stars, name, scores_ext in highScores[difficulty]]
    return binascii.hexlify(Cerealizer.dumps(s))

  def save(self):
    if self.highScores != {}:
      self._set("scores",        self.getObfuscatedScores(part = parts[GUITAR_PART]))
      self._set("scores_ext",    self.getObfuscatedScoresExt(part = parts[GUITAR_PART]))
    if self.highScoresRhythm != {}:
      self._set("scores_rhythm", self.getObfuscatedScores(part = parts[RHYTHM_PART]))
      self._set("scores_rhythm_ext", self.getObfuscatedScoresExt(part = parts[RHYTHM_PART]))
    if self.highScoresBass != {}:
      self._set("scores_bass",   self.getObfuscatedScores(part = parts[BASS_PART]))
      self._set("scores_bass_ext",   self.getObfuscatedScoresExt(part = parts[BASS_PART]))
    if self.highScoresLead != {}:
      self._set("scores_lead",   self.getObfuscatedScores(part = parts[LEAD_PART]))
      self._set("scores_lead_ext",   self.getObfuscatedScoresExt(part = parts[LEAD_PART]))
    
    f = open(self.fileName, "w")
    self.info.write(f)
    f.close()
    
  def _get(self, attr, type = None, default = ""):
    try:
      v = self.info.get("song", attr)
    except:
      v = default
    if v is not None and type:
      v = type(v)
    return v

  def getDifficulties(self):
    # Tutorials only have the medium difficulty
    if self.tutorial:
      return [difficulties[MEDIUM_DIFFICULTY]]

    if self._difficulties is not None:
      return self._difficulties

    # See which difficulties are available
    try:
      noteFileName = os.path.join(os.path.dirname(self.fileName), "notes.mid")
      info = MidiInfoReader()
      midiIn = midi.MidiInFile(info, noteFileName)
      try:
        midiIn.read()
      except MidiInfoReader.Done:
        pass
      info.difficulties.sort(lambda a, b: cmp(b.id, a.id))
      self._difficulties = info.difficulties
    except:
      self._difficulties = difficulties.values()
    return self._difficulties

  def getParts(self):
    if self._parts is not None:
      return self._parts

    # See which parts are available
    try:
      noteFileName = os.path.join(os.path.dirname(self.fileName), "notes.mid")
      info = MidiPartsReader()

      midiIn = midi.MidiInFile(info, noteFileName)
      try:
        midiIn.read()
      except MidiPartsReader.Done:
        pass
      if info.parts == []:
        part = parts[GUITAR_PART]
        info.parts.append(part)
      info.parts.sort(lambda b, a: cmp(b.id, a.id))
      self._parts = info.parts
    except:
      self._parts = parts.values()
    return self._parts

  def getName(self):
    return self._get("name")

  def setName(self, value):
    self._set("name", value)

  def getArtist(self):
    return self._get("artist")

  def getCassetteColor(self):
    c = self._get("cassettecolor")
    if c:
      return Theme.hexToColor(c)
  
  def setCassetteColor(self, color):
    self._set("cassettecolor", Theme.colorToHex(color))
  
  def setArtist(self, value):
    self._set("artist", value)
    
  def getScoreHash(self, difficulty, score, stars, name):
    return sha.sha("%d%d%d%s" % (difficulty.id, score, stars, name)).hexdigest()
    
  def getDelay(self):
    return self._get("delay", int, 0)
    
  def setDelay(self, value):
    return self._set("delay", value)

  
  def getFrets(self):
    return self._get("frets")

  def setFrets(self, value):
    self._set("frets", value)
    
  def getVersion(self):
    return self._get("version")

  def setVersion(self, value):
    self._set("version", value)

  def getTags(self):
    return self._get("tags")

  def setTags(self, value):
    self._set("tags", value)

  def getHopo(self):
    return self._get("hopo")

  def setHopo(self, value):
    self._set("hopo", value)

  def getCount(self):
    return self._get("count")

  def setCount(self, value):
    self._set("count", value)

  def getLyrics(self):
    return self._get("lyrics")

  def setLyrics(self, value):
    self._set("lyrics", value)    
        
  def getHighscores(self, difficulty, part = parts[GUITAR_PART]):
    if part == parts[GUITAR_PART]:
      highScores = self.highScores
    elif part == parts[RHYTHM_PART]:
      highScores = self.highScoresRhythm
    elif part == parts[BASS_PART]:
      highScores = self.highScoresBass
    elif part == parts[LEAD_PART]:
      highScores = self.highScoresLead
    else:
      highScores = self.highScores
      
    try:
      return highScores[difficulty]
    except KeyError:
      return []
      
  def uploadHighscores(self, url, songHash, part = parts[GUITAR_PART]):
    try:
      d = {
        "songName": self.songName,
        "songHash": songHash,
        "scores":   self.getObfuscatedScores(part = part),
        "scores_ext": self.getObfuscatedScoresExt(part = part),
        "version":  Version.version(),
        "songPart": part
      }
      data = urllib.urlopen(url + "?" + urllib.urlencode(d)).read()
      Log.debug("Score upload result: %s" % data)
      return data == "True"
    except Exception, e:
      Log.error(e)
      return False
    return True
  
  def addHighscore(self, difficulty, score, stars, name, part = parts[GUITAR_PART], scoreExt = (0, 0, 0, "RF-mod", "Default", "Default")):
    if part == parts[GUITAR_PART]:
      highScores = self.highScores
    elif part == parts[RHYTHM_PART]:
      highScores = self.highScoresRhythm
    elif part == parts[BASS_PART]:
      highScores = self.highScoresBass
    elif part == parts[LEAD_PART]:
      highScores = self.highScoresLead
    else:
      highScores = self.highScores

    #notesHit, notesTotal, noteStreak, modVersion, modOptions1, modOptions2 = scoreExt 
    if not difficulty in highScores:
      highScores[difficulty] = []
    highScores[difficulty].append((score, stars, name, scoreExt))
    highScores[difficulty].sort(lambda a, b: {True: -1, False: 1}[a[0] > b[0]])
    highScores[difficulty] = highScores[difficulty][:5]
    for i, scores in enumerate(highScores[difficulty]):
      _score, _stars, _name, _scores_ext = scores
      if _score == score and _stars == stars and _name == name:
        return i
    return -1

  def isTutorial(self):
    return self._get("tutorial", int, 0) == 1

  def findTag(self, find, value = None):
    for tag in self.tags.split(','):
      temp = tag.split('=')
      if find == temp[0]:
        if value == None:
          return True
        elif len(temp) == 2 and value == temp[1]:
          return True

    return False
      
    
  name          = property(getName, setName)
  artist        = property(getArtist, setArtist)
  delay         = property(getDelay, setDelay)
  tutorial      = property(isTutorial)
  difficulties  = property(getDifficulties)
  cassetteColor = property(getCassetteColor, setCassetteColor)
  #New RF-mod Items
  parts         = property(getParts)
  frets         = property(getFrets, setFrets)
  version       = property(getVersion, setVersion)
  tags          = property(getTags, setTags)
  hopo          = property(getHopo, setHopo)
  count         = property(getCount, setCount)
  lyrics        = property(getLyrics, setLyrics)
  #May no longer be necessary
  folder        = False


class LibraryInfo(object):
  def __init__(self, libraryName, infoFileName):
    self.libraryName   = libraryName
    self.fileName      = infoFileName
    self.info          = Config.MyConfigParser()
    self.songCount     = 0

    try:
      self.info.read(infoFileName)
    except:
      pass

    # Set a default name
    if not self.name:
      self.name = os.path.basename(os.path.dirname(self.fileName))
    if Config.get("game", "disable_libcount") == True:
      return
    # Count the available songs
    libraryRoot = os.path.dirname(self.fileName)
    for name in os.listdir(libraryRoot):
      if not os.path.isdir(os.path.join(libraryRoot, name)) or name.startswith("."):
        continue
      if os.path.isfile(os.path.join(libraryRoot, name, "notes.mid")):
        self.songCount += 1

  def _set(self, attr, value):
    if not self.info.has_section("library"):
      self.info.add_section("library")
    if type(value) == unicode:
      value = value.encode(Config.encoding)
    else:
      value = str(value)
    self.info.set("library", attr, value)
    
  def save(self):
    f = open(self.fileName, "w")
    self.info.write(f)
    f.close()
    
  def _get(self, attr, type = None, default = ""):
    try:
      v = self.info.get("library", attr)
    except:
      v = default
    if v is not None and type:
      v = type(v)
    return v

  def getName(self):
    return self._get("name")

  def setName(self, value):
    self._set("name", value)

  def getColor(self):
    c = self._get("color")
    if c:
      return Theme.hexToColor(c)
  
  def setColor(self, color):
    self._set("color", Theme.colorToHex(color))
        
  name          = property(getName, setName)
  color         = property(getColor, setColor)

class Event:
  def __init__(self, length):
    self.length = length

class Note(Event):
  def __init__(self, number, length, special = False, tappable = 0):
    Event.__init__(self, length)
    self.number   = number
    self.played   = False
    self.special  = special
    self.tappable = tappable
    #RF-mod
    self.hopod   = False
    self.skipped = False
    self.flameCount = 0
    
  def __repr__(self):
    return "<#%d>" % self.number

class Tempo(Event):
  def __init__(self, bpm):
    Event.__init__(self, 0)
    self.bpm = bpm
    
  def __repr__(self):
    return "<%d bpm>" % self.bpm

class TextEvent(Event):
  def __init__(self, text, length):
    Event.__init__(self, length)
    self.text = text

  def __repr__(self):
    return "<%s>" % self.text

class PictureEvent(Event):
  def __init__(self, fileName, length):
    Event.__init__(self, length)
    self.fileName = fileName
    
class Track:
  granularity = 50
  
  def __init__(self):
    self.events = []
    self.allEvents = []
    self.marked = False

  def addEvent(self, time, event):
    for t in range(int(time / self.granularity), int((time + event.length) / self.granularity) + 1):
      if len(self.events) < t + 1:
        n = t + 1 - len(self.events)
        n *= 8
        self.events = self.events + [[] for n in range(n)]
      self.events[t].append((time - (t * self.granularity), event))
    self.allEvents.append((time, event))

  def removeEvent(self, time, event):
    for t in range(int(time / self.granularity), int((time + event.length) / self.granularity) + 1):
      e = (time - (t * self.granularity), event)
      if t < len(self.events) and e in self.events[t]:
        self.events[t].remove(e)
    if (time, event) in self.allEvents:
      self.allEvents.remove((time, event))

  def getEvents(self, startTime, endTime):
    t1, t2 = [int(x) for x in [startTime / self.granularity, endTime / self.granularity]]
    if t1 > t2:
      t1, t2 = t2, t1

    events = []
    for t in range(max(t1, 0), min(len(self.events), t2)):
      for diff, event in self.events[t]:
        time = (self.granularity * t) + diff
        if not (time, event) in events:
          events.append((time, event))
    return events

  def getAllEvents(self):
    return self.allEvents

  def reset(self):
    for eventList in self.events:
      for time, event in eventList:
        if isinstance(event, Note):
          event.played = False
          event.hopod = False
          event.skipped = False
          event.flameCount = 0

  def markTappable(self):
    # Determine which notes are tappable. The rules are:
    #  1. Not the first note of the track
    #  2. Previous note not the same as this one
    #  3. Previous note not a chord
    #  4. Previous note ends at most 161 ticks before this one starts
    bpm             = None
    ticksPerBeat    = 480
    tickThreshold   = 161
    prevNotes       = []
    currentNotes    = []
    currentTicks    = 0.0
    prevTicks       = 0.0
    epsilon         = 1e-3

    def beatsToTicks(time):
      return (time * bpm * ticksPerBeat) / 60000.0

    if not self.allEvents:
      return

    for time, event in self.allEvents + [self.allEvents[-1]]:
      if isinstance(event, Tempo):
        bpm = event.bpm
      elif isinstance(event, Note):
        # All notes are initially not tappable
        event.tappable = 0
        ticks = beatsToTicks(time)
        
        # Part of chord?
        if ticks < currentTicks + epsilon:
          currentNotes.append(event)
          continue

        # Previous note not a chord?
        if len(prevNotes) == 1:
          # Previous note ended recently enough?
          prevEndTicks = prevTicks + beatsToTicks(prevNotes[0].length)
          if currentTicks - prevEndTicks <= tickThreshold:
            for note in currentNotes:
              # Are any current notes the same as the previous one?
              if note.number == prevNotes[0].number:
                break
            else:
              # If all the notes are different, mark the current notes tappable
              for note in currentNotes:
                note.tappable = 2

        # Set the current notes as the previous notes
        prevNotes    = currentNotes
        prevTicks    = currentTicks
        currentNotes = [event]
        currentTicks = ticks

  def markHopo(self):
    lastTick = 0
    lastTime  = 0
    lastEvent = Note
    
    tickDelta = 0
    noteDelta = 0

    #dtb file says 170 ticks
    hopoDelta = 170
    chordFudge = 10
    ticksPerBeat = 480
    hopoNotes = []
    chordNotes = []
    sameNotes = []
    bpmNotes = []
    firstTime = 1

    #If already processed abort   
    if self.marked == True:
      return
    
    for time, event in self.allEvents:
      if isinstance(event, Tempo):
        bpmNotes.append([time, event])
        continue
      if not isinstance(event, Note):
        continue
      
      while bpmNotes and time >= bpmNotes[0][0]:
        #Adjust to new BPM
        #bpm = bpmNotes[0][1].bpm
        bpmTime, bpmEvent = bpmNotes.pop(0)
        bpm = bpmEvent.bpm

      tick = (time * bpm * ticksPerBeat) / 60000.0
      lastTick = (lastTime * bpm * ticksPerBeat) / 60000.0
      
      #skip first note
      if firstTime == 1:
        event.tappable = -3
        lastEvent = event
        lastTime  = time
        firstTime = 0
        continue

      tickDelta = tick - lastTick        
      noteDelta = event.number - lastEvent.number

      #previous note and current note HOPOable      
      if tickDelta <= hopoDelta:
        #Add both notes to HOPO list even if duplicate.  Will come out in processing
        if (not hopoNotes) or not (hopoNotes[-1][0] == lastTime and hopoNotes[-1][1] == lastEvent):
          #special case for first marker note.  Change it to a HOPO start
          if not hopoNotes and lastEvent.tappable == -3:
            lastEvent.tappable = 1
          #this may be incorrect if a bpm event happened inbetween this note and last note
          hopoNotes.append([lastTime, bpmEvent])
          hopoNotes.append([lastTime, lastEvent])

        hopoNotes.append([bpmTime, bpmEvent])
        hopoNotes.append([time, event])
        
      #HOPO Over        
      if tickDelta > hopoDelta:
        if hopoNotes != []:
          #If the last event is the last HOPO note, mark it as a HOPO end
          if lastEvent.tappable != -1 and hopoNotes[-1][1] == lastEvent:
            if lastEvent.tappable >= 0:
              lastEvent.tappable = 3
            else:
              lastEvent.tappable = -1

      #This is the same note as before
      elif noteDelta == 0:
        #Add both notes to bad list even if duplicate.  Will come out in processing
        sameNotes.append(lastEvent)
        sameNotes.append(event)
        lastEvent.tappable = -2
        event.tappable = -2
            
      #This is a chord
      elif tickDelta < chordFudge:
        #Add both notes to bad list even if duplicate.  Will come out in processing
        if len(chordNotes) != 0 and chordNotes[-1] != lastEvent:
          chordNotes.append(lastEvent)
        chordNotes.append(event)
        lastEvent.tappable = -1
        event.tappable = -1
        
      lastEvent = event
      lastTime = time
    else:
      #Add last note to HOPO list if applicable
      if noteDelta != 0 and tickDelta > 1.5 and tickDelta < hopoDelta and isinstance(event, Note):
        hopoNotes.append([time, bpmEvent])
        hopoNotes.append([time, event])

    firstTime = 1
    note = None

    for note in list(chordNotes):
      #chord notes -1
      note.tappable = -1   

    for note in list(sameNotes):
      #same note in string -2
      note.tappable = -2

    bpmNotes = []
    
    for time, note in list(hopoNotes):
      if isinstance(note, Tempo):
        bpmNotes.append([time, note])
        continue
      if not isinstance(note, Note):
        continue
      while bpmNotes and time >= bpmNotes[0][0]:
        #Adjust to new BPM
        #bpm = bpmNotes[0][1].bpm
        bpmTime, bpmEvent = bpmNotes.pop(0)
        bpm = bpmEvent.bpm

      if firstTime == 1:
        if note.tappable >= 0:
          note.tappable = 1
        lastEvent = note
        firstTime = 0
        continue


#need to recompute (or carry forward) BPM at this time
      tick = (time * bpm * ticksPerBeat) / 60000.0
      lastTick = (lastTime * bpm * ticksPerBeat) / 60000.0
      tickDelta = tick - lastTick

      #current Note Invalid
      if note.tappable < 0:
        #If current note is invalid for HOPO, and previous note was start of a HOPO section, then previous note not HOPO
        if lastEvent.tappable == 1:
          lastEvent.tappable = 0
        #If current note is beginning of a same note sequence, it's valid for END of HOPO only
        #elif lastEvent.tappable == 2 and note.tappable == -2:
        #  note.tappable = 3
        #If current note is invalid for HOPO, and previous note was a HOPO section, then previous note is end of HOPO
        elif lastEvent.tappable > 0:
          lastEvent.tappable = 3
      #current note valid
      elif note.tappable >= 0:
        #String of same notes can be followed by HOPO
        if note.tappable == 3:
          #This is the end of a valid HOPO section
          if lastEvent.tappable == 1 or lastEvent.tappable == 2:
            lastEvent = note
            lastTime = time
            continue
          if lastEvent.tappable == -2:
            #If its the same note again it's invalid
            if lastEvent.number == note.number:
              note.tappable = -2
            else:
              lastEvent.tappable = 1
          elif lastEvent.tappable == 0:
            lastEvent.tappable = 1
          #If last note was invalid or end of HOPO section, and current note is end, it is really not HOPO
          elif lastEvent.tappable != 2 and lastEvent.tappable != 1:
            note.tappable = 0
          #If last event was invalid or end of HOPO section, current note is start of HOPO
          else:
            note.tappable = 1
        elif note.tappable == 2:
          if lastEvent.tappable == -2:
            note.tappable = 1
          elif lastEvent.tappable == -1:
            note.tappable = 0
        elif note.tappable == 1:
          if lastEvent.tappable == 2:
            note.tappable = 0
        else:
          if lastEvent.tappable == -2:
            if tickDelta <= hopoDelta:
              lastEvent.tappable = 1
              
          if lastEvent.tappable != 2 and lastEvent.tappable != 1:
            note.tappable = 1
          else:
            if note.tappable == 1:
              note.tappable = 1
            else:
              note.tappable = 2
      lastEvent = note
      lastTime = time
    else:
      if note != None:
        #Handle last note
        #If it is the start of a HOPO, it's not really a HOPO
        if note.tappable == 1:
          note.tappable = 0
        #If it is the middle of a HOPO, it's really the end of a HOPO
        elif note.tappable == 2:
          note.tappable = 3      
    self.marked = True

    for time, event in self.allEvents:
      if isinstance(event, Tempo):
        bpmNotes.append([time, event])
        continue
      if not isinstance(event, Note):
        continue
        
class Song(object):
  def __init__(self, engine, infoFileName, songTrackName, guitarTrackName, rhythmTrackName, noteFileName, scriptFileName = None, partlist = [parts[GUITAR_PART]]):
    self.engine        = engine
    self.info         = SongInfo(infoFileName)
    self.tracks       = [[Track() for t in range(len(difficulties))] for i in range(len(partlist))]
    self.difficulty   = [difficulties[AMAZING_DIFFICULTY] for i in partlist]
    self._playing     = False
    self.start        = 0.0
    self.noteFileName = noteFileName
    self.bpm          = None
    self.period       = 0
    self.parts        = partlist
    self.delay        = self.engine.config.get("audio", "delay")
    self.delay        += self.info.delay
    self.missVolume   = self.engine.config.get("audio", "miss_volume")

    #RF-mod skip if folder (not needed anymore?)
    #if self.info.folder == True:
    #  return

    # load the tracks
    if songTrackName:
      self.music       = Audio.Music(songTrackName)

    self.guitarTrack = None
    self.rhythmTrack = None

    try:
      if guitarTrackName:
        self.guitarTrack = Audio.StreamingSound(self.engine, self.engine.audio.getChannel(1), guitarTrackName)
    except Exception, e:
      Log.warn("Unable to load guitar track: %s" % e)

    try:
      if rhythmTrackName:
        self.rhythmTrack = Audio.StreamingSound(self.engine, self.engine.audio.getChannel(2), rhythmTrackName)
    except Exception, e:
      Log.warn("Unable to load rhythm track: %s" % e)

    # load the notes   
    if noteFileName:
      midiIn = midi.MidiInFile(MidiReader(self), noteFileName)
      midiIn.read()

    # load the script
    if scriptFileName and os.path.isfile(scriptFileName):
      scriptReader = ScriptReader(self, open(scriptFileName))
      scriptReader.read()

    # update all note tracks
    #HOPO done here (should be in guitar scene, only do the track you are playing)
    #for tracks in self.tracks:
    #  for track in tracks:
    #    track.update()

  def getHash(self):
    h = sha.new()
    f = open(self.noteFileName, "rb")
    bs = 1024
    while True:
      data = f.read(bs)
      if not data: break
      h.update(data)
    return h.hexdigest()
  
  def setBpm(self, bpm):
    self.bpm    = bpm
    self.period = 60000.0 / self.bpm

  def save(self):
    self.info.save()
    f = open(self.noteFileName + ".tmp", "wb")
    midiOut = MidiWriter(self, midi.MidiOutFile(f))
    midiOut.write()
    f.close()

    # Rename the output file after it has been succesfully written
    shutil.move(self.noteFileName + ".tmp", self.noteFileName)

  def play(self, start = 0.0):
    self.start = start
    self.music.play(0, start / 1000.0)
    #RF-mod No longer needed?
    self.music.setVolume(1.0)
    if self.guitarTrack:
      assert start == 0.0
      self.guitarTrack.play()
    if self.rhythmTrack:
      assert start == 0.0
      self.rhythmTrack.play()
    self._playing = True

  def pause(self):
    self.music.pause()
    self.engine.audio.pause()

  def unpause(self):
    self.music.unpause()
    self.engine.audio.unpause()

  def setInstrumentVolume(self, volume, part):
    if part == parts[GUITAR_PART]:
      self.setGuitarVolume(volume)
    else:
      self.setRhythmVolume(volume)
      
  def setGuitarVolume(self, volume):
    if self.guitarTrack:
      if volume == 0:
        self.guitarTrack.setVolume(self.missVolume)
      else:
        self.guitarTrack.setVolume(volume)
    #This is only used if there is no guitar.ogg to lower the volume of song.ogg instead of muting this track
    else:
      if volume == 0:
        self.music.setVolume(self.missVolume * 1.5)
      else:
        self.music.setVolume(volume)

  def setRhythmVolume(self, volume):
    if self.rhythmTrack:
      if volume == 0:
        self.rhythmTrack.setVolume(self.missVolume)
      else:
        self.rhythmTrack.setVolume(volume)
  
  def setBackgroundVolume(self, volume):
    self.music.setVolume(volume)
  
  def stop(self):
    for tracks in self.tracks:
      for track in tracks:
        track.reset()
      
    self.music.stop()
    self.music.rewind()
    if self.guitarTrack:
      self.guitarTrack.stop()
    if self.rhythmTrack:
      self.rhythmTrack.stop()
    self._playing = False

  def fadeout(self, time):
    for tracks in self.tracks:
      for track in tracks:
        track.reset()
    #RF-mod (not needed?)
    #if self.info.folder == True:
    #  return
    
    self.music.fadeout(time)
    if self.guitarTrack:
      self.guitarTrack.fadeout(time)
    if self.rhythmTrack:
      self.rhythmTrack.fadeout(time)
    self._playing = False

  def getPosition(self):
    if not self._playing:
      pos = 0.0
    else:
      pos = self.music.getPosition()
    if pos < 0.0:
      pos = 0.0
    return pos + self.start - self.delay

  def isPlaying(self):
    return self._playing and self.music.isPlaying()

  def getBeat(self):
    return self.getPosition() / self.period

  def update(self, ticks):
    pass

  def getTrack(self):
    return [self.tracks[i][self.difficulty[i].id] for i in range(len(self.difficulty))]

  track = property(getTrack)

noteMap = {     # difficulty, note
  0x60: (AMAZING_DIFFICULTY,  0),
  0x61: (AMAZING_DIFFICULTY,  1),
  0x62: (AMAZING_DIFFICULTY,  2),
  0x63: (AMAZING_DIFFICULTY,  3),
  0x64: (AMAZING_DIFFICULTY,  4),
  0x54: (MEDIUM_DIFFICULTY,   0),
  0x55: (MEDIUM_DIFFICULTY,   1),
  0x56: (MEDIUM_DIFFICULTY,   2),
  0x57: (MEDIUM_DIFFICULTY,   3),
  0x58: (MEDIUM_DIFFICULTY,   4),
  0x48: (EASY_DIFFICULTY,     0),
  0x49: (EASY_DIFFICULTY,     1),
  0x4a: (EASY_DIFFICULTY,     2),
  0x4b: (EASY_DIFFICULTY,     3),
  0x4c: (EASY_DIFFICULTY,     4),
  0x3c: (SUPAEASY_DIFFICULTY, 0),
  0x3d: (SUPAEASY_DIFFICULTY, 1),
  0x3e: (SUPAEASY_DIFFICULTY, 2),
  0x3f: (SUPAEASY_DIFFICULTY, 3),
  0x40: (SUPAEASY_DIFFICULTY, 4),
}

reverseNoteMap = dict([(v, k) for k, v in noteMap.items()])

class MidiWriter:
  def __init__(self, song, out):
    self.song         = song
    self.out          = out
    self.ticksPerBeat = 480

  def midiTime(self, time):
    return int(self.song.bpm * self.ticksPerBeat * time / 60000.0)

  def write(self):
    self.out.header(division = self.ticksPerBeat)
    self.out.start_of_track()
    self.out.update_time(0)
    if self.song.bpm:
      self.out.tempo(int(60.0 * 10.0**6 / self.song.bpm))
    else:
      self.out.tempo(int(60.0 * 10.0**6 / 122.0))

    # Collect all events
    events = [zip([difficulty] * len(track.getAllEvents()), track.getAllEvents()) for difficulty, track in enumerate(self.song.tracks[0])]
    events = reduce(lambda a, b: a + b, events)
    events.sort(lambda a, b: {True: 1, False: -1}[a[1][0] > b[1][0]])
    heldNotes = []

    for difficulty, event in events:
      time, event = event
      if isinstance(event, Note):
        time = self.midiTime(time)

        # Turn off any held notes that were active before this point in time
        for note, endTime in list(heldNotes):
          if endTime <= time:
            self.out.update_time(endTime, relative = 0)
            self.out.note_off(0, note)
            heldNotes.remove((note, endTime))

        note = reverseNoteMap[(difficulty, event.number)]
        self.out.update_time(time, relative = 0)
        self.out.note_on(0, note, event.special and 127 or 100)
        heldNotes.append((note, time + self.midiTime(event.length)))
        heldNotes.sort(lambda a, b: {True: 1, False: -1}[a[1] > b[1]])

    # Turn off any remaining notes
    for note, endTime in heldNotes:
      self.out.update_time(endTime, relative = 0)
      self.out.note_off(0, note)
      
    self.out.update_time(0)
    self.out.end_of_track()
    self.out.eof()
    self.out.write()

class ScriptReader:
  def __init__(self, song, scriptFile):
    self.song = song
    self.file = scriptFile

  def read(self):
    for line in self.file:
      if line.startswith("#") or line.isspace(): continue
      time, length, type, data = re.split("[\t ]+", line.strip(), 3)
      time   = float(time)
      length = float(length)

      if type == "text":
        event = TextEvent(data, length)
      elif type == "pic":
        event = PictureEvent(data, length)
      else:
        continue

      for track in self.song.tracks:
        for t in track:
          t.addEvent(time, event)

class MidiReader(midi.MidiOutStream):
  def __init__(self, song):
    midi.MidiOutStream.__init__(self)
    self.song = song
    self.heldNotes = {}
    self.velocity  = {}
    self.ticksPerBeat = 480
    self.tempoMarkers = []
    self.partTrack = 0
    self.partnumber = -1

  def addEvent(self, track, event, time = None):
    if self.partnumber == -1:
      #Looks like notes have started appearing before any part information. Lets assume its part0
      self.partnumber = self.song.parts[0]
    
    if (self.partnumber == None) and isinstance(event, Note):
      return True

    if time is None:
      time = self.abs_time()
    assert time >= 0
    
    if track is None:
      for t in self.song.tracks:
        for s in t:
          s.addEvent(time, event)
    else:
      
      tracklist = [i for i,j in enumerate(self.song.parts) if self.partnumber == j]
      for i in tracklist:
        #Each track needs it's own copy of the event, otherwise they'll interfere
        eventcopy = copy.deepcopy(event)
        if track < len(self.song.tracks[i]):
          self.song.tracks[i][track].addEvent(time, eventcopy)

  def abs_time(self):
    def ticksToBeats(ticks, bpm):
      return (60000.0 * ticks) / (bpm * self.ticksPerBeat)
      
    if self.song.bpm:
      currentTime = midi.MidiOutStream.abs_time(self)

      # Find out the current scaled time.
      # Yeah, this is reeally slow, but fast enough :)
      scaledTime      = 0.0
      tempoMarkerTime = 0.0
      currentBpm      = self.song.bpm
      for i, marker in enumerate(self.tempoMarkers):
        time, bpm = marker
        if time > currentTime:
          break
        scaledTime += ticksToBeats(time - tempoMarkerTime, currentBpm)
        tempoMarkerTime, currentBpm = time, bpm
      return scaledTime + ticksToBeats(currentTime - tempoMarkerTime, currentBpm)
    return 0.0

  def header(self, format, nTracks, division):
    self.ticksPerBeat = division
    if nTracks == 2:
      self.partTrack = 1
    
  def tempo(self, value):
    bpm = 60.0 * 10.0**6 / value
    self.tempoMarkers.append((midi.MidiOutStream.abs_time(self), bpm))
    if not self.song.bpm:
      self.song.setBpm(bpm)
    self.addEvent(None, Tempo(bpm))

  def sequence_name(self, text):
    #if self.get_current_track() == 0:
    self.partnumber = None
      
    if (text == "PART GUITAR" or text == "T1 GEMS" or text == "Click" or text == "MIDI out") and parts[GUITAR_PART] in self.song.parts:
      self.partnumber = parts[GUITAR_PART]
    elif text == "PART RHYTHM" and parts[RHYTHM_PART] in self.song.parts:
      self.partnumber = parts[RHYTHM_PART]
    elif text == "PART BASS" and parts[BASS_PART] in self.song.parts:
      self.partnumber = parts[BASS_PART]
    elif text == "PART GUITAR COOP" and parts[LEAD_PART] in self.song.parts:
      self.partnumber = parts[LEAD_PART]
    elif self.get_current_track() <= 1 and parts [GUITAR_PART] in self.song.parts:
      #Oh dear, the track wasn't recognised, lets just assume it was the guitar part
      self.partnumber = parts[GUITAR_PART]
      
  def note_on(self, channel, note, velocity):
    if self.partnumber == None:
      return
    self.velocity[note] = velocity
    self.heldNotes[(self.get_current_track(), channel, note)] = self.abs_time()

  def note_off(self, channel, note, velocity):
    if self.partnumber == None:
      return
    try:
      startTime = self.heldNotes[(self.get_current_track(), channel, note)]
      endTime   = self.abs_time()
      del self.heldNotes[(self.get_current_track(), channel, note)]
      if note in noteMap:
        track, number = noteMap[note]
        self.addEvent(track, Note(number, endTime - startTime, special = self.velocity[note] == 127), time = startTime)
      else:
        #Log.warn("MIDI note 0x%x at %d does not map to any game note." % (note, self.abs_time()))
        pass
    except KeyError:
      Log.warn("MIDI note 0x%x on channel %d ending at %d was never started." % (note, channel, self.abs_time()))
      
class MidiInfoReader(midi.MidiOutStream):
  # We exit via this exception so that we don't need to read the whole file in
  class Done: pass
  
  def __init__(self):
    midi.MidiOutStream.__init__(self)
    self.difficulties = []

  def note_on(self, channel, note, velocity):
    try:
      track, number = noteMap[note]
      diff = difficulties[track]
      if not diff in self.difficulties:
        self.difficulties.append(diff)
        #ASSUMES ALL parts (lead, rhythm, bass) have same difficulties of guitar part!
        if len(self.difficulties) == len(difficulties):
           raise Done
    except KeyError:
      pass

class MidiPartsReader(midi.MidiOutStream):
  # We exit via this exception so that we don't need to read the whole file in
  class Done: pass
  
  def __init__(self):
    midi.MidiOutStream.__init__(self)
    self.parts = []
    
  def sequence_name(self, text):

    if text == "PART GUITAR" or text == "T1 GEMS" or text == "Click":
      if not parts[GUITAR_PART] in self.parts:
        part = parts[GUITAR_PART]
        self.parts.append(part)

    if text == "PART RHYTHM":
      if not parts[RHYTHM_PART] in self.parts:
        part = parts[RHYTHM_PART]
        self.parts.append(part)        
     
    if text == "PART BASS":
      if not parts[BASS_PART] in self.parts:
        part = parts[BASS_PART]
        self.parts.append(part)

    if text == "PART GUITAR COOP":
      if not parts[LEAD_PART] in self.parts:
        part = parts[LEAD_PART]
        self.parts.append(part)

def loadSong(engine, name, library = DEFAULT_LIBRARY, seekable = False, playbackOnly = False, notesOnly = False, part = [parts[GUITAR_PART]]):
  #RF-mod (not needed?)
  #library = Config.get("game", "selected_library")
  guitarFile = engine.resource.fileName(library, name, "guitar.ogg")
  songFile   = engine.resource.fileName(library, name, "song.ogg")
  rhythmFile = engine.resource.fileName(library, name, "rhythm.ogg")
  noteFile   = engine.resource.fileName(library, name, "notes.mid", writable = True)
  infoFile   = engine.resource.fileName(library, name, "song.ini", writable = True)
  scriptFile = engine.resource.fileName(library, name, "script.txt")
  previewFile = engine.resource.fileName(library, name, "preview.ogg")
  
  if seekable:
    if os.path.isfile(guitarFile) and os.path.isfile(songFile):
      # TODO: perform mixing here
      songFile   = guitarFile
      guitarFile = None
      rhythmFile = ""
    else:
      songFile   = guitarFile
      guitarFile = None
      rhythmFile = ""
      
  if not os.path.isfile(songFile):
    songFile   = guitarFile
    guitarFile = None
  
  if not os.path.isfile(rhythmFile):
    rhythmFile = None
  
  if playbackOnly:
    noteFile = None
    if os.path.isfile(previewFile):
      songFile = previewFile
      guitarFile = None
      rhythmFile = None
      
  if notesOnly:
    songFile = None
    guitarFile = None
    rhythmFile = None
    previewFile = None

  if songFile != None and guitarFile != None:
    #check for the same file
    songStat = os.stat(songFile)
    guitarStat = os.stat(guitarFile)
    #Simply checking file size, no md5
    if songStat.st_size == guitarStat.st_size:
      guitarFile = None
  
  song       = Song(engine, infoFile, songFile, guitarFile, rhythmFile, noteFile, scriptFile, part)
  return song

def loadSongInfo(engine, name, library = DEFAULT_LIBRARY):
  #RF-mod (not needed?)
  #library = Config.get("game", "selected_library")
  infoFile   = engine.resource.fileName(library, name, "song.ini", writable = True)
  return SongInfo(infoFile)
  
def createSong(engine, name, guitarTrackName, backgroundTrackName, rhythmTrackName = None, library = DEFAULT_LIBRARY):
  #RF-mod (not needed?)
  #library = Config.get("game", "selected_library")
  path = os.path.abspath(engine.resource.fileName(library, name, writable = True))
  os.makedirs(path)
  
  guitarFile = engine.resource.fileName(library, name, "guitar.ogg", writable = True)
  songFile   = engine.resource.fileName(library, name, "song.ogg",   writable = True)
  noteFile   = engine.resource.fileName(library, name, "notes.mid",  writable = True)
  infoFile   = engine.resource.fileName(library, name, "song.ini",   writable = True)
  
  shutil.copy(guitarTrackName, guitarFile)
  
  if backgroundTrackName:
    shutil.copy(backgroundTrackName, songFile)
  else:
    songFile   = guitarFile
    guitarFile = None

  if rhythmTrackName:
    rhythmFile = engine.resource.fileName(library, name, "rhythm.ogg", writable = True)
    shutil.copy(rhythmTrackName, rhythmFile)
  else:
    rhythmFile = None
    
  f = open(noteFile, "wb")
  m = midi.MidiOutFile(f)
  m.header()
  m.start_of_track()
  m.update_time(0)
  m.end_of_track()
  m.eof()
  m.write()
  f.close()

  song = Song(engine, infoFile, songFile, guitarFile, rhythmFile, noteFile)
  song.info.name = name
  song.save()
  
  return song

def getDefaultLibrary(engine):
  return LibraryInfo(DEFAULT_LIBRARY, engine.resource.fileName(DEFAULT_LIBRARY, "library.ini"))

def getAvailableLibraries(engine, library = DEFAULT_LIBRARY):
  # Search for libraries in both the read-write and read-only directories
  songRoots    = [engine.resource.fileName(library),
                  engine.resource.fileName(library, writable = True)]
  libraries    = []
  libraryRoots = []

  for songRoot in set(songRoots):
    if (os.path.exists(songRoot) == False):
      return libraries
    for libraryRoot in os.listdir(songRoot):
      libraryRoot = os.path.join(songRoot, libraryRoot)
      if not os.path.isdir(libraryRoot):
        continue
      if os.path.isfile(os.path.join(libraryRoot, "notes.mid")):
        continue
      libName = library + os.path.join(libraryRoot.replace(songRoot, ""))
      libraries.append(LibraryInfo(libName, os.path.join(libraryRoot, "library.ini")))
      continue
      dirs = os.listdir(libraryRoot)
      for name in dirs:
        if os.path.isfile(os.path.join(libraryRoot, name, "song.ini")):
          if not libraryRoot in libraryRoots:
            libName = library + os.path.join(libraryRoot.replace(songRoot, ""))
            libraries.append(LibraryInfo(libName, os.path.join(libraryRoot, "library.ini")))
            libraryRoots.append(libraryRoot)

  libraries.sort(lambda a, b: cmp(a.name.lower(), b.name.lower()))
  return libraries

def getAvailableSongs(engine, library = DEFAULT_LIBRARY, includeTutorials = False):
  order = engine.config.get("game", "sort_order")
  # Search for songs in both the read-write and read-only directories
  if library == None:
    return []
  songRoots = [engine.resource.fileName(library), engine.resource.fileName(library, writable = True)]
  names = []
  for songRoot in songRoots:
    if (os.path.exists(songRoot) == False):
      return []
    for name in os.listdir(songRoot):
      if not os.path.isfile(os.path.join(songRoot, name, "notes.mid")):
        continue
      if not os.path.isfile(os.path.join(songRoot, name, "song.ini")) or name.startswith("."):
        continue
      if not name in names:
        names.append(name)

  songs = [SongInfo(engine.resource.fileName(library, name, "song.ini", writable = True)) for name in names]
  if not includeTutorials:
    songs = [song for song in songs if not song.tutorial]
  songs = [song for song in songs if not song.artist == '=FOLDER=']
  if order == 1:
    songs.sort(lambda a, b: cmp(a.artist.lower(), b.artist.lower()))
  else:
    songs.sort(lambda a, b: cmp(a.name.lower(), b.name.lower()))
  return songs
