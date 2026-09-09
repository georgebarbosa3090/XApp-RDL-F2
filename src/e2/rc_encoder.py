from src.observability.logging import setup_logger
from pycrate_asn1rt.asnobj_basic import INT
from pycrate_asn1rt.asnobj_construct import SEQ, SEQ_OF, ASN1Dict
from pycrate_asn1rt.asnobj_str import STR_UTF8, OCT_STR

logger = setup_logger("RCEncoder")

# Definição Estrutural Nativa ASN.1 (E2SM-RC v1)
class E2SM_RC_ControlHeader(SEQ):
    _cont = ASN1Dict([
        ('ricControlStyleType', INT()),
        ('ricControlActionID', INT())
    ])
    _root_mand = ['ricControlStyleType', 'ricControlActionID']
    _root_opt = []
    _root = ['ricControlStyleType', 'ricControlActionID']
    _ext = None

class E2SM_RC_ControlMessageItem(SEQ):
    _cont = ASN1Dict([
        ('ranParameterID', INT()),
        ('ranParameterName', STR_UTF8()),
        ('ranParameterValue', INT())
    ])
    _root_mand = ['ranParameterID', 'ranParameterName', 'ranParameterValue']
    _root_opt = []
    _root = ['ranParameterID', 'ranParameterName', 'ranParameterValue']
    _ext = None

class ParamList(SEQ_OF):
    _cont = E2SM_RC_ControlMessageItem()

class E2SM_RC_ControlMessage(SEQ):
    _cont = ASN1Dict([
        ('ricControlActionParameters', ParamList())
    ])
    _root_mand = ['ricControlActionParameters']
    _root_opt = []
    _root = ['ricControlActionParameters']
    _ext = None

class RCEncoder:
    """
    Construtor de payloads APER para a subcamada E2SM-RC (RAN Control).
    Requisito RF-17.
    """
# Dicionário Sistemático de Perfis de Parâmetros E2SM-RC (O-RAN.WG3.TS.E2SM-RC v01.00)
# Define ID padronizado, fator de escala em ponto fixo, unidade e faixa admissível
PARAM_PROFILES = {
    "PRB_QUOTA":          {"id": 1,  "scale": 1,    "unit": "PRB",         "min": 0,    "max": 100},
    "TX_POWER":           {"id": 2,  "scale": 10,   "unit": "dBm_x10",     "min": -100, "max": 430},
    "SCHEDULER_WEIGHT":   {"id": 3,  "scale": 1000, "unit": "milli_ratio", "min": 10,   "max": 10000},
    "A3_OFFSET":          {"id": 4,  "scale": 100,  "unit": "centi_dB",    "min": -1000,"max": 1000},
    "BEAM_DOWNTILT":      {"id": 10, "scale": 10,   "unit": "deg_x10",     "min": 0,    "max": 150},
    "ISAC_SENSING_RATIO": {"id": 11, "scale": 1000, "unit": "milli_ratio", "min": 0,    "max": 500},
    "CARRIER_AGG_RATIO":  {"id": 12, "scale": 1000, "unit": "milli_ratio", "min": 0,    "max": 1000}
}

class RCEncoder:
    """
    Construtor de payloads APER para a subcamada E2SM-RC (RAN Control).
    Garante fidelidade numérica com ponto fixo padronizado e decodificação reversível.
    """
    def __init__(self):
        self.profiles = PARAM_PROFILES

    def encode_control_request(self, node_id: str, parameter: str, value: float) -> bytes:
        """
        Gera o payload binário APER ASN.1 padronizado com escala de ponto fixo.
        """
        try:
            profile = self.profiles.get(parameter, {"id": 99, "scale": 1})
            param_id = profile["id"]
            scale = profile["scale"]
            
            # Conversão precisa com escala de ponto fixo
            encoded_val = int(round(float(value) * scale))

            # Constrói o Header
            header = E2SM_RC_ControlHeader()
            header.set_val({'ricControlStyleType': 1, 'ricControlActionID': 1})
            header_aper = header.to_aper()

            # Constrói a Message
            msg = E2SM_RC_ControlMessage()
            msg.set_val({'ricControlActionParameters': [
                {
                    'ranParameterID': param_id,
                    'ranParameterName': parameter,
                    'ranParameterValue': encoded_val
                }
            ]})
            msg_aper = msg.to_aper()
            
            logger.debug(f"RC Control Encoded APER size: {len(msg_aper)} bytes for param {parameter} (val={value} -> {encoded_val})")
            return msg_aper

        except Exception as e:
            logger.error(f"Erro Crítico ao encodar E2SM-RC via APER: {e}")
            raise

    def decode_control_request(self, msg_aper: bytes, parameter: str) -> float:
        """
        Decodifica o payload APER ASN.1 e restaura o valor em ponto flutuante original.
        """
        try:
            msg = E2SM_RC_ControlMessage()
            msg.from_aper(msg_aper)
            val_dict = msg.get_val()
            raw_int = val_dict['ricControlActionParameters'][0]['ranParameterValue']
            
            profile = self.profiles.get(parameter, {"scale": 1})
            scale = profile["scale"]
            return float(raw_int) / float(scale)
        except Exception as e:
            logger.error(f"Erro ao decodificar E2SM-RC APER: {e}")
            raise
