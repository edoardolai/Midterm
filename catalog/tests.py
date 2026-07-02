"""Tests for the REST endpoints (and a smoke test for the two HTML pages).

Test data is built with the factories in factories.py. Each test class
seeds only what it needs in setUpTestData, with explicit prices so the
expected discounts and averages can be checked by hand.
"""
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .factories import BrandFactory, CategoryFactory, ProductFactory
from .models import Product


class ProductDetailTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(
            name="Detail Product",
            retail_price=Decimal("100.00"),
            sale_price=Decimal("60.00"),
            rating=Decimal("4.5"),
        )

    def test_detail_returns_product_with_nested_relations(self):
        url = reverse("catalog:product-detail", args=[self.product.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["name"], "Detail Product")
        # category and brand come back nested, not as bare ids
        self.assertEqual(data["category"]["name"], self.product.category.name)
        self.assertEqual(data["brand"]["name"], self.product.brand.name)
        # 100 -> 60 is 40% off
        self.assertEqual(float(data["discount_pct"]), 40.0)

    def test_detail_404_for_missing_product(self):
        url = reverse("catalog:product-detail", args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CategoryProductsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = CategoryFactory(name="Shoes")
        cls.small = ProductFactory(
            category=cls.category,
            retail_price=Decimal("100.00"), sale_price=Decimal("90.00"),  # 10%
        )
        cls.big = ProductFactory(
            category=cls.category,
            retail_price=Decimal("100.00"), sale_price=Decimal("50.00"),  # 50%
        )
        cls.zero_retail = ProductFactory(
            category=cls.category,
            retail_price=Decimal("0.00"), sale_price=Decimal("0.00"),
        )
        cls.other = ProductFactory()  # different category, must not appear

    def test_returns_only_that_category_ordered_by_discount(self):
        url = reverse("catalog:category-products", args=[self.category.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row["id"] for row in response.json()]
        # biggest discount first, other category absent
        self.assertEqual(ids, [self.big.pk, self.small.pk])

    def test_zero_retail_price_products_are_excluded(self):
        url = reverse("catalog:category-products", args=[self.category.pk])
        ids = [row["id"] for row in self.client.get(url).json()]
        self.assertNotIn(self.zero_retail.pk, ids)


class DealsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = CategoryFactory(name="Electronics")
        cls.deal_60 = ProductFactory(
            category=cls.category,
            retail_price=Decimal("100.00"), sale_price=Decimal("40.00"),  # 60%
        )
        cls.deal_20 = ProductFactory(
            retail_price=Decimal("100.00"), sale_price=Decimal("80.00"),  # 20%
        )
        cls.no_deal = ProductFactory(
            retail_price=Decimal("100.00"), sale_price=Decimal("100.00"),  # 0%
        )

    def test_min_discount_filters_products(self):
        url = reverse("catalog:deals-list")
        response = self.client.get(url, {"min_discount": "50"})
        ids = [row["id"] for row in response.json()]
        self.assertEqual(ids, [self.deal_60.pk])

    def test_defaults_to_zero_when_min_discount_missing_or_invalid(self):
        url = reverse("catalog:deals-list")
        for params in ({}, {"min_discount": "not-a-number"}):
            ids = [row["id"] for row in self.client.get(url, params).json()]
            # everything with retail > 0 comes back, biggest discount first
            self.assertEqual(
                ids, [self.deal_60.pk, self.deal_20.pk, self.no_deal.pk]
            )

    def test_category_param_narrows_results(self):
        url = reverse("catalog:deals-list")
        response = self.client.get(
            url, {"min_discount": "10", "category": self.category.pk}
        )
        ids = [row["id"] for row in response.json()]
        self.assertEqual(ids, [self.deal_60.pk])


class BrandDetailTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.brand = BrandFactory(name="TestBrand")
        ProductFactory(
            brand=cls.brand,
            retail_price=Decimal("200.00"), sale_price=Decimal("100.00"),  # 50%
            rating=Decimal("4.0"),
        )
        ProductFactory(
            brand=cls.brand,
            retail_price=Decimal("100.00"), sale_price=Decimal("90.00"),   # 10%
            rating=Decimal("3.0"),
        )
        # excluded from the stats by the retail_price > 0 rule
        ProductFactory(
            brand=cls.brand,
            retail_price=Decimal("0.00"), sale_price=Decimal("0.00"),
        )

    def test_stats_are_aggregated_over_positive_retail_products(self):
        url = reverse("catalog:brand-detail", args=[self.brand.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["name"], "TestBrand")
        stats = data["stats"]
        self.assertEqual(stats["product_count"], 2)
        self.assertAlmostEqual(float(stats["avg_retail_price"]), 150.0)
        self.assertAlmostEqual(float(stats["min_retail_price"]), 100.0)
        self.assertAlmostEqual(float(stats["max_retail_price"]), 200.0)
        self.assertAlmostEqual(float(stats["avg_discount_pct"]), 30.0)  # (50+10)/2
        self.assertAlmostEqual(float(stats["avg_rating"]), 3.5)
        self.assertEqual(len(data["products"]), 2)

    def test_404_for_missing_brand(self):
        url = reverse("catalog:brand-detail", args=[99999])
        self.assertEqual(
            self.client.get(url).status_code, status.HTTP_404_NOT_FOUND
        )


class CategoryPricingAnalyticsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cheap = CategoryFactory(name="Cheap Deals")
        ProductFactory(category=cheap,
                       retail_price=Decimal("100.00"), sale_price=Decimal("40.00"))  # 60%
        ProductFactory(category=cheap,
                       retail_price=Decimal("50.00"), sale_price=Decimal("30.00"))   # 40%
        full_price = CategoryFactory(name="Full Price")
        ProductFactory(category=full_price,
                       retail_price=Decimal("80.00"), sale_price=Decimal("80.00"))   # 0%
        ProductFactory(category=full_price,
                       retail_price=Decimal("0.00"), sale_price=Decimal("0.00"))     # excluded

    def test_one_row_per_category_with_correct_aggregates(self):
        url = reverse("catalog:category-pricing")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rows = response.json()
        by_name = {row["category__name"]: row for row in rows}

        cheap = by_name["Cheap Deals"]
        self.assertEqual(cheap["product_count"], 2)
        self.assertAlmostEqual(float(cheap["avg_retail_price"]), 75.0)
        self.assertAlmostEqual(float(cheap["avg_sale_price"]), 35.0)
        self.assertAlmostEqual(float(cheap["avg_discount_pct"]), 50.0)  # (60+40)/2

        full = by_name["Full Price"]
        # the zero-retail product is excluded, so one product remains
        self.assertEqual(full["product_count"], 1)
        self.assertAlmostEqual(float(full["avg_discount_pct"]), 0.0)

    def test_ordered_by_average_discount_descending(self):
        url = reverse("catalog:category-pricing")
        rows = self.client.get(url).json()
        discounts = [float(row["avg_discount_pct"]) for row in rows]
        self.assertEqual(discounts, sorted(discounts, reverse=True))


class ProductCreateTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = CategoryFactory()
        cls.brand = BrandFactory()

    def payload(self, **overrides):
        data = {
            "source_id": "created-001",
            "name": "Created Product",
            "description": "",
            "category": self.category.pk,
            "brand": self.brand.pk,
            "retail_price": "50.00",
            "sale_price": "40.00",
            "rating": None,
            "image_url": "",
            "product_url": "",
        }
        data.update(overrides)
        return data

    def test_valid_post_creates_product(self):
        url = reverse("catalog:product-create")
        response = self.client.post(url, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product.objects.filter(source_id="created-001").exists())

    def test_sale_price_above_retail_is_rejected(self):
        url = reverse("catalog:product-create")
        bad = self.payload(retail_price="10.00", sale_price="20.00")
        response = self.client.post(url, bad, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sale_price", response.json())
        self.assertEqual(Product.objects.count(), 0)

    def test_missing_required_fields_are_rejected(self):
        url = reverse("catalog:product-create")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProductUpdateDeleteTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(
            retail_price=Decimal("100.00"), sale_price=Decimal("80.00")
        )
        cls.new_category = CategoryFactory(name="Moved Here")

    def full_payload(self, **overrides):
        p = self.product
        data = {
            "source_id": p.source_id,
            "name": p.name,
            "description": p.description,
            "category": p.category.pk,
            "brand": p.brand.pk,
            "retail_price": "100.00",
            "sale_price": "80.00",
            "rating": None,
            "image_url": "",
            "product_url": "",
        }
        data.update(overrides)
        return data

    def test_put_updates_fields_including_category(self):
        url = reverse("catalog:product-detail", args=[self.product.pk])
        payload = self.full_payload(
            name="Renamed", category=self.new_category.pk, sale_price="70.00"
        )
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Renamed")
        self.assertEqual(self.product.category, self.new_category)
        self.assertEqual(self.product.sale_price, Decimal("70.00"))

    def test_put_rejects_sale_price_above_retail(self):
        url = reverse("catalog:product-detail", args=[self.product.pk])
        bad = self.full_payload(retail_price="10.00", sale_price="20.00")
        response = self.client.put(url, bad, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sale_price", response.json())

    def test_delete_removes_product(self):
        url = reverse("catalog:product-detail", args=[self.product.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            self.client.get(url).status_code, status.HTTP_404_NOT_FOUND
        )


class HtmlPagesTests(APITestCase):
    """Smoke tests for the two browser pages."""

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()

    def test_main_page_lists_endpoints_and_metadata(self):
        response = self.client.get(reverse("catalog:index"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        html = response.content.decode()
        self.assertIn("/api/deals/", html)
        self.assertIn("/api/analytics/category-pricing/", html)
        self.assertIn(f"/api/product/{self.product.pk}/", html)
        self.assertIn("admin123", html)

    def test_form_page_rejects_sale_above_retail_via_model_clean(self):
        data = {
            "source_id": "form-001", "name": "Form Product", "description": "",
            "category": self.product.category.pk, "brand": "",
            "retail_price": "10.00", "sale_price": "20.00",
            "rating": "", "image_url": "", "product_url": "",
        }
        response = self.client.post(reverse("catalog:product-add"), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # re-rendered
        self.assertContains(
            response, "Sale price cannot be higher than retail price."
        )
        self.assertFalse(Product.objects.filter(source_id="form-001").exists())

    def test_form_page_creates_and_redirects(self):
        data = {
            "source_id": "form-002", "name": "Form Product", "description": "",
            "category": self.product.category.pk, "brand": "",
            "retail_price": "20.00", "sale_price": "10.00",
            "rating": "", "image_url": "", "product_url": "",
        }
        response = self.client.post(reverse("catalog:product-add"), data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        new = Product.objects.get(source_id="form-002")
        self.assertEqual(response.headers["Location"],
                         reverse("catalog:product-detail", args=[new.pk]))