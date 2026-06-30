"""
Quick look at the Flipkart CSV before deciding on the models.
Just checking shapes, missing values, and the messy columns
(prices, ratings, the category tree) so I know what I'm modelling.
"""
import ast

import pandas as pd

df = pd.read_csv("dataset.csv")

print("shape:", df.shape)
print()

print("columns:")
print(list(df.columns))
print()

# missing values per column
print("nulls per column:")
print(df.isna().sum())
print()

# the two price columns come in as strings - how many won't convert to a number?
for col in ["retail_price", "discounted_price"]:
    nums = pd.to_numeric(df[col], errors="coerce")
    print(f"{col}: {nums.isna().sum()} non-numeric/blank, "
          f"range {nums.min()} - {nums.max()}")
print()

# how often is sale price actually above retail (bad rows we'd drop)?
retail = pd.to_numeric(df["retail_price"], errors="coerce")
sale = pd.to_numeric(df["discounted_price"], errors="coerce")
print("rows where sale > retail:", (sale > retail).sum())
print()

# rating columns - suspect these are mostly text
print("product_rating top values:")
print(df["product_rating"].value_counts().head())
print()

# brand coverage
print("distinct brands:", df["brand"].nunique())
print("rows with no brand:", df["brand"].isna().sum())
print()

# uniq_id - is it actually unique? (want to use it as the dedupe key)
print("duplicate uniq_id count:", df["uniq_id"].duplicated().sum())
print()


# the category column is a stringified list like ["A >> B >> C >> ..."].
# pull the top-level category off each row and see how many distinct ones there are.
def top_category(raw):
    try:
        tree = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return None
    if not tree:
        return None
    return tree[0].split(">>")[0].strip()


top = df["product_category_tree"].dropna().apply(top_category)
print("distinct top-level categories:", top.nunique())
print()
print("top 15 categories by count:")
print(top.value_counts().head(15))
