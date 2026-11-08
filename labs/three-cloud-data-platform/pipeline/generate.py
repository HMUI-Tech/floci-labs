"""Make fake shop data for one or more days: customers, products and orders.

The same date always gives the same data. Every random choice is seeded from a
fixed number (customers, products) or from the date itself (orders).

  python generate.py --date 2026-11-02            # one day
  python generate.py --date 2026-11-02 --days 7   # a week, starting that day

Writes JSON lines to data/jsonl/dt=YYYY-MM-DD/:
  orders.jsonl     that day's orders, one per line
  customers.jsonl  every customer as they were that day (about a quarter move house
                   at some point in the six months, which later feeds the SCD Type 2 task)
  products.jsonl   the product catalogue
"""

import argparse
import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from faker import Faker

OUT = Path(__file__).parent / "data" / "jsonl"

SEED = 42  # fixed seed for customers and products
N_CUSTOMERS = 300
MOVE_SHARE = 0.25  # share of customers who move house during the plan
MOVE_WINDOW = (date(2026, 11, 3), date(2027, 5, 2))  # roughly the 26 weeks of the plan

# category: (lowest price, highest price, items)
CATALOGUE = {
    "Kitchen": (8, 120, ["Kettle", "Toaster", "Chef's Knife", "Frying Pan", "Blender", "Mixing Bowls", "Coffee Grinder", "Cutting Board"]),
    "Garden": (5, 90, ["Hose", "Trowel", "Pruning Shears", "Plant Pot", "Bird Feeder", "Watering Can", "Garden Gloves", "Rake"]),
    "Electronics": (25, 400, ["Headphones", "Speaker", "USB-C Charger", "Webcam", "Keyboard", "Mouse", "Monitor Stand", "Power Bank"]),
    "Books": (6, 40, ["Cookbook", "Travel Guide", "Crime Novel", "Sci-Fi Novel", "Gardening Handbook", "Python Primer", "Atlas", "Poetry Collection"]),
    "Toys": (5, 60, ["Jigsaw Puzzle", "Building Blocks", "Board Game", "Kite", "Plush Bear", "Toy Car", "Yo-yo", "Card Game"]),
}
STYLES = ["Classic", "Compact", "Deluxe", "Eco", "Pro", "Mini", "Family", "Travel"]

STATUSES = (["completed", "cancelled", "returned"], [92, 5, 3])
QUANTITIES = ([1, 2, 3, 4], [70, 20, 7, 3])


def make_products():
    rng = random.Random(f"products-{SEED}")
    products = []
    for category, (low, high, items) in CATALOGUE.items():
        for item in items:
            price = max(1, round(rng.uniform(low, high))) - 0.01  # prices end in .99
            products.append({
                "product_id": f"P{len(products) + 1:03d}",
                "name": f"{rng.choice(STYLES)} {item}",
                "category": category,
                "price": round(price, 2),
            })
    return products


def make_customers():
    """Each customer gets a home address and, for some, a later address and the day they move."""
    customers = []
    for n in range(1, N_CUSTOMERS + 1):
        rng = random.Random(f"customer-{SEED}-{n}")
        fake = Faker("en_US")
        fake.seed_instance(rng.randrange(2**32))

        def address():
            return {"street": fake.street_address(), "city": fake.city(), "state": fake.state_abbr(), "postcode": fake.postcode()}

        first, last = fake.first_name(), fake.last_name()
        signup = date(2024, 1, 1) + timedelta(days=rng.randrange((date(2026, 10, 31) - date(2024, 1, 1)).days))
        customer = {
            "customer_id": f"C{n:04d}",
            "first_name": first,
            "last_name": last,
            "email": f"{first}.{last}.{n}@example.com".lower(),
            "signup_date": signup,
            "home": address(),
            "moves_on": None,
            "new_home": None,
        }
        if rng.random() < MOVE_SHARE:
            span = (MOVE_WINDOW[1] - MOVE_WINDOW[0]).days
            customer["moves_on"] = MOVE_WINDOW[0] + timedelta(days=rng.randrange(span))
            customer["new_home"] = address()
        customers.append(customer)
    return customers


def customers_on(customers, day):
    """Every customer as they were on `day`: the new address once they've moved."""
    rows = []
    for c in customers:
        moved = c["moves_on"] is not None and day >= c["moves_on"]
        rows.append({
            "customer_id": c["customer_id"],
            "first_name": c["first_name"],
            "last_name": c["last_name"],
            "email": c["email"],
            "signup_date": c["signup_date"].isoformat(),
            **(c["new_home"] if moved else c["home"]),
            "updated_at": (c["moves_on"] if moved else c["signup_date"]).isoformat(),
        })
    return rows


def orders_on(day, customers, products):
    rng = random.Random(f"orders-{day.isoformat()}")

    # Some customers and products are far more popular than others. These weights
    # come from the fixed seed, so the same customers stay loyal every day.
    weights_rng = random.Random(f"weights-{SEED}")
    customer_weights = [weights_rng.expovariate(1) for _ in customers]
    product_weights = [weights_rng.expovariate(1) for _ in products]

    count = 100 + (40 if day.weekday() >= 5 else 0) + rng.randint(-15, 15)
    midnight = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    orders = []
    for _ in range(count):
        product = rng.choices(products, product_weights)[0]
        # Most orders land in the evening: a triangle peaking at 19:00.
        seconds = int(rng.triangular(0, 86_399, 19 * 3600))
        orders.append({
            "order_ts": (midnight + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "customer_id": rng.choices(customers, customer_weights)[0]["customer_id"],
            "product_id": product["product_id"],
            "quantity": rng.choices(*QUANTITIES)[0],
            "unit_price": product["price"],
            "status": rng.choices(*STATUSES)[0],
        })

    orders.sort(key=lambda o: o["order_ts"])
    return [{"order_id": f"O{day:%Y%m%d}-{i:04d}", **o} for i, o in enumerate(orders, 1)]


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--date", required=True, type=date.fromisoformat, help="first day, e.g. 2026-11-02")
    parser.add_argument("--days", type=int, default=1, help="how many days to make (default 1)")
    args = parser.parse_args()

    products = make_products()
    customers = make_customers()

    for offset in range(args.days):
        day = args.date + timedelta(days=offset)
        folder = OUT / f"dt={day.isoformat()}"
        folder.mkdir(parents=True, exist_ok=True)

        orders = orders_on(day, customers, products)
        write_jsonl(folder / "orders.jsonl", orders)
        write_jsonl(folder / "customers.jsonl", customers_on(customers, day))
        write_jsonl(folder / "products.jsonl", products)
        print(f"{day}: {len(orders):>3} orders, {len(customers)} customers, {len(products)} products -> {folder.relative_to(OUT.parent.parent)}")


if __name__ == "__main__":
    main()
