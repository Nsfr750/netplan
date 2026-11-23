"""
sample_data.py
Genera un dataset SINTETICO di KPI di rete aggregati per cella, utile
per testare lo strumento senza avere accesso a dati reali di un operatore.

IMPORTANTE: tutti i valori qui sono a livello di CELLA/SETTORE, aggregati
su una finestra temporale (es. ora/giorno). Non c'è alcun riferimento a
utenti, numeri di telefono o IMSI: questo è ciò che rende i dati
"anonimizzati" e idonei alla pianificazione di rete.
"""

import csv
import random
import math

RNG = random.Random(42)

SITES = [
    # site_id, lat, lon  (coordinate di esempio, area urbana fittizia)
    ("SITE_001", 45.4642, 9.1900),
    ("SITE_002", 45.4700, 9.1800),
    ("SITE_003", 45.4600, 9.2050),
    ("SITE_004", 45.4550, 9.1700),
    ("SITE_005", 45.4800, 9.2000),
]

SECTORS_PER_SITE = 3  # tipico sito trisettoriale
HOURS = 24


def generate(output_path: str, days: int = 1):
    fieldnames = [
        "timestamp_hour",
        "site_id",
        "cell_id",
        "technology",
        "band",
        "latitude",
        "longitude",
        "azimuth_deg",
        "traffic_erlang",
        "data_volume_gb",
        "prb_utilization_pct",
        "connected_users_avg",  # numero MEDIO di utenze contemporanee, non identificabili
        "call_drop_rate_pct",
        "handover_success_rate_pct",
        "avg_rsrp_dbm",
        "weak_signal_sample_pct",  # % di campioni di rete con RSRP < -110dBm in quella cella
    ]

    # Tecnologia e banda fisse per cella (realistico: una cella non cambia RAT ora per ora)
    cell_tech = {}
    for site_id, _, _ in SITES:
        for s in range(SECTORS_PER_SITE):
            tech = RNG.choice(["LTE", "NR"])
            band = (
                RNG.choice(["B3", "B7", "B20"])
                if tech == "LTE"
                else RNG.choice(["n78", "n1"])
            )
            cell_tech[f"{site_id}_C{s+1}"] = (tech, band)

    rows = []
    for day in range(days):
        for hour in range(HOURS):
            for site_id, lat, lon in SITES:
                base_load = 0.3 + 0.5 * math.sin((hour - 8) / 24 * 2 * math.pi) ** 2
                for s in range(SECTORS_PER_SITE):
                    cell_id = f"{site_id}_C{s+1}"
                    azimuth = s * 120
                    congestion_bias = 1.0
                    if site_id == "SITE_002":  # simuliamo un sito "critico"
                        congestion_bias = 1.6
                    if site_id == "SITE_004":  # simuliamo un sito con copertura debole
                        rsrp = -118 + RNG.uniform(-4, 4)
                        weak_pct = RNG.uniform(25, 45)
                    else:
                        rsrp = -95 + RNG.uniform(-8, 8)
                        weak_pct = RNG.uniform(2, 10)

                    prb = min(
                        100,
                        max(5, base_load * 70 * congestion_bias + RNG.uniform(-5, 5)),
                    )
                    users = max(0, int(prb * 1.8 + RNG.uniform(-5, 5)))
                    drop_rate = max(0.1, (prb / 100) ** 2 * 6 + RNG.uniform(-0.3, 0.3))
                    ho_success = min(
                        99.9, max(80, 99.5 - (prb / 100) * 8 + RNG.uniform(-1, 1))
                    )

                    rows.append(
                        {
                            "timestamp_hour": f"2026-01-{day+1:02d}T{hour:02d}:00",
                            "site_id": site_id,
                            "cell_id": cell_id,
                            "technology": cell_tech[cell_id][0],
                            "band": cell_tech[cell_id][1],
                            "latitude": round(lat + RNG.uniform(-0.0005, 0.0005), 6),
                            "longitude": round(lon + RNG.uniform(-0.0005, 0.0005), 6),
                            "azimuth_deg": azimuth,
                            "traffic_erlang": round(prb / 10, 2),
                            "data_volume_gb": round(prb * 1.3 + RNG.uniform(-3, 3), 2),
                            "prb_utilization_pct": round(prb, 1),
                            "connected_users_avg": users,
                            "call_drop_rate_pct": round(drop_rate, 2),
                            "handover_success_rate_pct": round(ho_success, 2),
                            "avg_rsrp_dbm": round(rsrp, 1),
                            "weak_signal_sample_pct": round(weak_pct, 1),
                        }
                    )

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Dataset di esempio generato: {output_path} ({len(rows)} righe)")

if __name__ == "__main__":
    generate("data/sample_kpis.csv", days=1)
