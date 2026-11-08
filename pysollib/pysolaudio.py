#!/usr/bin/env python
# -*- mode: python; coding: utf-8; -*-
# ---------------------------------------------------------------------------##
#
# Copyright (C) 1998-2003 Markus Franz Xaver Johannes Oberhumer
# Copyright (C) 2003 Mt. Hood Playing Card Co.
# Copyright (C) 2005-2009 Skomoroh
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
# ---------------------------------------------------------------------------##


# imports
import os
import traceback
from threading import Thread

try:
    import pysolsoundserver
except ImportError:
    pysolsoundserver = None


# Fixed playback volume (0-128); users adjust their device volume instead.
SAMPLE_VOLUME = 75


# ************************************************************************
# * basic audio client
# ************************************************************************

class AbstractAudioClient:

    CAN_PLAY_SOUND = False

    def __init__(self):
        self.server = None
        self.audiodev = None
        self.connected = 0
        self.app = None
        self.sample_priority = -1
        self.sample_loop = 0

    def __del__(self):
        self.destroy()

    # start server - set self.server on success (may also set self.audiodev)
    def startServer(self):
        pass

    # connect to server - set self.audiodev on success
    def connectServer(self, app):
        assert app
        self.app = app
        if self.server is not None:
            try:
                if self._connectServer():
                    self.connected = 1
            except Exception:
                if traceback:
                    traceback.print_exc()
                self.destroy()

    # disconnect and stop server
    def destroy(self):
        if self.audiodev:
            self._destroy()
        self.server = None
        self.audiodev = None
        self.connected = 0
        self.app = None

    #
    # high-level interface
    #

    def playSample(self, name, priority=0, loop=0, volume=-1):
        # print 'AbstractAudioClient.playSample', name
        if self.audiodev is None or not self.app or not self.app.opt.sound:
            return 0
        if priority <= self.sample_priority and self.sample_loop:
            return 0
        obj = self.app.sample_manager.getByName(name)
        if not obj or not obj.absname:
            return 0
        try:
            if self._playSample(obj.absname, priority, loop, volume):
                self.sample_priority = priority
                self.sample_loop = loop
                return 1
        except Exception:
            if traceback:
                traceback.print_exc()
        return 0

    def stopSamples(self):
        if self.audiodev is None:
            return
        try:
            self._stopSamples()
        except Exception:
            if traceback:
                traceback.print_exc()
        self.sample_priority = -1
        self.sample_loop = 0

    def stopSamplesLoop(self):
        if self.audiodev is None:
            return
        try:
            self._stopSamplesLoop()
        except Exception:
            if traceback:
                traceback.print_exc()
        self.sample_priority = -1
        self.sample_loop = 0

    #
    # subclass - core implementation
    #

    def _connectServer(self):
        return 0

    def _destroy(self):
        pass

    def _playSample(self, filename, priority, loop, volume):
        return 0

    def _stopSamples(self):
        pass

    def _stopSamplesLoop(self):
        self._stopSamples()

    #
    # subclass - extensions
    #

    def updateSettings(self):
        pass


# ************************************************************************
# * pysolsoundserver module
# ************************************************************************

class PysolSoundServerModuleClient(AbstractAudioClient):

    CAN_PLAY_SOUND = True

    def __init__(self):
        AbstractAudioClient.__init__(self)

    def startServer(self):
        # use the module
        try:
            import pysolsoundserver
            self.audiodev = pysolsoundserver
            self.audiodev.init()
            self.server = 1
        except Exception:
            if traceback:
                traceback.print_exc()
            self.server = None
            self.audiodev = None

    def cmd(self, cmd):
        return self.audiodev.cmd(cmd)

    # connect to server
    def _connectServer(self):
        r = self.cmd("protocol 6")
        if r != 0:
            return 0
        # self.cmd("debug 1")
        return 1

    # disconnect and stop server
    def _destroy(self):
        self.audiodev.exit()

    #
    #
    #

    def _playSample(self, filename, priority, loop, volume):
        self.cmd("playwav '%s' %d %d %d %d"
                 % (filename, -1, priority, loop, volume))
        return 1

    def _stopSamples(self):
        self.cmd("stopwav")

    def _stopSamplesLoop(self):
        self.cmd("stopwavloop")

    def updateSettings(self):
        if self.audiodev is None or not self.app:
            return
        s = 0
        if self.app.opt.sound:
            s = SAMPLE_VOLUME
        try:
            self.cmd("setwavvol %d" % s)
        except Exception:
            if traceback:
                traceback.print_exc()


# ************************************************************************
# * Win32 winsound audio
# ************************************************************************

class Win32AudioClient(AbstractAudioClient):

    CAN_PLAY_SOUND = True

    def __init__(self):
        AbstractAudioClient.__init__(self)
        import winsound
        self.audiodev = winsound

    def startServer(self):
        pass

    def _playSample(self, filename, priority, loop, volume):
        a = self.audiodev
        flags = a.SND_FILENAME | a.SND_NODEFAULT | a.SND_NOWAIT | a.SND_ASYNC
        if loop:
            flags = flags | a.SND_LOOP
        if priority <= self.sample_priority:
            flags = flags | a.SND_NOSTOP
        # print filename, flags, priority
        try:
            a.PlaySound(filename, flags)
            return 1
        except Exception:
            pass
        return 0

    def _stopSamples(self):
        a = self.audiodev
        flags = a.SND_NODEFAULT | a.SND_PURGE
        a.PlaySound(None, flags)


