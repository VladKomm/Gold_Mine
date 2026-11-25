import csv
import random
from datetime import date, timedelta
from faker import Faker

fake = Faker()
random.seed(42)  # для воспроизводимости

# ---------- СПРАВОЧНИКИ (эталонные, "чистые") ----------
# Их пользователь должен восстановить сам из загрязнённых данных.

COUNTRIES = ["Peru", "Brazil", "Chile", "Ecuador", "Colombia", "Argentina"]

COMPANIES = {
    "Newmont": ["Yanacocha", "Cerro Negro"],
    "Glencore": ["Antapaccay"],
    "Gold Fields": ["Cerro Corona", "Salares Norte"],
    "Barrick": ["Lagunas Norte", "Veladero", "Cerro Casale"],
    "Buenaventura": ["Orcopampa", "Tambomayo"],
    "Poderosa": ["Poderosa"],
    "Boroo": ["Boroo Misquichilca"],
    "G Mining Ventures": ["Tocantinzinho"],
    "Kinross": ["Paracatu", "Cerro Casale"],
    "AngloGold Ashanti": ["Cuiabá Complex", "Serra Grande", "La Colosa", "Cerro Vanguardia"],
    "Lundin Mining": ["Candelaria", "Chapada"],
    "Hochschild": ["Mara Rosa"],
    "Serabi Gold": ["Palito Complex"],
    "Yamana": ["El Peñón"],
    "Pan American Silver": ["El Peñón"],
    "Rio2": ["Fénix"],
    "Lundin Gold": ["Fruta del Norte"],
    "CRCC": ["Mirador"],
    "Aris Mining": ["Segovia"],
}

MINES = [(m, c) for c, ms in COMPANIES.items() for m in ms]
# → [('Yanacocha', 'Newmont'), ('Cerro Negro', 'Newmont'), ('Antapaccay', 'Glencore'), ...]

MINE_COUNTRY = {
    "Yanacocha": "Peru",
    "Cerro Negro": "Argentina",
    "Antapaccay": "Peru",
    "Cerro Corona": "Peru",
    "Salares Norte": "Chile",
    "Lagunas Norte": "Peru",
    "Veladero": "Argentina",
    "Cerro Casale": "Chile",
    "Orcopampa": "Peru",
    "Tambomayo": "Peru",
    "Poderosa": "Peru",
    "Boroo Misquichilca": "Peru",
    "Tocantinzinho": "Brazil",
    "Paracatu": "Brazil",
    "Cuiabá Complex": "Brazil",
    "Serra Grande": "Brazil",
    "La Colosa": "Colombia",
    "Cerro Vanguardia": "Argentina",
    "Candelaria": "Chile",
    "Chapada": "Brazil",
    "Mara Rosa": "Brazil",
    "Palito Complex": "Brazil",
    "El Peñón": "Chile",
    "Fénix": "Chile",
    "Fruta del Norte": "Ecuador",
    "Mirador": "Ecuador",
    "Segovia": "Colombia",
}

# добавляем страну к каждой паре (рудник, компания)
MINES = [(m, co, MINE_COUNTRY[m]) for (m, co) in MINES]

DEST_PORTS = {
    "Peru": ["Salaverry", "Matarani", "Callao"],
    "Chile": ["Puerto Ventanas", "Antofagasta", "San Antonio"],
    "Brazil": ["Vila do Conde", "Santos", "Itaqui"],
    "Ecuador": ["Guayaquil"],
    "Colombia": ["Cartagena", "Buenaventura"],
    "Argentina": ["Buenos Aires", "San Lorenzo"],
}
CARRIERS = ["Transportes Andinos", "TransAmazon", "ChileCarga", "AndesLog",
            "PeruRail", "BrazilLog", "Pacific Cargo", "Sur Logistics", "Cordillera Freight"]
BUYER_COUNTRIES = ["USA", "China", "Switzerland", "Germany", "UK", "Japan",
                   "Canada", "India", "UAE", "South Korea"]
PAYMENT_TERMS = ["15 days", "30 days", "45 days", "60 days", "90 days", "LC at sight"]
INCOTERMS = ["CIF", "FOB", "DAP", "CFR", "EXW"]

# ---------- ЗАГРЯЗНИТЕЛИ ----------

