import pytest
from src.e2.rc_encoder import RCEncoder

def test_rc_encoder_valid_parameter_profiles():
    encoder = RCEncoder()
    valid_test_cases = [
        ("TX_POWER", 23.0),
        ("PRB_QUOTA", 60.0),
        ("BEAM_DOWNTILT", 6.5),
        ("ISAC_SENSING_RATIO", 0.25),
        ("A3_OFFSET", 3.0),
        ("SCHEDULER_WEIGHT", 2.0),
    ]
    
    for param, val in valid_test_cases:
        payload = encoder.encode_control_request(node_id="gnb_01", parameter=param, value=val)
        assert isinstance(payload, bytes)
        assert len(payload) > 0

def test_rc_encoder_rejects_unsupported_parameters():
    encoder = RCEncoder()
    with pytest.raises(ValueError, match="Parâmetro E2SM-RC não suportado ou desconhecido"):
        encoder.encode_control_request(node_id="gnb_01", parameter="NON_EXISTENT_PARAM", value=10.0)

def test_rc_encoder_rejects_out_of_bounds_values():
    encoder = RCEncoder()
    
    # Power > 43 dBm
    with pytest.raises(ValueError, match="Valor fora dos limites para TX_POWER"):
        encoder.encode_control_request(node_id="gnb_01", parameter="TX_POWER", value=50.0)
        
    # Negative PRB
    with pytest.raises(ValueError, match="Valor fora dos limites para PRB_QUOTA"):
        encoder.encode_control_request(node_id="gnb_01", parameter="PRB_QUOTA", value=-5.0)
        
    # ISAC ratio > 0.5
    with pytest.raises(ValueError, match="Valor fora dos limites para ISAC_SENSING_RATIO"):
        encoder.encode_control_request(node_id="gnb_01", parameter="ISAC_SENSING_RATIO", value=0.8)

def test_rc_encoder_decoder_reversible():
    encoder = RCEncoder()
    test_cases = [
        ("TX_POWER", 23.5),
        ("PRB_QUOTA", 75.0),
        ("BEAM_DOWNTILT", 7.2),
        ("ISAC_SENSING_RATIO", 0.3),
        ("A3_OFFSET", -2.5),
        ("SCHEDULER_WEIGHT", 1.5)
    ]
    for param, val in test_cases:
        payload = encoder.encode_control_request(node_id="gnb_01", parameter=param, value=val)
        decoded_val = encoder.decode_control_request(payload, param)
        assert pytest.approx(decoded_val, abs=0.01) == val

def test_rc_encoder_encode_pdu_and_header_decode():
    """Valida a codificação completa de PDU (Header + Message) e decodificação estruturada."""
    encoder = RCEncoder()
    header_aper, msg_aper = encoder.encode_control_pdu("gnb_01", "TX_POWER", 23.5, style_type=1, action_id=1)
    
    assert isinstance(header_aper, bytes)
    assert isinstance(msg_aper, bytes)
    assert len(header_aper) > 0
    assert len(msg_aper) > 0
    
    # Decodifica Header
    hdr_dict = encoder.decode_control_header(header_aper)
    assert hdr_dict["ricControlStyleType"] == 1
    assert hdr_dict["ricControlActionID"] == 1
    
    # Decodifica Message
    msg_dict = encoder.decode_control_message(msg_aper)
    assert "ricControlActionParameters" in msg_dict
    assert msg_dict["ricControlActionParameters"][0]["ranParameterName"] == "TX_POWER"
    assert msg_dict["ricControlActionParameters"][0]["ranParameterValue"] == 235

