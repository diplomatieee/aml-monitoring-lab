"""
Synthetic data generator for the AML alert triage demo.

Generates two CSV files (customers, transactions) with 7 intentionally
planted suspicious scenarios so the SQL detection rules have something
to find. All data is fake. Do not use for anything besides this demo.
"""

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

# 재현성을 위한 시드 고정
SEED = 42
random.seed(SEED)
fake = Faker("ko_KR")
Faker.seed(SEED)

# 기본 파라미터
NUM_CUSTOMERS = 100
NUM_TRANSACTIONS = 500
DATE_START = datetime(2026, 1, 1)
DATE_END = datetime(2026, 4, 20)

AGE_BANDS = ["20s", "30s", "40s", "50s", "60s+"]
OCCUPATIONS = ["student", "salaried", "self_employed", "retired", "unemployed"]
INCOME_BANDS = ["LOW", "MID", "HIGH"]
CHANNELS = ["ATM", "MOBILE_APP", "WEB", "BRANCH"]


def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    offset = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=offset)


def generate_customers(n: int) -> list[dict]:
    customers = []
    for i in range(1, n + 1):
        onboarding = random_date(DATE_START, DATE_END - timedelta(days=5))
        customers.append(
            {
                "customer_id": f"C{i:04d}",
                "onboarding_date": onboarding.strftime("%Y-%m-%d"),
                "age_band": random.choice(AGE_BANDS),
                "occupation": random.choice(OCCUPATIONS),
                "income_band": random.choices(
                    INCOME_BANDS, weights=[0.3, 0.5, 0.2]
                )[0],
                "country_risk_flag": 1 if random.random() < 0.05 else 0,
                "watchlist_flag": 1 if random.random() < 0.02 else 0,
            }
        )
    return customers


def random_txn(
    customer_id: str,
    txn_idx: int,
    earliest: datetime,
    primary_device: str,
) -> dict:
    # 고객 온보딩 이전 거래는 현실에서 발생하지 않으므로 제한
    txn_dt = random_date(max(DATE_START, earliest), DATE_END)
    # 실제 분포에 가깝게 소액 거래 비중을 높게
    amount_bucket = random.choices(
        ["small", "medium", "large"], weights=[0.65, 0.28, 0.07]
    )[0]
    if amount_bucket == "small":
        amount = random.randint(10_000, 500_000)
    elif amount_bucket == "medium":
        amount = random.randint(500_000, 3_000_000)
    else:
        amount = random.randint(3_000_000, 8_000_000)
    # 본인 기기 사용이 일반적이나 가끔 다른 기기 혼용
    device_id = (
        primary_device
        if random.random() < 0.9
        else f"D{random.randint(1, 60):03d}"
    )
    return {
        "txn_id": f"T{txn_idx:05d}",
        "customer_id": customer_id,
        "txn_date": txn_dt.strftime("%Y-%m-%d"),
        "txn_datetime": txn_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "amount": amount,
        "cash_yn": "Y" if random.random() < 0.25 else "N",
        "channel": random.choice(CHANNELS),
        "counterparty_id": f"CP{random.randint(1, 200):04d}"
        if random.random() < 0.7
        else "",
        "device_id": device_id,
        "ip_country": "KR" if random.random() < 0.9 else "HIGH_RISK_COUNTRY",
    }


def generate_transactions(customers: list[dict], n: int) -> list[dict]:
    txns = []
    onboarding_lookup = {
        c["customer_id"]: datetime.strptime(c["onboarding_date"], "%Y-%m-%d")
        for c in customers
    }
    # 각 고객에게 주 사용 기기를 하나 배정 (현실에서는 본인 휴대폰/PC)
    primary_device = {
        c["customer_id"]: f"D{random.randint(1, 60):03d}" for c in customers
    }
    customer_ids = list(onboarding_lookup.keys())
    for i in range(1, n + 1):
        cid = random.choice(customer_ids)
        txns.append(
            random_txn(cid, i, onboarding_lookup[cid], primary_device[cid])
        )
    return txns


