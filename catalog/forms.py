from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    """Browser-side form for adding a product.

    ModelForm validation runs the model's clean() automatically, so the
    sale price <= retail price rule applies here without repeating it
    (unlike the DRF serializer, where it had to be re-implemented).
    """

    class Meta:
        model = Product
        fields = [
            "source_id", "name", "description", "category", "brand",
            "retail_price", "sale_price", "rating", "image_url", "product_url",
        ]