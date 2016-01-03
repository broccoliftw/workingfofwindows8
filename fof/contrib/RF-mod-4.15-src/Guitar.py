#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyostila                                  #
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

import Player
from Song import Note, Tempo
from Mesh import Mesh
import Theme

from OpenGL.GL import *
import math

#KEYS = [Player.KEY1, Player.KEY2, Player.KEY3, Player.KEY4, Player.KEY5]
PLAYER1KEYS    = [Player.KEY1, Player.KEY2, Player.KEY3, Player.KEY4, Player.KEY5]
PLAYER1ACTIONS = [Player.ACTION1, Player.ACTION2]
PLAYER2KEYS    = [Player.PLAYER_2_KEY1, Player.PLAYER_2_KEY2, Player.PLAYER_2_KEY3, Player.PLAYER_2_KEY4, Player.PLAYER_2_KEY5]
PLAYER2ACTIONS = [Player.PLAYER_2_ACTION1, Player.PLAYER_2_ACTION2]


class Guitar:
  def __init__(self, engine, editorMode = False, player = 0):
    self.engine         = engine
    self.boardWidth     = 4.0
    self.boardLength    = 12.0
    self.beatsPerBoard  = 5.0
    self.strings        = 5
    self.fretWeight     = [0.0] * self.strings
    self.fretActivity   = [0.0] * self.strings
    self.fretColors     = Theme.fretColors
    self.playedNotes    = []
    self.missedNotes    = []
    self.editorMode     = editorMode
    self.selectedString = 0
    self.time           = 0.0
    self.pickStartPos   = 0
    self.leftyMode      = False
    self.currentBpm     = 50.0
    self.currentPeriod  = 60000.0 / self.currentBpm
    self.targetBpm      = self.currentBpm
    self.targetPeriod   = 60000.0 / self.targetBpm
    self.lastBpmChange  = -1.0
    self.baseBeat       = 0.0

    self.twoChord       = 0
    self.hopoActive     = 0
    self.hopoLast       = -1
    self.hopoColor      = (0, .5, .5)
    self.player         = player
    self.scoreMultiplier = 1
    
    if player == 0:
      self.keys = PLAYER1KEYS
      self.actions = PLAYER1ACTIONS
      #self.ACTION1 = Player.ACTION1
      #self.ACTION2 = Player.ACTION2
    else:
      self.keys = PLAYER2KEYS
      self.actions = PLAYER2ACTIONS
      #self.ACTION1 = Player.PLAYER_2_ACTION1
      #self.ACTION2 = Player.PLAYER_2_ACTION2    
    
    self.setBPM(self.currentBpm)

    engine.resource.load(self,  "noteMesh", lambda: Mesh(engine.resource.fileName("note.dae")))
    engine.resource.load(self,  "keyMesh",  lambda: Mesh(engine.resource.fileName("key.dae")))
    engine.loadSvgDrawing(self, "glowDrawing", "glow.svg",  textureSize = (128, 128))
    engine.loadSvgDrawing(self, "neckDrawing", "neck.svg",  textureSize = (256, 256))
    engine.loadSvgDrawing(self, "hitflames1Drawing", "hitflames1.svg",  textureSize = (128, 128))
    engine.loadSvgDrawing(self, "hitflames2Drawing", "hitflames2.svg",  textureSize = (128, 128))
    engine.loadSvgDrawing(self, "hitglowDrawing", "hitglow.svg",  textureSize = (128, 128))
    engine.loadSvgDrawing(self, "hitglow2Drawing", "hitglow2.svg",  textureSize = (128, 128))


    self.hopoColor  = Theme.hopoColor
    self.spotColor = Theme.spotColor   
    self.keyColor = Theme.keyColor
    self.key2Color = Theme.key2Color
    self.tracksColor = Theme.tracksColor
    self.barsColor = Theme.barsColor
    self.flameColors = Theme.flameColors
    self.flameSizes = Theme.flameSizes
    self.glowColor  = Theme.glowColor
    
    
    self.twoChordMax = self.engine.config.get("player%d" % (player), "two_chord_max")
    self.disableVBPM  = self.engine.config.get("game", "disable_vbpm")
    self.disableNoteSFX  = self.engine.config.get("video", "disable_notesfx")
    self.disableFretSFX  = self.engine.config.get("video", "disable_fretsfx")
    self.disableFlameSFX  = self.engine.config.get("video", "disable_flamesfx")

    
  def selectPreviousString(self):
    self.selectedString = (self.selectedString - 1) % self.strings

  def selectString(self, string):
    self.selectedString = string % self.strings

  def selectNextString(self):
    self.selectedString = (self.selectedString + 1) % self.strings

  def setBPM(self, bpm):
    self.earlyMargin       = 60000.0 / bpm / 3.5
    self.lateMargin        = 60000.0 / bpm / 3.5
    self.noteReleaseMargin = 60000.0 / bpm / 2
    self.currentBpm        = bpm
    self.targetBpm         = bpm
    self.baseBeat          = 0.0

  def setDynamicBPM(self, bpm):
    #if bpm > 110:
    #  bpm = 110
    self.earlyMargin       = 60000.0 / bpm / 3.5
    self.lateMargin        = 60000.0 / bpm / 3.5
    self.noteReleaseMargin = 60000.0 / bpm / 2
    
  def setMultiplier(self, multiplier):
    self.scoreMultiplier = multiplier
    
  def renderNeck(self, visibility, song, pos):
    if not song:
      return

    def project(beat):
      return .5 * beat / beatsPerUnit

    v            = visibility
    w            = self.boardWidth
    l            = self.boardLength

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 

    glEnable(GL_TEXTURE_2D)
    self.neckDrawing.texture.bind()
    
    glBegin(GL_TRIANGLE_STRIP)
    glColor4f(1, 1, 1, 0)
    glTexCoord2f(0.0, project(offset - 2 * beatsPerUnit))
    glVertex3f(-w / 2, 0, -2)
    glTexCoord2f(1.0, project(offset - 2 * beatsPerUnit))
    glVertex3f( w / 2, 0, -2)
    
    glColor4f(1, 1, 1, v)
    glTexCoord2f(0.0, project(offset - 1 * beatsPerUnit))
    glVertex3f(-w / 2, 0, -1)
    glTexCoord2f(1.0, project(offset - 1 * beatsPerUnit))
    glVertex3f( w / 2, 0, -1)
    
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit * .7))
    glVertex3f(-w / 2, 0, l * .7)
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit * .7))
    glVertex3f( w / 2, 0, l * .7)
    
    glColor4f(1, 1, 1, 0)
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit))
    glVertex3f(-w / 2, 0, l)
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit))
    glVertex3f( w / 2, 0, l)
    glEnd()
    
    glDisable(GL_TEXTURE_2D)
    
  def renderTracks(self, visibility):
    if self.tracksColor[0] == -1:
      return
    w = self.boardWidth / self.strings
    v = 1.0 - visibility

    if self.editorMode:
      x = (self.strings / 2 - self.selectedString) * w
      s = 2 * w / self.strings
      z1 = -0.5 * visibility ** 2
      z2 = (self.boardLength - 0.5) * visibility ** 2
      
      glColor4f(1, 1, 1, .15)
      
      glBegin(GL_TRIANGLE_STRIP)
      glVertex3f(x - s, 0, z1)
      glVertex3f(x + s, 0, z1)
      glVertex3f(x - s, 0, z2)
      glVertex3f(x + s, 0, z2)
      glEnd()

    sw = 0.025
    for n in range(self.strings - 1, -1, -1):
      glBegin(GL_TRIANGLE_STRIP)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], 0)
      glVertex3f((n - self.strings / 2) * w - sw, -v, -2)
      glVertex3f((n - self.strings / 2) * w + sw, -v, -2)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], (1.0 - v) * .75)
      glVertex3f((n - self.strings / 2) * w - sw, -v, -1)
      glVertex3f((n - self.strings / 2) * w + sw, -v, -1)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], (1.0 - v) * .75)
      glVertex3f((n - self.strings / 2) * w - sw, -v, self.boardLength * .7)
      glVertex3f((n - self.strings / 2) * w + sw, -v, self.boardLength * .7)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], 0)
      glVertex3f((n - self.strings / 2) * w - sw, -v, self.boardLength)
      glVertex3f((n - self.strings / 2) * w + sw, -v, self.boardLength)
      glEnd()
      v *= 2
      
      
  def renderBars(self, visibility, song, pos):
    if not song or self.tracksColor[0] == -1:
      return
    
    w            = self.boardWidth
    v            = 1.0 - visibility
    sw           = 0.02
    beatsPerUnit = self.beatsPerBoard / self.boardLength
    pos         -= self.lastBpmChange
    offset       = pos / self.currentPeriod * beatsPerUnit
    currentBeat  = pos / self.currentPeriod
    beat         = int(currentBeat)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    glPushMatrix()
    while beat < currentBeat + self.beatsPerBoard:
      z = (beat - currentBeat) / beatsPerUnit

      if z > self.boardLength * .8:
        c = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        c = max(0, 1 + z)
      else:
        c = 1.0
        
      glRotate(v * 90, 0, 0, 1)

      if (beat % 1.0) < 0.001:
        glColor4f(self.barsColor[0], self.barsColor[1], self.barsColor[2], visibility * c * .75)
      else:
        glColor4f(self.barsColor[0], self.barsColor[1], self.barsColor[2], visibility * c * .5)

      glBegin(GL_TRIANGLE_STRIP)
      glVertex3f(-(w / 2), -v, z + sw)
      glVertex3f(-(w / 2), -v, z - sw)
      glVertex3f(w / 2,    -v, z + sw)
      glVertex3f(w / 2,    -v, z - sw)
      glEnd()
      
      if self.editorMode:
        beat += 1.0 / 4.0
      else:
        beat += 1
    glPopMatrix()

    Theme.setSelectedColor(visibility * .5)
    glBegin(GL_TRIANGLE_STRIP)
    glVertex3f(-w / 2, 0,  sw)
    glVertex3f(-w / 2, 0, -sw)
    glVertex3f(w / 2,  0,  sw)
    glVertex3f(w / 2,  0, -sw)
    glEnd()

  def renderNote(self, length, color, flat = False, tailOnly = False, isTappable = False):
    if not self.noteMesh:
      return

    glColor4f(*color)

    if flat:
      glScalef(1, .1, 1)

    size = (.1, length + 0.00001)
    glBegin(GL_TRIANGLE_STRIP)
    glVertex3f(-size[0], 0, 0)
    glVertex3f( size[0], 0, 0)
    glVertex3f(-size[0], 0, size[1])
    glVertex3f( size[0], 0, size[1])
    glEnd()

    if tailOnly:
      return

    #mesh = outer ring (black) 
    #mesh_001 = main note (key color) 
    #mesh_002 = top (spot or hopo if no mesh_003) 
    #mesh_003 = hopo bump (hopo color)
    
    glPushMatrix()
    glEnable(GL_DEPTH_TEST)
    glDepthMask(1)
    glShadeModel(GL_SMOOTH)

    self.noteMesh.render("Mesh_001")
    glColor3f(self.spotColor[0], self.spotColor[1], self.spotColor[2])
    if isTappable:
      if self.hopoColor[0] == -2:
        glColor4f(*color)
      else:
        glColor3f(self.hopoColor[0], self.hopoColor[1], self.hopoColor[2])
      if(self.noteMesh.find("Mesh_003")) == True:
        self.noteMesh.render("Mesh_003")
        glColor3f(self.spotColor[0], self.spotColor[1], self.spotColor[2])
    self.noteMesh.render("Mesh_002")
    glColor3f(0, 0, 0)
    self.noteMesh.render("Mesh")



    glDepthMask(0)
    glPopMatrix()

  def renderNotes(self, visibility, song, pos):
    if not song:
      return

    # Update dynamic period
    self.currentPeriod = round(60000.0 / self.currentBpm, 4)
    self.targetPeriod  = round(60000.0 / self.targetBpm, 4)

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    w = self.boardWidth / self.strings
    track = song.track[self.player]

    for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
      if isinstance(event, Tempo):
        if self.lastBpmChange > 0 and self.disableVBPM == True:
            continue
        if (pos - time > self.currentPeriod or self.lastBpmChange < 0) and time > self.lastBpmChange:
          self.baseBeat         += (time - self.lastBpmChange) / self.currentPeriod
          self.targetBpm         = event.bpm
          self.lastBpmChange     = time
          self.setDynamicBPM(self.targetBpm)
        continue
      
      if not isinstance(event, Note):
        continue
        
      c = self.fretColors[event.number]

      x  = (self.strings / 2 - event.number) * w
      z  = ((time - pos) / self.currentPeriod) / beatsPerUnit
      z2 = ((time + event.length - pos) / self.currentPeriod) / beatsPerUnit

      if z > self.boardLength * .8:
        f = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        f = min(1, max(0, 1 + z2))
      else:
        f = 1.0

      color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)
      length     = event.length / self.currentPeriod / beatsPerUnit
      flat       = False
      tailOnly   = False


      if event.tappable < 2:
        isTappable = False
      else:
        isTappable = True
      
      # Clip the played notes to the origin
      if z < 0:
        if event.played or event.hopod:
          tailOnly = True
          length += z
          z = 0
          if length <= 0:
            continue
        else:
          color = (.2 + .4, .2 + .4, .2 + .4, .5 * visibility * f)
          flat  = True

      if z + length < -1.0:
        continue
      glPushMatrix()
      glTranslatef(x, (1.0 - visibility) ** (event.number + 1), z)
        
      self.renderNote(length, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable)
      glPopMatrix()


    # Draw a waveform shape over the currently playing notes

    if self.disableNoteSFX == True:
      return
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    for time, event in self.playedNotes:
      step  = self.currentPeriod / 16
      t     = time + event.length
      x     = (self.strings / 2 - event.number) * w
      c     = self.fretColors[event.number]
      s     = t
      proj  = 1.0 / self.currentPeriod / beatsPerUnit
      zStep = step * proj

      def waveForm(t):
        u = ((t - time) * -.1 + pos - time) / 64.0 + .0001
        return (math.sin(event.number + self.time * -.01 + t * .03) + math.cos(event.number + self.time * .01 + t * .02)) * .1 + .1 + math.sin(u) / (5 * u)

      glBegin(GL_TRIANGLE_STRIP)
      f1 = 0
      while t > time:
        z  = (t - pos) * proj
        if z < 0:
          break
        f2 = min((s - t) / (6 * step), 1.0)
        a1 = waveForm(t) * f1
        a2 = waveForm(t - step) * f2
        glColor4f(c[0], c[1], c[2], .5)
        glVertex3f(x - a1, 0, z)
        glVertex3f(x - a2, 0, z - zStep)
        glColor4f(1, 1, 1, .75)
        glVertex3f(x, 0, z)
        glVertex3f(x, 0, z - zStep)
        glColor4f(c[0], c[1], c[2], .5)
        glVertex3f(x + a1, 0, z)
        glVertex3f(x + a2, 0, z - zStep)
        glVertex3f(x + a2, 0, z - zStep)
        glVertex3f(x - a2, 0, z - zStep)
        t -= step
        f1 = f2
      glEnd()
      
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

  def renderFrets(self, visibility, song, controls):
    w = self.boardWidth / self.strings
    size = (.22, .22)
    v = 1.0 - visibility
    
    glEnable(GL_DEPTH_TEST)
    
    for n in range(self.strings):
      f = self.fretWeight[n]
      c = self.fretColors[n]

      if f and (controls.getState(self.actions[0]) or controls.getState(self.actions[1])):
        f += 0.25

      glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)
      y = v + f / 6
      x = (self.strings / 2 - n) * w

      if self.keyMesh:
        glPushMatrix()
        glTranslatef(x, y + v * 6, 0)
        glDepthMask(1)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glShadeModel(GL_SMOOTH)
        glRotatef(90, 0, 1, 0)
        glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 10.0, -10.0, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT,  (.2, .2, .2, 0.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  (1.0, 1.0, 1.0, 0.0))
        glRotatef(-90, 1, 0, 0)
        glRotatef(-90, 0, 0, 1)
        glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)

        #Mesh - Main fret
        #Key_001 - Top of fret (key_color)
        #Key_002 - Bottom of fret (key2_color)
        #Glow_001 - Only rendered when a note is hit along with the glow.svg
        
        if(self.keyMesh.find("Glow_001")) == True:
          self.keyMesh.render("Mesh")
          glColor3f(self.keyColor[0], self.keyColor[1], self.keyColor[2])
          self.keyMesh.render("Key_001")
          glColor3f(self.key2Color[0], self.key2Color[1], self.key2Color[2])
          self.keyMesh.render("Key_002")
        else:
          self.keyMesh.render()
          
        glDisable(GL_LIGHTING)
        glDisable(GL_LIGHT0)
        glDepthMask(0)
        glPopMatrix()

      f = self.fretActivity[n]

      if f and self.disableFretSFX != True:
        glBlendFunc(GL_ONE, GL_ONE)

        if self.glowColor[0] == -1:
          s = 1.0
        else:
          s = 0.0
          
        while s < 1:
          ms = s * (math.sin(self.time) * .25 + 1)
          if self.glowColor[0] == -2:
            glColor3f(c[0] * (1 - ms), c[1] * (1 - ms), c[2] * (1 - ms))
          else:
            glColor3f(self.glowColor[0] * (1 - ms), self.glowColor[1] * (1 - ms), self.glowColor[2] * (1 - ms))
            
          glPushMatrix()
          glTranslate(x, y, 0)
          glScalef(1 + .6 * ms * f, 1 + .6 * ms * f, 1 + .6 * ms * f)
          glRotatef( 90, 0, 1, 0)
          glRotatef(-90, 1, 0, 0)
          glRotatef(-90, 0, 0, 1)
          if(self.keyMesh.find("Glow_001")) == True:
            self.keyMesh.render("Glow_001")
          else:
            self.keyMesh.render()
          glPopMatrix()
          s += 0.2

        glColor3f(c[0], c[1], c[2])
        glEnable(GL_TEXTURE_2D)
        self.glowDrawing.texture.bind()
        f += 2

        glPushMatrix()
        glTranslate(x, y, 0)
        glRotate(f * 90 + self.time, 0, 1, 0)
        glBegin(GL_TRIANGLE_STRIP)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-size[0] * f, 0, -size[1] * f)
        glTexCoord2f(1.0, 0.0)
        glVertex3f( size[0] * f, 0, -size[1] * f)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-size[0] * f, 0,  size[1] * f)
        glTexCoord2f(1.0, 1.0)
        glVertex3f( size[0] * f, 0,  size[1] * f)
        glEnd()
        glPopMatrix()
        
        glDisable(GL_TEXTURE_2D)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

      v *= 1.5
    glDisable(GL_DEPTH_TEST)

  def renderFlames(self, visibility, song, pos, controls):
    if not song or self.flameColors[0][0][0] == -1:
      return

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    w = self.boardWidth / self.strings
    track = song.track[self.player]

    size = (.22, .22)
    v = 1.0 - visibility

    if self.disableFlameSFX != True:
      for n in range(self.strings):
        f = self.fretWeight[n]
        c = self.fretColors[n]
        if f and (controls.getState(self.actions[0]) or controls.getState(self.actions[1])):
          f += 0.25      
        y = v + f / 6
        x = (self.strings / 2 - n) * w
        f = self.fretActivity[n]

        if f:
          ms = math.sin(self.time) * .25 + 1
          ff = f
          ff += 1.2
          
          glBlendFunc(GL_ONE, GL_ONE)
          
          flameSize = self.flameSizes[self.scoreMultiplier - 1][n]        
          flameColor = self.flameColors[self.scoreMultiplier - 1][n]
          if flameColor[0] == -2:
            flameColor = self.fretColors[n]

          flameColorMod0 = 1.1973333333333333333333333333333
          flameColorMod1 = 1.9710526315789473684210526315789
          flameColorMod2 = 10.592592592592592592592592592593

          glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)          
          glEnable(GL_TEXTURE_2D)
          self.hitglowDrawing.texture.bind()    
          glPushMatrix()
          glTranslate(x, y + .125, 0)
          glRotate(90, 1, 0, 0)
          glScalef(0.5 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff)
          glBegin(GL_TRIANGLE_STRIP)
          glTexCoord2f(0.0, 0.0)
          glVertex3f(-flameSize * ff, 0, -flameSize * ff)
          glTexCoord2f(1.0, 0.0)
          glVertex3f( flameSize * ff, 0, -flameSize * ff)
          glTexCoord2f(0.0, 1.0)
          glVertex3f(-flameSize * ff, 0,  flameSize * ff)
          glTexCoord2f(1.0, 1.0)
          glVertex3f( flameSize * ff, 0,  flameSize * ff)
          glEnd()
          glPopMatrix()
          glDisable(GL_TEXTURE_2D)

          ff += .3

          #flameSize = self.flameSizes[self.scoreMultiplier - 1][n]
          #flameColor = self.flameColors[self.scoreMultiplier - 1][n]

          flameColorMod0 = 1.1973333333333333333333333333333
          flameColorMod1 = 1.7842105263157894736842105263158
          flameColorMod2 = 12.222222222222222222222222222222
          
          glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
          glEnable(GL_TEXTURE_2D)
          self.hitglow2Drawing.texture.bind()    
          glPushMatrix()
          glTranslate(x, y + .25, .05)
          glRotate(90, 1, 0, 0)
          glScalef(.40 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff)
          glBegin(GL_TRIANGLE_STRIP)
          glTexCoord2f(0.0, 0.0)
          glVertex3f(-flameSize * ff, 0, -flameSize * ff)
          glTexCoord2f(1.0, 0.0)
          glVertex3f( flameSize * ff, 0, -flameSize * ff)
          glTexCoord2f(0.0, 1.0)
          glVertex3f(-flameSize * ff, 0,  flameSize * ff)
          glTexCoord2f(1.0, 1.0)
          glVertex3f( flameSize * ff, 0,  flameSize * ff)
          glEnd()
          glPopMatrix()
          glDisable(GL_TEXTURE_2D)
          
          glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    if self.disableFlameSFX != True:
      flameLimit = 10.0
      flameLimitHalf = round(flameLimit/2.0)
      for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
        if isinstance(event, Tempo):
          continue
        
        if not isinstance(event, Note):
          continue
        
        if (event.played or event.hopod) and event.flameCount < flameLimit:
          ms = math.sin(self.time) * .25 + 1
          x  = (self.strings / 2 - event.number) * w
          ff = 1 + 0.25       
          y = v + ff / 6
          glBlendFunc(GL_ONE, GL_ONE)
          
          flameSize = self.flameSizes[self.scoreMultiplier - 1][event.number]
          flameColor = self.flameColors[self.scoreMultiplier - 1][event.number]
          if flameColor[0] == -2:
            flameColor = self.fretColors[event.number]
          
          ff += 1.5

          if event.flameCount < flameLimitHalf:
            glColor3f(flameColor[0], flameColor[1], flameColor[2])
            glEnable(GL_TEXTURE_2D)
            self.hitflames2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x, y + .20, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.25 + .6 * ms * ff, event.flameCount/6.0 + .6 * ms * ff, event.flameCount / 6.0 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()
            glDisable(GL_TEXTURE_2D) 

            glColor3f(flameColor[0], flameColor[1], flameColor[2])           
            glEnable(GL_TEXTURE_2D)
            self.hitflames2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x - .005, y + .25 + .005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.30 + .6 * ms * ff, (event.flameCount + 1) / 5.5 + .6 * ms * ff, (event.flameCount + 1) / 5.5 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()	  
            glDisable(GL_TEXTURE_2D)

            glColor3f(flameColor[0], flameColor[1], flameColor[2])
            glEnable(GL_TEXTURE_2D)
            self.hitflames2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x+.005, y +.25 +.005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.35 + .6 * ms * ff, (event.flameCount + 1) / 5.0 + .6 * ms * ff, (event.flameCount + 1) / 5.0 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()	  
            glDisable(GL_TEXTURE_2D)

            glColor3f(flameColor[0], flameColor[1], flameColor[2])  
            glEnable(GL_TEXTURE_2D)
            self.hitflames2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x, y +.25 +.005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.40 + .6 * ms * ff, (event.flameCount + 1)/ 4.7 + .6 * ms * ff, (event.flameCount + 1) / 4.7 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()	  
            glDisable(GL_TEXTURE_2D)
          else:
            flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
            
            glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
            glEnable(GL_TEXTURE_2D)
            self.hitflames1Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x, y + .35, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.25 + .6 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()
            glDisable(GL_TEXTURE_2D)

            flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
            
            glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)      
            glEnable(GL_TEXTURE_2D)
            self.hitflames1Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x - .005, y + .40 + .005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.30 + .6 * ms * ff, (event.flameCount + 1)/ 2.5 + .6 * ms * ff, (event.flameCount + 1) / 2.5 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()  
            glDisable(GL_TEXTURE_2D)

            flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
            
            glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
            glEnable(GL_TEXTURE_2D)
            self.hitflames1Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x + .005, y + .35 + .005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.35 + .6 * ms * ff, (event.flameCount + 1) / 2.0 + .6 * ms * ff, (event.flameCount + 1) / 2.0 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()  
            glDisable(GL_TEXTURE_2D)

            flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
            
            glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
            glEnable(GL_TEXTURE_2D)
            self.hitflames1Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x+.005, y +.35 +.005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.40 + .6 * ms * ff, (event.flameCount + 1) / 1.7 + .6 * ms * ff, (event.flameCount + 1) / 1.7 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()  
            glDisable(GL_TEXTURE_2D)
         

          glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
          event.flameCount += 1
        
  def render(self, visibility, song, pos, controls):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_COLOR_MATERIAL)
    if self.leftyMode:
      glScale(-1, 1, 1)

    self.renderNeck(visibility, song, pos)
    self.renderTracks(visibility)
    self.renderBars(visibility, song, pos)
    self.renderNotes(visibility, song, pos)
    self.renderFrets(visibility, song, controls)
    self.renderFlames(visibility, song, pos, controls)
    
    if self.leftyMode:
      glScale(-1, 1, 1)

  def getMissedNotes(self, song, pos, catchup = False):
    if not song:
      return

    m1      = self.lateMargin
    m2      = self.lateMargin * 2

    #if catchup == True:
    #  m2 = 0
      
    track   = song.track[self.player]
    notes   = [(time, event) for time, event in track.getEvents(pos - m1, pos - m2) if isinstance(event, Note)]
    notes   = [(time, event) for time, event in notes if (time >= (pos - m2)) and (time <= (pos - m1))]
    notes   = [(time, event) for time, event in notes if not event.played and not event.hopod and not event.skipped]

    if catchup == True:
      for time, event in notes:
        event.skipped = True

    return sorted(notes, key=lambda x: x[1].number)        
    #return notes

  def getRequiredNotes(self, song, pos):
    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not event.played]
    notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]
    if notes:
      t     = min([time for time, event in notes])
      notes = [(time, event) for time, event in notes if time - t < 1e-3]
    return sorted(notes, key=lambda x: x[1].number)

  def getRequiredNotes2(self, song, pos, hopo = False):

    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not (event.hopod or event.played)]
    notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]
    if notes:
      t     = min([time for time, event in notes])
      notes = [(time, event) for time, event in notes if time - t < 1e-3]
      
    return sorted(notes, key=lambda x: x[1].number)
    
  def getRequiredNotes3(self, song, pos, hopo = False):

    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not (event.hopod or event.played or event.skipped)]
    notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]
    #if notes:
    #  t     = min([time for time, event in notes])
    #  notes = [(time, event) for time, event in notes if time - t < 1e-3]

    return sorted(notes, key=lambda x: x[1].number)

  def controlsMatchNotes(self, controls, notes):
    # no notes?
    if not notes:
      return False
  
    # check each valid chord
    chords = {}
    for time, note in notes:
      if not time in chords:
        chords[time] = []
      chords[time].append((time, note))

    #Make sure the notes are in the right time order
    chordlist = chords.values()
    chordlist.sort(lambda a, b: cmp(a[0][0], b[0][0]))

    twochord = 0
    for chord in chordlist:
      # matching keys?
      requiredKeys = [note.number for time, note in chord]
      requiredKeys = self.uniqify(requiredKeys)
      
      if len(requiredKeys) > 2 and self.twoChordMax == True:
        twochord = 0
        for n, k in enumerate(self.keys):
          if controls.getState(k):
            twochord += 1
        if twochord == 2:
          skipped = len(requiredKeys) - 2
          requiredKeys = [min(requiredKeys), max(requiredKeys)]
        else:
          twochord = 0

      for n, k in enumerate(self.keys):
        if n in requiredKeys and not controls.getState(k):
          return False
        if not n in requiredKeys and controls.getState(k):
          # The lower frets can be held down
          if n > max(requiredKeys):
            return False
      if twochord != 0:
        if twochord != 2:
          for time, note in chord:
            note.played = True
        else:
          for time, note in chord:
            note.skipped = True
          chord[0][1].skipped = False
          chord[-1][1].skipped = False
          chord[0][1].played = True
          chord[-1][1].played = True
    if twochord == 2:
      self.twoChord += skipped

    return True

  def controlsMatchNotes2(self, controls, notes, hopo = False):
    # no notes?
    if not notes:
      return False

    # check each valid chord
    chords = {}
    for time, note in notes:
      if note.hopod == True and controls.getState(self.keys[note.number]):
      #if hopo == True and controls.getState(self.keys[note.number]):
        self.playedNotes = []
        return True
      if not time in chords:
        chords[time] = []
      chords[time].append((time, note))

    #Make sure the notes are in the right time order
    chordlist = chords.values()
    chordlist.sort(lambda a, b: cmp(a[0][0], b[0][0]))

    twochord = 0
    for chord in chordlist:
      # matching keys?
      requiredKeys = [note.number for time, note in chord]
      requiredKeys = self.uniqify(requiredKeys)

      if len(requiredKeys) > 2 and self.twoChordMax == True:
        twochord = 0
        for n, k in enumerate(self.keys):
          if controls.getState(k):
            twochord += 1
        if twochord == 2:
          skipped = len(requiredKeys) - 2
          requiredKeys = [min(requiredKeys), max(requiredKeys)]
        else:
          twochord = 0
        
      for n, k in enumerate(self.keys):
        if n in requiredKeys and not controls.getState(k):
          return False
        if not n in requiredKeys and controls.getState(k):
          # The lower frets can be held down
          if hopo == False and n >= min(requiredKeys):
            return False
      if twochord != 0:
        if twochord != 2:
          for time, note in chord:
            note.played = True
        else:
          for time, note in chord:
            note.skipped = True
          chord[0][1].skipped = False
          chord[-1][1].skipped = False
          chord[0][1].played = True
          chord[-1][1].played = True
        
    if twochord == 2:
      self.twoChord += skipped
      
    return True

  def controlsMatchNotes3(self, controls, notes, hopo = False):
    # no notes?
    if not notes:
      return False

    # check each valid chord
    chords = {}
    for time, note in notes:
      if note.hopod == True and controls.getState(self.keys[note.number]):
      #if hopo == True and controls.getState(self.keys[note.number]):
        self.playedNotes = []
        return True
      if not time in chords:
        chords[time] = []
      chords[time].append((time, note))

    #Make sure the notes are in the right time order
    chordlist = chords.values()
    chordlist.sort(lambda a, b: cmp(a[0][0], b[0][0]))

    self.missedNotes = []
    twochord = 0
    for chord in chordlist:
      # matching keys?
      requiredKeys = [note.number for time, note in chord]
      requiredKeys = self.uniqify(requiredKeys)

      if len(requiredKeys) > 2 and self.twoChordMax == True:
        twochord = 0
        for n, k in enumerate(self.keys):
          if controls.getState(k):
            twochord += 1
        if twochord == 2:
          skipped = len(requiredKeys) - 2
          requiredKeys = [min(requiredKeys), max(requiredKeys)]
        else:
          twochord = 0
          
      if (self.controlsMatchNote3(controls, chord, requiredKeys, hopo)):
        if twochord != 2:
          for time, note in chord:
            note.played = True
        else:
          for time, note in chord:
            note.skipped = True
          chord[0][1].skipped = False
          chord[-1][1].skipped = False
          chord[0][1].played = True
          chord[-1][1].played = True
        break
      if hopo == True:
        break
      self.missedNotes.append(chord)
    else:
      self.missedNotes = []
    
    for chord in self.missedNotes:
      for time, note in chord:
        note.skipped = True
        note.played = False
    if twochord == 2:
      self.twoChord += skipped
      
    return True

  def uniqify(self, seq, idfun=None): 
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result
  
  def controlsMatchNote3(self, controls, chordTuple, requiredKeys, hopo):
    if len(chordTuple) > 1:
    #Chords must match exactly
      for n, k in enumerate(self.keys):
        if (n in requiredKeys and not controls.getState(k)) or (n not in requiredKeys and controls.getState(k)):
          return False
    else:
    #Single Note must match that note
      requiredKey = requiredKeys[0]
      if not controls.getState(self.keys[requiredKey]):
        return False
      if hopo == False:
      #Check for higher numbered frets if not a HOPO
        for n, k in enumerate(self.keys):
          if n > requiredKey:
          #higher numbered frets cannot be held
            if controls.getState(k):
              return False
    return True

  def areNotesTappable(self, notes):
    if not notes:
      return
    for time, note in notes:
      if note.tappable > 1:
        return True
    return False
  
  def startPick(self, song, pos, controls, hopo = False):
    if hopo == True:
      res = startPick2(song, pos, controls, hopo)
      return res
    if not song:
      return False
    
    self.playedNotes = []
    
    notes = self.getRequiredNotes(song, pos)

    if self.controlsMatchNotes(controls, notes):
      self.pickStartPos = pos
      for time, note in notes:
        if note.skipped == True:
          continue
        self.pickStartPos = max(self.pickStartPos, time)
        note.played       = True
        self.playedNotes.append([time, note])
      return True
    return False

  def startPick2(self, song, pos, controls, hopo = False):
    if not song:
      return False
    
    self.playedNotes = []
    
    notes = self.getRequiredNotes2(song, pos, hopo)

    if self.controlsMatchNotes2(controls, notes, hopo):
      self.pickStartPos = pos
      for time, note in notes:
        if note.skipped == True:
          continue
        self.pickStartPos = max(self.pickStartPos, time)
        if hopo:
          note.hopod        = True
        else:
          note.played       = True
        if note.tappable == 1 or note.tappable == 2:
          self.hopoActive = time
        elif note.tappable == 3:
          self.hopoActive = -time
        else:
          self.hopoActive = 0
        self.playedNotes.append([time, note])
      self.hopoLast     = note.number
      return True
    return False

  def startPick3(self, song, pos, controls, hopo = False):
    if not song:
      return False
    
    self.playedNotes = []
    
    notes = self.getRequiredNotes3(song, pos, hopo)

    self.controlsMatchNotes3(controls, notes, hopo)
    for time, note in notes:
      if note.played != True:
        continue
      self.pickStartPos = pos
      self.pickStartPos = max(self.pickStartPos, time)
      if hopo:
        note.hopod        = True
      else:
        note.played       = True
      if note.tappable == 1 or note.tappable == 2:
        self.hopoActive = time
      elif note.tappable == 3:
        self.hopoActive = -time
      else:
        self.hopoActive = 0
      self.hopoLast     = note.number
      self.playedNotes.append([time, note])
    if len(self.playedNotes) != 0:
      return True
    return False

  def endPick(self, pos):
    for time, note in self.playedNotes:
      if time + note.length > pos + self.noteReleaseMargin:
        self.playedNotes = []
        return False
      
    self.playedNotes = []
    return True
    
  def getPickLength(self, pos):
    if not self.playedNotes:
      return 0.0
    
    # The pick length is limited by the played notes
    pickLength = pos - self.pickStartPos
    for time, note in self.playedNotes:
      pickLength = min(pickLength, note.length)
    return pickLength

  def run(self, ticks, pos, controls):
    self.time += ticks
    
    # update frets
    if self.editorMode:
      if (controls.getState(self.actions[0]) or controls.getState(self.actions[1])):
        activeFrets = [i for i, k in enumerate(self.keys) if controls.getState(k)] or [self.selectedString]
      else:
        activeFrets = []
    else:
      activeFrets = [note.number for time, note in self.playedNotes]
    
    for n in range(self.strings):
      if controls.getState(self.keys[n]) or (self.editorMode and self.selectedString == n):
        self.fretWeight[n] = 0.5
      else:
        self.fretWeight[n] = max(self.fretWeight[n] - ticks / 64.0, 0.0)
      if n in activeFrets:
        self.fretActivity[n] = min(self.fretActivity[n] + ticks / 32.0, 1.0)
      else:
        self.fretActivity[n] = max(self.fretActivity[n] - ticks / 64.0, 0.0)

    for time, note in self.playedNotes:
      if pos > time + note.length:
        return False

    # update bpm
    diff = self.targetBpm - self.currentBpm
    if (round((diff * .03), 4) != 0):
      self.currentBpm = round(self.currentBpm + (diff * .03), 4)
    else:
      self.currentBpm = self.targetBpm

    if self.currentBpm != self.targetBpm:
      self.setDynamicBPM(self.currentBpm)    
    return True
