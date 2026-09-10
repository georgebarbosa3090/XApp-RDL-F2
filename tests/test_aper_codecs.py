import pytest
from src.e2.e2ap_decoder import decode_e2ap_ric_indication
from src.e2.kpm_decoder import KpmDecoder
from src.e2.rc_encoder import RCEncoder

def test_e2ap_decoder_strict_rejection():
    """Valida a rejeicao estrita de envelope E2AP quando o payload APER e invalido."""
    payload = b"MOCK_PAYLOAD"
    with pytest.raises(Exception):
        decode_e2ap_ric_indication(payload)

def test_kpm_decoder_rejection_on_invalid_payload():
    """Valida a rejeicao estrita de telemetria sem dados artificiais quando o payload APER esta corrompido."""
    decoder = KpmDecoder()
    payload = b"BOGUS_CORRUPTED_DATA"
    measurements = decoder.decode_indication(payload)
    assert isinstance(measurements, list)
    assert len(measurements) == 0

def test_kpm_decoder_valid_aper_multimetric_aggregation():
    """Valida decodificacao e agregacao de telemetria valida via APER."""
    from src.e2.kpm_decoder import E2SM_KPM_IndicationMessage
    decoder = KpmDecoder()
    
    msg = E2SM_KPM_IndicationMessage()
    msg.set_val({
        'nodeID': 'gnb_01',
        'ueID': 'ue_01',
        'measData': [
            {'metricName': 'DRB.UEThpDl', 'metricValue': 85},
            {'metricName': 'RRU.PrbUsedDl', 'metricValue': 60}
        ]
    })
    valid_aper = msg.to_aper()
    
    aggregated = decoder.decode_indication(valid_aper)
    assert len(aggregated) == 1
    assert aggregated[0]["node_id"] == "gnb_01"
    assert aggregated[0]["ue_id"] == "ue_01"
    assert aggregated[0]["drb_thp_dl"] == pytest.approx(85.0)
    assert aggregated[0]["prb_used_dl"] == 60

def test_rc_encoder_generates_bytes():
    encoder = RCEncoder()
    node_id = "gnb_01"
    parameter = "PRB_QUOTA"
    value = 50.0
    
    aper_bytes = encoder.encode_control_request(node_id, parameter, value)
    assert isinstance(aper_bytes, bytes)
    assert len(aper_bytes) > 0
