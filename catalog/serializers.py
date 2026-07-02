from rest_framework import serializers

from .models import Brand, Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    """Read representation: category/brand nested, discount_pct included
    even though it's a model property, not a real field.
    """
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    discount_pct = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            "id", "source_id", "name", "description", "category", "brand",
            "retail_price", "sale_price", "discount_pct", "rating",
            "image_url", "product_url",
        ]


class ProductWriteSerializer(serializers.ModelSerializer):
    """Used for the write operations (POST create, PUT update). category and
    brand are plain FK ids here, not the nested shape above.
    """

    class Meta:
        model = Product
        fields = [
            "source_id", "name", "description", "category", "brand",
            "retail_price", "sale_price", "rating", "image_url", "product_url",
        ]

    def validate(self, data):
        # Product.clean() enforces this too, but DRF never calls clean() on
        # a ModelSerializer, so the same check is repeated here.
        retail = data.get("retail_price")
        sale = data.get("sale_price")
        if retail is not None and sale is not None and sale > retail:
            raise serializers.ValidationError(
                {"sale_price": "Sale price cannot be higher than retail price."}
            )
        return data