def inject_suspicious_scenarios(
    customers: list[dict], txns: list[dict]
) -> list[dict]:
    """
    Inject 7 planted scenarios so the detection rules have concrete hits.
    We append new transactions rather than mutating existing ones.
    """
    next_idx = len(txns) + 1

    # [SUSPICIOUS SCENARIO #1] Daily cash aggregation (CTR)
    # C0001 deposits 3x cash on the same day, totaling 15,000,000 KRW
    for amt in [6_000_000, 5_000_000, 4_000_000]:
        txns.append(
            {
                "txn_id": f"T{next_idx:05d}",
                "customer_id": "C0001",
                "txn_date": "2026-03-10",
                "txn_datetime": f"2026-03-10 {random.randint(9, 17):02d}:00:00",
                "amount": amt,
                "cash_yn": "Y",
                "channel": "BRANCH",
                "counterparty_id": "",
                "device_id": "D001",
                "ip_country": "KR",
            }
        )
        next_idx += 1

    # [SUSPICIOUS SCENARIO #2] Structured transactions under CTR threshold
    # C0002 makes 4 transactions of 9.1M-9.8M within 5 days
    for day, amt in [
        ("2026-03-05", 9_100_000),
        ("2026-03-07", 9_500_000),
        ("2026-03-08", 9_800_000),
        ("2026-03-09", 9_300_000),
    ]:
        txns.append(
            {
                "txn_id": f"T{next_idx:05d}",
                "customer_id": "C0002",
                "txn_date": day,
                "txn_datetime": f"{day} 14:00:00",
                "amount": amt,
                "cash_yn": "Y",
                "channel": "BRANCH",
                "counterparty_id": "",
                "device_id": "D002",
                "ip_country": "KR",
            }
        )
        next_idx += 1

    # [SUSPICIOUS SCENARIO #3] New account with large transaction within 30 days
    # Override C0023 onboarding to a recent date
    for c in customers:
        if c["customer_id"] == "C0023":
            c["onboarding_date"] = "2026-03-15"
    txns.append(
        {
            "txn_id": f"T{next_idx:05d}",
            "customer_id": "C0023",
            "txn_date": "2026-03-19",
            "txn_datetime": "2026-03-19 11:00:00",
            "amount": 15_000_000,
            "cash_yn": "N",
            "channel": "MOBILE_APP",
            "counterparty_id": "CP0123",
            "device_id": "D023",
            "ip_country": "KR",
        }
    )
    next_idx += 1

    # [SUSPICIOUS SCENARIO #4] Shared device across multiple accounts
    # D050 is shared by C0010, C0011, C0012, C0013
    for cid in ["C0010", "C0011", "C0012", "C0013"]:
        txns.append(
            {
                "txn_id": f"T{next_idx:05d}",
                "customer_id": cid,
                "txn_date": "2026-02-20",
                "txn_datetime": "2026-02-20 10:00:00",
                "amount": 2_000_000,
                "cash_yn": "N",
                "channel": "MOBILE_APP",
                "counterparty_id": "CP0099",
                "device_id": "D050",
                "ip_country": "KR",
            }
        )
        next_idx += 1

    # [SUSPICIOUS SCENARIO #5] Profile mismatch — LOW income, high monthly volume
    # C0030 is forced to LOW income; makes 60M+ in February 2026
    for c in customers:
        if c["customer_id"] == "C0030":
            c["income_band"] = "LOW"
            c["occupation"] = "student"
    for day, amt in [
        ("2026-02-05", 20_000_000),
        ("2026-02-12", 18_000_000),
        ("2026-02-20", 25_000_000),
    ]:
        txns.append(
            {
                "txn_id": f"T{next_idx:05d}",
                "customer_id": "C0030",
                "txn_date": day,
                "txn_datetime": f"{day} 13:30:00",
                "amount": amt,
                "cash_yn": "N",
                "channel": "WEB",
                "counterparty_id": f"CP0{random.randint(100, 199):03d}",
                "device_id": "D030",
                "ip_country": "KR",
            }
        )
        next_idx += 1

    # [SUSPICIOUS SCENARIO #6] Another structuring pattern (C0045)
    for day, amt in [
        ("2026-04-01", 9_200_000),
        ("2026-04-03", 9_700_000),
        ("2026-04-06", 9_400_000),
    ]:
        txns.append(
            {
                "txn_id": f"T{next_idx:05d}",
                "customer_id": "C0045",
                "txn_date": day,
                "txn_datetime": f"{day} 16:00:00",
                "amount": amt,
                "cash_yn": "Y",
                "channel": "ATM",
                "counterparty_id": "",
                "device_id": "D045",
                "ip_country": "KR",
            }
        )
        next_idx += 1

    # [SUSPICIOUS SCENARIO #7] New account + large cash deposit (C0060)
    for c in customers:
        if c["customer_id"] == "C0060":
            c["onboarding_date"] = "2026-04-01"
    txns.append(
        {
            "txn_id": f"T{next_idx:05d}",
            "customer_id": "C0060",
            "txn_date": "2026-04-10",
            "txn_datetime": "2026-04-10 09:15:00",
            "amount": 8_000_000,
            "cash_yn": "Y",
            "channel": "BRANCH",
            "counterparty_id": "",
            "device_id": "D060",
            "ip_country": "KR",
        }
    )
    next_idx += 1

    return txns


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic AML data")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent,
        help="Directory to write customers.csv and transactions.csv",
    )
    args = parser.parse_args()

    customers = generate_customers(NUM_CUSTOMERS)
    txns = generate_transactions(customers, NUM_TRANSACTIONS)
    txns = inject_suspicious_scenarios(customers, txns)

    write_csv(args.output_dir / "customers.csv", customers)
    write_csv(args.output_dir / "transactions.csv", txns)

    print(f"Wrote {len(customers)} customers -> {args.output_dir / 'customers.csv'}")
    print(f"Wrote {len(txns)} transactions -> {args.output_dir / 'transactions.csv'}")


if __name__ == "__main__":
    main()
