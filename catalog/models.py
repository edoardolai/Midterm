from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    # uniq_id from the source CSV; kept so re-running the loader updates rows
    # in place instead of creating duplicates
    source_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    # many source rows have no brand, so it's optional
    brand = models.ForeignKey(
        Brand, on_delete=models.SET_NULL, related_name="products",
        null=True, blank=True,
    )

    retail_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    sale_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("5"))],
    )

    image_url = models.URLField(max_length=500, blank=True)
    product_url = models.URLField(max_length=500, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def discount_pct(self):
        # percent off retail; clamped at 0 so dirty data can't make it negative
        if not self.retail_price or self.retail_price <= 0:
            return Decimal("0")
        off = (self.retail_price - self.sale_price) / self.retail_price * 100
        if off < 0:
            return Decimal("0")
        return off.quantize(Decimal("0.1"))

    def clean(self):
        # NOTE: this runs for ModelForm/admin saves, but DRF serializers do
        # NOT call it — so the same rule is repeated in the serializer later.
        if self.sale_price is not None and self.retail_price is not None:
            if self.sale_price > self.retail_price:
                raise ValidationError(
                    {"sale_price": "Sale price cannot be higher than retail price."}
                )