"""
Load and store script for the Flipkart product dataset.

Reads dataset.csv, cleans each row, and stores it as Category / Brand /
Product records. Run from the project root with:

    python load_data.py

Safe to re-run: products are matched on their source id, so existing
rows are updated rather than duplicated.
"""
import ast
import csv
import os
from decimal import Decimal, InvalidOperation

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "retailapi.settings")
django.setup()

from catalog.models import Brand, Category, Product  # noqa: E402  (must follow setup)


CSV_PATH = "dataset.csv"
MAX_ROWS = 8000         


def parse_top_category(raw):
    if not raw:
        return None
    try:
        tree = ast.literal_eval(raw)        # the cell is a Python-list literal
    except (ValueError, SyntaxError):
        return None
    if not tree:
        return None
    return tree[0].split(">>")[0].strip()


def parse_first_image(raw):
    """The image column is a stringified list of URLs; take the first."""
    if not raw:
        return ""
    try:
        urls = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return ""
    return urls[0].strip() if urls else ""


def parse_price(raw):
    """Return a Decimal, or None if the cell is blank/non-numeric."""
    if not raw:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def parse_rating(raw):
    """Ratings are often the text 'No rating available' -> treat as None."""
    if not raw or raw.strip() == "No rating available":
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def run():
    created, updated, skipped = 0, 0, 0

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            if i >= MAX_ROWS:
                break

            retail = parse_price(row["retail_price"])
            sale = parse_price(row["discounted_price"])
            category_name = parse_top_category(row["product_category_tree"])

            # a product is useless without prices and a category
            if retail is None or sale is None or not category_name:
                skipped += 1
                continue

            # drop the occasional dirty row where the discount is impossible
            if sale > retail:
                skipped += 1
                continue

            category, _ = Category.objects.get_or_create(name=category_name)

            brand = None
            brand_name = row["brand"].strip()
            if brand_name:
                brand, _ = Brand.objects.get_or_create(name=brand_name)

            _, was_created = Product.objects.update_or_create(
                source_id=row["uniq_id"],
                defaults={
                    "name": row["product_name"].strip(),
                    "description": row["description"].strip(),
                    "category": category,
                    "brand": brand,
                    "retail_price": retail,
                    "sale_price": sale,
                    "rating": parse_rating(row["overall_rating"]),
                    "image_url": parse_first_image(row["image"]),
                    "product_url": row["product_url"].strip(),
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

    print(f"done. created={created} updated={updated} skipped={skipped}")


if __name__ == "__main__":
    run()