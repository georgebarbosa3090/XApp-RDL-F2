from typing import Tuple, Dict, Any, Optional
from src.observability.logging import setup_logger
from src.e2.asn1_shim import INT, STR_UTF8, OCT_STR, SEQ, SEQ_OF, ASN1Dict

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

    def encode_control_pdu(self, node_id: str, parameter: str, value: float, style_type: int = 1, action_id: int = 1) -> Tuple[bytes, bytes]:
        """
        Gera tanto o Header APER quanto o Message APER completos para controle de rádio.
        Retorna a tupla (header_aper, msg_aper).
        """
        if parameter not in self.profiles:
            raise ValueError(f"Parâmetro E2SM-RC não suportado ou desconhecido: '{parameter}'")
            
        profile = self.profiles[parameter]
        param_id = profile["id"]
        scale = profile["scale"]
        
        # Conversão precisa com escala de ponto fixo
        encoded_val = int(round(float(value) * scale))
        
        # Validação estrita de limites numéricos
        if encoded_val < profile["min"] or encoded_val > profile["max"]:
            raise ValueError(
                f"Valor fora dos limites para {parameter}: {value} (codificado: {encoded_val}, permitido: [{profile['min']}, {profile['max']}])"
            )

        # Constrói o Header
        header = E2SM_RC_ControlHeader()
        header.set_val({'ricControlStyleType': style_type, 'ricControlActionID': action_id})
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
        
        logger.debug(f"RC Control Encoded APER size: header={len(header_aper)}B, msg={len(msg_aper)}B for param {parameter} (val={value} -> {encoded_val})")
        return header_aper, msg_aper

    def encode_control_request(self, node_id: str, parameter: str, value: float) -> bytes:
        """
        Gera o payload binário APER ASN.1 padronizado com escala de ponto fixo.
        Rejeita parâmetros não suportados ou valores fora dos limites físicos configurados.
        Retorna o Message APER (compatibilidade direta).
        """
        _, msg_aper = self.encode_control_pdu(node_id, parameter, value)
        return msg_aper

    def decode_control_header(self, header_aper: bytes) -> Dict[str, Any]:
        """Decodifica o cabeçalho de controle E2SM-RC APER."""
        try:
            header = E2SM_RC_ControlHeader()
            header.from_aper(header_aper)
            return header.get_val()
        except Exception as e:
            logger.error(f"Erro ao decodificar Header E2SM-RC APER: {e}")
            raise

    def decode_control_message(self, msg_aper: bytes) -> Dict[str, Any]:
        """Decodifica a mensagem de controle E2SM-RC APER."""
        try:
            msg = E2SM_RC_ControlMessage()
            msg.from_aper(msg_aper)
            return msg.get_val()
        except Exception as e:
            logger.error(f"Erro ao decodificar Mensagem E2SM-RC APER: {e}")
            raise

    def decode_control_request(self, msg_aper: bytes, parameter: str) -> float:
        """
        Decodifica o payload APER ASN.1 e restaura o valor em ponto flutuante original.
        """
        try:
            val_dict = self.decode_control_message(msg_aper)
            raw_int = val_dict['ricControlActionParameters'][0]['ranParameterValue']
            
            profile = self.profiles.get(parameter, {"scale": 1})
            scale = profile["scale"]
            return float(raw_int) / float(scale)
        except Exception as e:
            logger.error(f"Erro ao decodificar E2SM-RC APER: {e}")
            raise
