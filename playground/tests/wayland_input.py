"""A virtual pointer for headless KWin tests, speaking the Wayland wire protocol directly.

KWin's org_kde_kwin_fake_input sends input through its real input pipeline, so overlays,
click-through and Playground's native click bridge see it like a mouse.
"""
import os
import socket
import struct

BTN_LEFT = 0x110
# Request opcodes from plasma-wayland-protocols fake-input.xml.
AUTHENTICATE, BUTTON, POINTER_MOTION_ABSOLUTE = 0, 2, 9


def _string(text):
    data = text.encode()+b'\0'
    return struct.pack('<I', len(data))+data+b'\0'*(-len(data) % 4)


class Connection:
    def __init__(self):
        path = os.path.join(os.environ['XDG_RUNTIME_DIR'], os.environ.get('WAYLAND_DISPLAY', 'wayland-0'))
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(path)
        self.next_id, self.buffer, self.globals = 2, b'', {}

    def new_id(self):
        self.next_id += 1
        return self.next_id-1

    def send(self, obj, opcode, payload=b''):
        self.sock.sendall(struct.pack('<II', obj, (8+len(payload)) << 16 | opcode)+payload)

    def roundtrip(self):
        callback = self.new_id()
        self.send(1, 0, struct.pack('<I', callback))  # wl_display.sync
        while True:
            while len(self.buffer) < 8:
                chunk = self.sock.recv(65536)
                if not chunk:
                    raise ConnectionError('Compositor closed the connection')
                self.buffer += chunk
            obj, word = struct.unpack_from('<II', self.buffer)
            size, opcode = word >> 16, word & 0xffff
            while len(self.buffer) < size:
                self.buffer += self.sock.recv(65536)
            body, self.buffer = self.buffer[8:size], self.buffer[size:]
            if obj == 1 and opcode == 0:  # wl_display.error
                _, code, length = struct.unpack_from('<III', body)
                raise RuntimeError(f'Wayland error {code}: {body[12:12+length-1].decode()}')
            if obj == self.registry and opcode == 0:  # wl_registry.global
                name, length = struct.unpack_from('<II', body)
                interface = body[8:8+length-1].decode()
                version, = struct.unpack_from('<I', body, 8+length+(-length % 4))
                self.globals[interface] = (name, version)
            if obj == callback:
                return

    def connect_registry(self):
        self.registry = self.new_id()
        self.send(1, 1, struct.pack('<I', self.registry))  # wl_display.get_registry
        self.roundtrip()


class FakePointer:
    """A virtual pointer. Create it early: a headless seat gains pointer support only once it exists."""

    def __init__(self):
        self.wl = Connection()
        self.wl.connect_registry()
        if 'org_kde_kwin_fake_input' not in self.wl.globals:
            raise RuntimeError('KWin does not offer fake input to this client')
        name, version = self.wl.globals['org_kde_kwin_fake_input']
        self.fake = self.wl.new_id()
        self.wl.send(self.wl.registry, 0, struct.pack('<I', name)+_string('org_kde_kwin_fake_input')
                     + struct.pack('<II', min(version, 4), self.fake))
        self.wl.send(self.fake, AUTHENTICATE, _string('Playground smoke test')+_string('Click through the overlay'))
        self.wl.roundtrip()

    def click(self, x, y):
        self.wl.send(self.fake, POINTER_MOTION_ABSOLUTE, struct.pack('<ii', round(x*256), round(y*256)))
        self.wl.roundtrip()
        for state in (1, 0):
            self.wl.send(self.fake, BUTTON, struct.pack('<II', BTN_LEFT, state))
            self.wl.roundtrip()

    def close(self):
        self.wl.sock.close()