def maybe_duplicate(rows, rate=0.10):
    """Дубликаты с немного изменённым ID или без него."""
    out = list(rows)
    n_dup = int(len(rows) * rate)
    for _ in range(n_dup):
        r = random.choice(rows).copy()
        if random.random() < 0.5:
            r["record_id"] = r["record_id"] + "_DUP" if "record_id" in r else r.get("shipment_id", "") + "_DUP"
        out.append(r)
    random.shuffle(out)
    return out

def corrupt_decimal_comma(value):
    if isinstance(value, (int, float)) and random.random() < 0.08:
        return str(value).replace(".", ",")
    return value

def corrupt_null(rows, fields, rate=0.05):
    for r in rows:
        for f in fields:
            if random.random() < rate:
                r[f] = None
    return rows

def corrupt_negative(rows, fields, rate=0.02):
    for r in rows:
        for f in fields:
            if isinstance(r.get(f), (int, float)) and random.random() < rate:
                r[f] = -abs(r[f])
    return rows

def corrupt_country_typo(rows, field="country", rate=0.03):
    typos = {"Peru": ["Equador", "Perù", "PERU", "Perú"],
             "Brazil": ["Brasil", "BRAZIL", "Brasil "],
             "Chile": ["Chilli", "CHILE", "Chle"],
             "Ecuador": ["Equador", "ECUADOR", "Equator"],
             "Colombia": ["Columbia", "COLOMBIA", "Colombie"],
             "Argentina": ["Argentine", "ARGENTINA", "Agentina"]}
    for r in rows:
        v = r.get(field)
        if v in typos and random.random() < rate:
            r[field] = random.choice(typos[v])
    return rows

def corrupt_units(rows, field, rate=0.02, suffix=" т"):
    for r in rows:
        if random.random() < rate and r.get(field) is not None:
            r[field] = f"{r[field]}{suffix}"
    return rows

def corrupt_dates_reversed(rows, dep="departure_date", arr="arrival_date", rate=0.03):
    for r in rows:
        if random.random() < rate and r.get(dep) and r.get(arr):
            r[dep], r[arr] = r[arr], r[dep]
    return rows

def corrupt_scientific(rows, fields, rate=0.01):
    for r in rows:
        for f in fields:
            if isinstance(r.get(f), (int, float)) and random.random() < rate:
                r[f] = f"{r[f]:.2e}"
    return rows

def corrupt_price_symbol(rows, field="price_per_oz_usd", rate=0.04):
    for r in rows:
        if isinstance(r.get(field), (int, float)) and random.random() < rate:
            r[field] = f"${r[field]:,}"
    return rows

# ---------- ГЕНЕРАЦИЯ production ----------

def gen_production(n=3000):
    rows = []
    start_year = 2024
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    for i in range(n):
        mine, company, country = random.choice(MINES)
        year = random.choice([2024, 2025])
        q = random.choice(quarters)
        # ore tonnes — реалистичный диапазон для рудника
        ore = random.randint(300_000, 2_500_000)
        grade = round(random.uniform(0.5, 12.0), 2)  # g/t
        # produced oz — грубая оценка: ore * grade / 31.1 * recovery(0.85–0.95)
        oz = int(ore * grade / 31.1 * random.uniform(0.85, 0.95))
        cost = random.randint(750, 1_400)
        status = random.choices(
            ["active", "ramp-up", "planned", "care & maintenance"],
            weights=[70, 15, 10, 5]
        )[0]
        rows.append({
            "record_id": f"P{i+1:05d}",
            "mine_name": mine,
            "country": country,
            "company": company,
            "year": year,
            "quarter": q,
            "ore_tonnes": ore,
            "grade_g_t": grade,
            "gold_produced_oz": oz,
            "production_cost_usd_oz": cost,
            "status": status,
            "notes": random.choice(["", "higher grades Q4 expected", "oxide leaching",
                                     "underground", "open pit", "concentrate", "doré",
                                     "timing of deliveries", "steady-state"]),
        })
    # загрязнения
    rows = corrupt_null(rows, ["company", "ore_tonnes", "grade_g_t", "production_cost_usd_oz"], rate=0.04)
    rows = corrupt_negative(rows, ["ore_tonnes", "gold_produced_oz"], rate=0.015)
    rows = corrupt_country_typo(rows, rate=0.04)
    rows = corrupt_scientific(rows, ["ore_tonnes"], rate=0.008)
    rows = corrupt_decimal_comma(rows)
    # "grade" с запятой — уже через corrupt_decimal_comma
    rows = maybe_duplicate(rows, rate=0.08)
    return rows

