-------------------------------------------------------------
All lyrics are the property and copyright of their respective 
rights holders and are strictly for educational use only.
-------------------------------------------------------------

LRC2FOF is a lyrics file converter from .LRC format lyrics 
file to script.txt Frets On Fire lyrics format.

How to use:
0) You need to get one .lrc lyrics format file to convert.
Or create one from scratch, for instance with Minilyrics editor.
1) Run LRC2FOF (the program verify self-updates on starting).
2) Click 'Open .lrc file' to load lyrics .lrc format file.
If .lrc source has [offset] tag, the value is showed as 'time shift' value.
3) One can adjust sinchronyzed values by setting Time Shift 
(positive/negative) values.
4) Setting 'Set [ lyrics=True ] in song.ini' to add this value 
in song.ini file and show lyrics with RF-mod.
5) Click 'Convert' to start 'convert process'.
6) Output: at same folder of source .lrc file 
will be created 'script.txt' file.
7) Repeat process with another .lrc file to convert 
or click 'Exit" to go out.

------------------------------------------------------------
Special thanks go to:
- Yannick (YMS lyrics-mod)
- Alex (Rogue-F RF-mod)

------------------------------------------------------------
VERSION HISTORY

LRC2FOF v1.2 (2007.11.30)
- Created a README.TXT file with 'how to use' instructions and 'release version history'.
- Created a 'View Script.txt' button to view output converted file 'script.txt'.
- Cosmetic interface changes: messages, buttons, layout.

LRC2FOF v1.1 (2007.11.29)
- Created a method to read [offset] tag from lyrics files 
made by Minilyrics editor.
For instance, if  offset tag is [offset:-1500] then timeshift = -1 * (offset value).
So, in this case, timeshift = 1500.
- Changed splashscreen time show. If not exist internet connection 
to verify update version then remove splashscreen after timeout.

LRC2FOF v1.0 (2007.11.25)
- Unicode/ANSI for win9x/Me compatibility.
- Interface cosmetic changes.
- Created a checkbox to set lyrics = True in song.ini file.
- Created new methods to read lyrics lines (current and next).
- Created new methods to verify/ignore blank lines.
- Changed splash screen to show current version.

LRC2FOF v0.9 (2007.11.16)
- Changed the method of version verification (speed up).
- Created a 'splash screen' (cosmetic change).
- Changed show window method (for performance).

LRC2FOF v0.8 (2007.11.15)
- Fixed error when no one LRC lyrics file is choosen (when hit cancel button).
- Created a method of version updating: compare local version 
to website version and show window with update version information.

LRC2FOF v0.7 (2007.11.13)
- Changed detection EOF method.
- Changed lines counter method of lrc files.
- Changed format [0:31.41] lyrics detection method.
- Fixed 'blank lines' bug.
- Changed lyrics delay show time values.
- More lrc lyrics formats compatibility.

LRC2FOF v0.6 (2007.11.12)
- Fixed error at lyrics initial time stamp.
- Accept lyrics files that have the first line of the lyric with 
[0:ss] or [1:ss] or [2:ss], etc. as the time stamp.

LRC2FOF v0.5 (2007.11.11)
- Fixed one more error at last lyrics line. 
- Fixed EOF detect, again.
- Change progress bar show method.
- Detect lyrics only formated {minutes:seconds].

LRC2FOF v0.4 (2007.11.11)
- Fixed error when last lyrics line have text. 
- Fixed EOF detect.
- Improve speed in progress bar.

LRC2FOF v0.3 (2007.11.10)
- Fixed delay times to show lyrics.

LRC2FOF v0.2 (2007.11.10)
- Fixed "time shift" problem: setting value was only working before 
"Open .lrc file" button click.
(now can adjust values at any time, before convert button click).

LRC2FOF v0.1 (2007.11.10)
- Initial public release.