# ************************************************************************
# * OSS audio
# ************************************************************************

class OSSAudioServer:

    def __init__(self, pipe):
        self.pipe = pipe
        # import ossaudiodev
        # self.audiodev = ossaudiodev.open('w')
        self.sound_priority = -1
        self._busy = False

    def mainLoop(self):
        while True:
            s = os.read(self.pipe, 256)
            ss = s.split(b'\0')
            if not ss[0]:
                os._exit(0)
            if ss[0] == b'break':
                self._play_loop = False
                continue
            filename, priority, loop = ss[0].decode(), int(ss[1]), int(ss[2])
            if loop:
                self._play_loop = True
                th = Thread(target=self.playLoop, args=(filename,))
                th.start()
            else:
                if not self._busy:
                    self.play(filename, priority)

    def _getParameters(self, filename):
        import ossaudiodev
        import wave
        w = wave.open(filename)
        fmt = ossaudiodev.AFMT_U8
        nch = w.getnchannels()
        rate = w.getframerate()
        frames = w.readframes(w.getnframes())
        return (frames, fmt, nch, rate)

    def playLoop(self, filename, priority=None):
        # print '_playLoop:', filename
        import ossaudiodev
        try:
            # audiodev = self.audiodev
            audiodev = ossaudiodev.open('w')
            # audiodev.nonblock()
            frames, fmt, nch, rate = self._getParameters(filename)
            audiodev.setparameters(fmt, nch, rate)
            while self._play_loop:
                audiodev.write(frames)
            audiodev.reset()
            # audiodev.close()
            # self.audiodev = ossaudiodev.open('w')
            return 1
        except Exception:
            if traceback:
                traceback.print_exc()
            return 0

    def play(self, filename, priority):
        # print '_play:', filename
        import ossaudiodev
        try:
            self._busy = True
            # audiodev = self.audiodev
            audiodev = ossaudiodev.open('w')
            # audiodev.nonblock()
            frames, fmt, nch, rate = self._getParameters(filename)
            audiodev.setparameters(fmt, nch, rate)
            audiodev.write(frames)
            # audiodev.close()
            # self.audiodev = ossaudiodev.open('w')
            self.sound_priority = priority
            self._busy = False
            return 1
        except Exception:
            if traceback:
                traceback.print_exc()
            self._busy = False
            return 0


class OSSAudioClient(AbstractAudioClient):

    CAN_PLAY_SOUND = True

    def __init__(self):
        AbstractAudioClient.__init__(self)
        import ossaudiodev
        if not os.path.exists('/dev/dsp'):
            raise RuntimeError('OSS interface not available')
        self.audiodev = ossaudiodev

    def startServer(self):
        pin, pout = os.pipe()
        self.pout = pout
        server = OSSAudioServer(pin)
        pid = os.fork()
        if pid == 0:
            server.mainLoop()

    def _playSample(self, filename, priority, loop, volume):
        # print '_playSample:', filename, loop
        os.write(self.pout, b'%s\0%s\0%s\0' %
                 (filename.encode(),
                  str(priority).encode(),
                  str(loop).encode()))
        return 1

    def _stopSamples(self):
        os.write(self.pout, b'break\0\0\0')

    def _destroy(self):
        os.write(self.pout, b'\0\0\0')


# ************************************************************************
# * PyGame
# ************************************************************************

class PyGameAudioClient(AbstractAudioClient):

    CAN_PLAY_SOUND = True

    def __init__(self):
        AbstractAudioClient.__init__(self)
        import pygame.mixer
        if os.name == 'nt':
            # for py2exe
            import pygame.base
            import pygame.rwobject
        self.mixer = pygame.mixer
        self.audiodev = self.mixer
        self.sound = None
        self.sound_channel = None
        self.sound_priority = -1

    def startServer(self):
        pass

    def connectServer(self, app):
        AbstractAudioClient.connectServer(self, app)
        # http://www.pygame.org/docs/ref/mixer.html
        # NOTE: there is currently a bug on some windows machines which
        # makes sound play back 'scratchy'. There is not enough cpu in
        # the sound thread to feed the buffer to the sound api. To get
        # around this you can increase the buffer size. However this
        # means that there is more of a delay between the time you ask to
        # play the sound and when it gets played. Try calling this before
        # the pygame.init or pygame.mixer.init calls.
        # pygame.mixer.pre_init(44100,-16,2, 1024 * 3)
        # self.mixer.pre_init(44100, -16, 2, 1024 * 3)
        buff_size = self.app.opt.sound_sample_buffer_size
        self.mixer.pre_init(44100, -16, 2, 1024*buff_size)
        self.mixer.init()

    def _playSample(self, filename, priority, loop, volume):
        # print '_playSample:', filename, priority, loop, volume
        if self.sound_channel and self.sound_channel.get_busy():
            if self.sound_priority >= priority:
                return 0
            self.sound.stop()
        vol = SAMPLE_VOLUME/128.0
        try:
            self.sound = self.mixer.Sound(filename)
            self.sound.set_volume(vol)
            self.sound_channel = self.sound.play(loop)
        except Exception:
            if traceback:
                traceback.print_exc()
        self.sound_priority = priority
        return 1

    def _stopSamples(self):
        if self.sound:
            self.sound.stop()
        self.sound = None
        self.sound_channel = None

    def _destroy(self):
        self.mixer.stop()
        self.mixer.quit()