# ---------- ГЕНЕРАЦИЯ logistics ----------

def gen_logistics(n=2500):
    rows = []
    modes = ["truck", "rail", "ship", "multimodal"]
    cargo_types = ["concentrate", "doré", "ore", "refined bars"]
    base = date(2024, 1, 1)
    for i in range(n):
        mine, company, country = random.choice(MINES)
        port = random.choice(DEST_PORTS[country])
        mode = random.choice(modes)
        distance = random.randint(150, 1_200)
        cargo = random.choice(cargo_types)
        weight = random.randint(8, 220) if cargo in ("doré", "refined bars") else random.randint(50, 400)
        dep = base + timedelta(days=random.randint(0, 700))
        arr = dep + timedelta(days=random.randint(2, 14))
        rows.append({
            "shipment_id": f"L{i+1:05d}",
            "mine_name": mine,
            "destination_port": port,
            "transport_mode": mode,
            "distance_km": distance,
            "cargo_type": cargo,
            "cargo_weight_tonnes": weight,
            "departure_date": dep.isoformat(),
            "arrival_date": arr.isoformat(),
            "carrier": random.choice(CARRIERS),
            "status": random.choices(["delivered", "in transit", "delayed", "customs hold"],
                                     weights=[65, 20, 10, 5])[0],
        })
    # загрязнения
    rows = corrupt_null(rows, ["distance_km", "carrier"], rate=0.05)
    rows = corrupt_units(rows, "cargo_weight_tonnes", rate=0.03, suffix=" т")
    rows = corrupt_dates_reversed(rows, rate=0.04)
    rows = maybe_duplicate(rows, rate=0.10)
    return rows

# ---------- ГЕНЕРАЦИЯ sales ----------

def gen_sales(n=2800):
    rows = []
    base = date(2024, 1, 1)
    for i in range(n):
        mine, company, country = random.choice(MINES)
        buyer = random.choice(BUYER_COUNTRIES)
        sale_date = base + timedelta(days=random.randint(0, 700))
        qty = random.randint(500, 9_000)  # oz
        price = random.randint(1_750, 2_050)  # USD/oz, реалистично для 2024–2025
        total = qty * price
        rows.append({
            "sale_id": f"S{i+1:05d}",
            "mine_name": mine,
            "buyer_country": buyer,
            "sale_date": sale_date.isoformat(),
            "quantity_oz": qty,
            "price_per_oz_usd": price,
            "total_revenue_usd": total,
            "payment_terms": random.choice(PAYMENT_TERMS),
            "incoterms": random.choice(INCOTERMS),
        })
    # загрязнения
    rows = corrupt_null(rows, ["buyer_country", "price_per_oz_usd"], rate=0.04)
    rows = corrupt_negative(rows, ["quantity_oz", "total_revenue_usd"], rate=0.015)
    rows = corrupt_price_symbol(rows, rate=0.05)
    # логическое противоречие: total != qty * price (уже может возникнуть из-за отрицательных)
    # специально ломаем 3% строк
    for r in rows:
        if random.random() < 0.03 and isinstance(r["quantity_oz"], (int, float)) and isinstance(r["price_per_oz_usd"], (int, float)):
            r["total_revenue_usd"] = int(r["total_revenue_usd"] * random.uniform(0.7, 1.3))
    rows = maybe_duplicate(rows, rate=0.10)
    return rows

# ---------- ЗАПИСЬ В CSV ----------

def write_csv(rows, path, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{path}: {len(rows)} rows")

if __name__ == "__main__":
    prod = gen_production(3000)
    log = gen_logistics(2500)
    sal = gen_sales(2800)

    write_csv(prod, "production.csv",
              ["record_id", "mine_name", "country", "company", "year", "quarter",
               "ore_tonnes", "grade_g_t", "gold_produced_oz", "production_cost_usd_oz",
               "status", "notes"])
    write_csv(log, "logistics.csv",
              ["shipment_id", "mine_name", "destination_port", "transport_mode",
               "distance_km", "cargo_type", "cargo_weight_tonnes", "departure_date",
               "arrival_date", "carrier", "status"])
    write_csv(sal, "sales.csv",
              ["sale_id", "mine_name", "buyer_country", "sale_date", "quantity_oz",
               "price_per_oz_usd", "total_revenue_usd", "payment_terms", "incoterms"])
