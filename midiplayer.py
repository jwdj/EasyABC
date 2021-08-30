from __future__ import unicode_literals


class EventHook(object):
    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__handlers.remove(handler)
        return self

    def fire(self, *args, **keywargs):
        for handler in self.__handlers:
            handler(*args, **keywargs)

    def clearObjectHandlers(self, obj):
        self.__handlers = [h for h in self.__handlers if getattr(h, '__self__', False) != obj]


class MidiPlayer(object):
    def __init__(self):
        super(MidiPlayer, self).__init__()
        self.OnAfterStop = EventHook()
        self.OnAfterLoad = EventHook()
        self._loop_midi_playback = False

    @property
    def is_playing(self):
        return False

    @property
    def is_paused(self):
        return False

    @property
    def loop_midi_playback(self):
        return self._loop_midi_playback

    def set_loop_midi_playback(self, value):
        self._loop_midi_playback = value

    @property
    def supports_tempo_change_while_playing(self):
        return False

    @property
    def unit_is_midi_tick(self):
        return False

    def Play(self):
        pass

    def Stop(self):
        pass

    def Pause(self):
        pass

    def Load(self, path):
        return True

    def Length(self):
        return 0

    def Seek(self, pos_in_ms):
        pass

    def Tell(self):
        return 0

    def dispose(self):
        pass


class DummyMidiPlayer(MidiPlayer):
    def __init__(self):
        super(DummyMidiPlayer, self).__init__()

