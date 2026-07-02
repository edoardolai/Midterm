"""factory_boy factories for building test data.

Defaults are deliberately simple: a product at 100 retail / 80 sale (a 20%
discount) with no rating. Tests override the fields in case it matters.
"""
from decimal import Decimal

import factory

from . import models


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Category
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Category {n}")


class BrandFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Brand
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Brand {n}")


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Product

    source_id = factory.Sequence(lambda n: f"test-{n:04d}")
    name = factory.Sequence(lambda n: f"Product {n}")
    description = ""
    category = factory.SubFactory(CategoryFactory)
    brand = factory.SubFactory(BrandFactory)
    retail_price = Decimal("100.00")
    sale_price = Decimal("80.00")
    rating = None
    image_url = ""
    product_url = ""