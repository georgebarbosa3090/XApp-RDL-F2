"""Variação da célula (vazão, atraso) e perdas de conexão 1 s e 2 s depois de cada conflito indireto resolvido
mantendo as ações (EEVS), contra janelas com uma ação isolada do mesmo parâmetro no mesmo gNB, nas execuções B3."""
import glob, json, re, statistics as st, sys, collections
pats = sys.argv[1:]
PARAMS = ("PRB_QUOTA", "TX_POWER", "HANDOVER", "CELL_STATE")
def par(i):
    for p in PARAMS:
        if f"-{p}-" in i: return p
def gnb(i):
    m = re.search(r"-g(\d+)-", i); return int(m.group(1)) if m else None
res = collections.defaultdict(list)
for p in pats:
    for d in sorted(glob.glob(p)):
        W = {}
        for l in open(f"{d}/raw/closed_loop_log.jsonl", encoding="utf-8"):
            j = json.loads(l)
            if j.get("type") == "window": W[round(j["t"], 1)] = j
        ts = sorted(W)
        def cell(t, g):
            w = W.get(round(t, 1))
            if not w: return None
            return next((c for c in w["kpm"]["cells"] if c["gnb"] == g), None)
        def lost(t0, t1, g):
            n = 0
            for t in ts:
                if t0 < t <= t1:
                    n += sum(1 for u in W[t]["kpm"]["ues"] if not u.get("connected", True))
            return n
        conflict_ids = set()
        for t in ts:
            for r in (W[t].get("decision") or {}).get("resolutions") or []:
                if r.get("conflict_type") != "INDIRECT": continue
                inv = r.get("involved") or []
                conflict_ids |= set(inv)
                key = "x".join(sorted({par(i) for i in inv}))
                g = gnb(inv[0])
                c0 = cell(t, g); c1 = cell(t + 1.0, g); c2 = cell(t + 2.0, g)
                if c0 and c1 and c2 and c0["thp_mbps"]:
                    res[("conflito", key)].append((c1["thp_mbps"] / c0["thp_mbps"] - 1, c2["thp_mbps"] / c0["thp_mbps"] - 1, lost(t, t + 2.0, g)))
        for t in ts:
            acts = W[t].get("actions") or []
            if len(acts) != 1 or acts[0]["id"] in conflict_ids: continue
            a = acts[0]; g = a["gnb"]
            c0 = cell(t, g); c1 = cell(t + 1.0, g); c2 = cell(t + 2.0, g)
            if c0 and c1 and c2 and c0["thp_mbps"]:
                res[("isolada", a["parameter"])].append((c1["thp_mbps"] / c0["thp_mbps"] - 1, c2["thp_mbps"] / c0["thp_mbps"] - 1, lost(t, t + 2.0, g)))
for k in sorted(res):
    v = res[k]; m = lambda i: round(100 * st.median(x[i] for x in v), 1)
    print(k, "n =", len(v), "| mediana Δvazão da célula +1 s:", m(0), "% +2 s:", m(1), "% | janelas-UE sem conexão em 2 s (soma):", sum(x[2] for x in v),
          "| casos com queda > 20 % em +2 s:", sum(1 for x in v if x[1] < -0.2))
