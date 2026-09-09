from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from src.observability.logging import setup_logger
from src.e2.asn1_shim import INT, STR_UTF8, OCT_STR, SEQ, SEQ_OF, ASN1Dict

logger = setup_logger("KpmDecoder")

@dataclass
class KpmMeasurement:
    node_id: str
    ue_id: str
    metric_name: str
    value: float
    timestamp: int

# Definição Estrutural Nativa ASN.1 (E2SM-KPM v3)
class GlobalNodeID(SEQ):
    _cont = ASN1Dict([
        ('plmnID', OCT_STR()),
        ('gnbID', OCT_STR())
    ])
    _root_mand = ['plmnID', 'gnbID']
    _root_opt = []
    _root = ['plmnID', 'gnbID']
    _ext = None

class E2SM_KPM_IndicationHeader(SEQ):
    _cont = ASN1Dict([
        ('collectionStartTime', OCT_STR()),
        ('fileFormatVersion', STR_UTF8(opt=True)),
        ('senderName', STR_UTF8(opt=True)),
        ('senderType', STR_UTF8(opt=True)),
        ('vendorName', STR_UTF8(opt=True))
    ])
    _root_mand = ['collectionStartTime']
    _root_opt = ['fileFormatVersion', 'senderName', 'senderType', 'vendorName']
    _root = ['collectionStartTime', 'fileFormatVersion', 'senderName', 'senderType', 'vendorName']
    _ext = None

class MeasurementRecordItem(SEQ):
    _cont = ASN1Dict([
        ('metricName', STR_UTF8()),
        ('metricValue', INT())
    ])
    _root_mand = ['metricName', 'metricValue']
    _root_opt = []
    _root = ['metricName', 'metricValue']
    _ext = None

class MeasDataList(SEQ_OF):
    _cont = MeasurementRecordItem()

class E2SM_KPM_IndicationMessage(SEQ):
    _cont = ASN1Dict([
        ('measData', MeasDataList()),
        ('nodeID', STR_UTF8()),
        ('ueID', STR_UTF8())
    ])
    _root_mand = ['measData', 'nodeID', 'ueID']
    _root_opt = []
    _root = ['measData', 'nodeID', 'ueID']
    _ext = None


class KpmDecoder:
    def __init__(self):
        self.metric_map = {
            "DRB.UEThpDl": "drb_thp_dl",
            "DRB.UEThpUl": "drb_thp_ul",
            "DRB.RlcSduDelayDl": "drb_delay_dl",
            "RRU.PrbUsedDl": "prb_dl",
            "RRU.PrbUsedUl": "prb_ul"
        }

    def decode_indication(self, payload: bytes) -> List[Dict]:
        """
        Wrapper exigido pelo rdl_xapp.py para extrair os reports KPM simulados/reais.
        Agrega todas as métricas pertencentes ao mesmo (node_id, ue_id) em um único dicionário,
        evitando que medições subsequentes (ex: PRBs após vazão) sobrescrevam valores anteriores com zero.
        """
        measurements = self.decode(payload, payload)
        
        aggregated: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for m in measurements:
            key = (m.node_id, m.ue_id)
            if key not in aggregated:
                aggregated[key] = {
                    "node_id": m.node_id,
                    "ue_id": m.ue_id,
                    "drb_thp_dl": 0.0,
                    "drb_thp_ul": 0.0,
                    "drb_delay_dl": 0.0,
                    "prb_used_dl": 0,
                    "prb_used_ul": 0
                }
            if m.metric_name == "DRB.UEThpDl":
                aggregated[key]["drb_thp_dl"] = float(m.value)
            elif m.metric_name == "DRB.UEThpUl":
                aggregated[key]["drb_thp_ul"] = float(m.value)
            elif m.metric_name == "DRB.RlcSduDelayDl":
                aggregated[key]["drb_delay_dl"] = float(m.value)
            elif m.metric_name == "RRU.PrbUsedDl":
                aggregated[key]["prb_used_dl"] = int(m.value)
            elif m.metric_name == "RRU.PrbUsedUl":
                aggregated[key]["prb_used_ul"] = int(m.value)

        return list(aggregated.values())

    def decode(self, indication_header: bytes, indication_message: bytes, default_node_id: str = "gnb_01") -> List[KpmMeasurement]:
        """
        Decodifica o payload E2SM-KPM via APER.
        Retorna lista de KpmMeasurement ou lista vazia [] em caso de payload inválido ou corrompido.
        """
        results = []
        try:
            msg = E2SM_KPM_IndicationMessage()
            msg.from_aper(indication_message)
            msg_val = msg()
            node = msg_val.get('nodeID', default_node_id)
            ue = msg_val.get('ueID', "ue_01")
            
            for item in msg_val.get('measData', []):
                results.append(KpmMeasurement(
                    node_id=node,
                    ue_id=ue,
                    metric_name=item['metricName'],
                    value=float(item['metricValue']),
                    timestamp=0
                ))
            return results
        except Exception as e:
            logger.warning(f"Rejeição de telemetria inválida ou corrompida no decoder E2SM-KPM: {e}")
            return []
