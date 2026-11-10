"""
Curva de calibração teto de PRB -> vazão relativa, medida na bancada NORI da Fase 1.

Fonte: ``XApp-RDL-F1/experiments/calibration/slice_cap_curve_v5.json`` (copiada para
``cardl/calibration/``), gerada a partir das séries do FlowMonitor de execuções com E2 real
(cada ponto traz o run_id e o sha256 da série). O sha256 do arquivo é verificado na carga
e registrado no manifesto de cada treino.

Regra de interpolação (a mesma da regra v6 da Fase 1, achados 41 e 42): só entre níveis que
restringem (``binding``); acima do último, a reta do último segmento continua até a
saturação (razão 1); abaixo do primeiro, reta até a origem.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

DEFAULT_CURVE = Path(__file__).resolve().parents[1] / "calibration" / "slice_cap_curve_v5.json"
EXPECTED_SHA256 = "d7c2f54ead0f51583a9b20c00eaa602f105b461a33d0ac44e2604015b0d8282d"


@dataclass(frozen=True)
class CapCurve:
    points: Tuple[Tuple[float, float], ...]  # (teto % de PRB, vazão depois / vazão antes), só binding
    base_throughput_mbps: float
    source: str
    sha256: str

    def ratio(self, cap_pct: float) -> float:
        """Vazão relativa à base para um teto de PRB (0–100 %)."""
        cap = max(0.0, min(100.0, float(cap_pct)))
        pts = self.points
        if cap <= pts[0][0]:
            return pts[0][1] * cap / pts[0][0]
        for (c0, r0), (c1, r1) in zip(pts, pts[1:]):
            if cap <= c1:
                return r0 + (r1 - r0) * (cap - c0) / (c1 - c0)
        (c0, r0), (c1, r1) = pts[-2], pts[-1]
        slope = (r1 - r0) / (c1 - c0)
        return min(1.0, r1 + slope * (cap - c1))

    def saturation_cap_pct(self) -> float:
        """Menor teto a partir do qual a vazão deixa de ser limitada."""
        (c0, r0), (c1, r1) = self.points[-2], self.points[-1]
        slope = (r1 - r0) / (c1 - c0)
        return min(100.0, c1 + (1.0 - r1) / slope)


def load_curve(path: Path = DEFAULT_CURVE, slice_key: str = "1", verify: bool = True) -> CapCurve:
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if verify and Path(path) == DEFAULT_CURVE and digest != EXPECTED_SHA256:
        raise ValueError(f"curva de calibração alterada: sha256 {digest} != {EXPECTED_SHA256}")
    data = json.loads(raw.decode("utf-8"))
    entries = data["curve"][slice_key]
    binding: List[Tuple[float, float]] = sorted(
        (float(e["cap_max_prb_pct"]), float(e["throughput_after_mbps"]) / float(e["throughput_before_mbps"]))
        for e in entries if e.get("binding")
    )
    if len(binding) < 2:
        raise ValueError("a curva precisa de pelo menos dois pontos que restringem")
    base = float(entries[0]["throughput_before_mbps"])
    return CapCurve(points=tuple(binding), base_throughput_mbps=base, source=str(path), sha256=digest)
