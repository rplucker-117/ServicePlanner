import rtmidi2
from logzero import logger

class Midi:
    def __init__(self):
        self.midi_out_port = None
        self.midi_out = rtmidi2.MidiOut()

    def get_midi_out(self):
        return rtmidi2.get_out_ports()

    def set_out_port(self, port):
        logger.debug('Midi: Setting output port %s', port)
        self.midi_out_port = port
        self.midi_out.open_port(self.midi_out_port)
        logger.debug(f'Set midi out port to {self.get_midi_out()[self.midi_out_port]}, port {self.midi_out_port}.')

    def send_noteon(self, channel, note, velocity):
        logger.debug(f'Sending midi note on: Device: {self.get_midi_out()[self.midi_out_port]}, port {self.midi_out_port}. Channel {channel}, Note {note}, Velocity {velocity}')
        self.midi_out.send_noteon(channel, note, velocity)

# midi = Midi()
# print(midi.get_midi_out())
# midi.set_out_port(2)
# midi.send_noteon(0, 19, 6)