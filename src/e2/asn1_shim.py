"""
Shim de compatibilidade ASN.1 / APER para o ecossistema E2 (E2AP, E2SM-KPM, E2SM-RC).
Utiliza pycrate nativo quando disponível; caso contrário, provê emulador estrutural
puro em Python para ambientes de desenvolvimento, teste e CI sem dependências de compilação C.
"""

try:
    from pycrate_asn1rt.asnobj_basic import INT, ENUM
    from pycrate_asn1rt.asnobj_construct import SEQ as _PycrateSEQ, SEQ_OF as _PycrateSEQ_OF, ASN1Dict
    from pycrate_asn1rt.asnobj_str import STR_UTF8, OCT_STR
    PYCRATE_AVAILABLE = True
    SEQ = _PycrateSEQ
    SEQ_OF = _PycrateSEQ_OF
except ImportError:
    PYCRATE_AVAILABLE = False
    import json
    import struct

    class ASN1Dict(dict):
        def __init__(self, items=None):
            super().__init__()
            if items:
                for k, v in items:
                    self[k] = v

    class INT:
        def __init__(self, opt=False):
            self.opt = opt

    class ENUM:
        def __init__(self, val=None, opt=False):
            self.val = val or {}
            self.opt = opt

    class STR_UTF8:
        def __init__(self, opt=False):
            self.opt = opt

    class OCT_STR:
        def __init__(self, opt=False):
            self.opt = opt

    class SEQ:
        _cont = None
        _root = []
        _root_mand = []
        _root_opt = []
        _ext = None

        def __init__(self):
            self._val = {}

        def set_val(self, val):
            self._val = val

        def get_val(self):
            return self._val

        def __call__(self):
            return self._val

        def to_aper(self) -> bytes:
            """Serialização binária canônica para emulação APER pura em Python."""
            payload = json.dumps(self._val, default=lambda o: getattr(o, "_val", str(o))).encode('utf-8')
            length = struct.pack(">I", len(payload))
            return b"\x30\x82" + length + payload

        def from_aper(self, char: bytes):
            """Desserialização binária canônica de buffer APER."""
            if not char:
                raise ValueError("Empty APER buffer")
            if char.startswith(b"\x30\x82") and len(char) >= 6:
                payload = char[6:]
                self._val = json.loads(payload.decode('utf-8'))
            else:
                try:
                    self._val = json.loads(char.decode('utf-8'))
                except Exception as e:
                    raise ValueError(f"Invalid APER payload: {e}")

    class SEQ_OF:
        _cont = None
        def __init__(self):
            self._list = []
