from decimal import Decimal, InvalidOperation

from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Max, Min
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Brand, Product
from .serializers import ProductSerializer, ProductWriteSerializer


def with_discount(queryset):
    """Annotate a Product queryset with discount as a real DB column
    (discount_pct_db), since the model's discount_pct property only works
    in Python and can't be used in filter()/order_by()/aggregate().

    Only meaningful for retail_price > 0, so those rows are dropped here
    rather than guarded inside the expression - see the report for why.
    """
    return queryset.filter(retail_price__gt=0).annotate(
        discount_pct_db=ExpressionWrapper(
            (F("retail_price") - F("sale_price")) * 100 / F("retail_price"),
            output_field=DecimalField(max_digits=5, decimal_places=1),
        )
    )


class ProductDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    """GET / PUT / DELETE /api/product/<pk>/ - one product.

    The brief asks for retrieve, add, update and delete, so this one URL
    also carries these methods. Each method forwards to the
    matching mixin action.
    """
    queryset = Product.objects.select_related("category", "brand")

    def get_serializer_class(self):
        # reads return the nested shape; updates need writable FK ids
        if self.request.method == "PUT":
            return ProductWriteSerializer
        return ProductSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class ProductCreate(generics.CreateAPIView):
    """POST /api/product/ - add a product."""
    queryset = Product.objects.all()
    serializer_class = ProductWriteSerializer


class CategoryProducts(generics.ListAPIView):
    """GET /api/category/<category_pk>/products/ - products in one
    category, biggest discount first.
    """
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = Product.objects.filter(
            category_id=self.kwargs["category_pk"]
        ).select_related("category", "brand")
        return with_discount(qs).order_by("-discount_pct_db")


class DealsList(generics.ListAPIView):
    """GET /api/deals/?min_discount=40&category=<id> - products at or
    above a discount threshold, optionally narrowed to one category.
    min_discount defaults to 0 if missing or not a number, so hitting the
    endpoint with no params still returns something sensible.
    """
    serializer_class = ProductSerializer

    def get_queryset(self):
        try:
            min_discount = Decimal(self.request.query_params.get("min_discount", "0"))
        except InvalidOperation:
            min_discount = Decimal("0")

        qs = Product.objects.select_related("category", "brand")
        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)

        return (
            with_discount(qs)
            .filter(discount_pct_db__gte=min_discount)
            .order_by("-discount_pct_db")
        )


class BrandDetail(APIView):
    """GET /api/brand/<pk>/ - brand info, aggregate stats, and its products."""

    def get(self, request, pk):
        brand = get_object_or_404(Brand, pk=pk)
        products = with_discount(Product.objects.filter(brand=brand))

        stats = products.aggregate(
            product_count=Count("id"),
            avg_retail_price=Avg("retail_price"),
            min_retail_price=Min("retail_price"),
            max_retail_price=Max("retail_price"),
            avg_discount_pct=Avg("discount_pct_db"),
            avg_rating=Avg("rating"),
        )

        data = {
            "id": brand.id,
            "name": brand.name,
            "stats": stats,
            "products": ProductSerializer(
                products.select_related("category", "brand"), many=True
            ).data,
        }
        return Response(data)


class CategoryPricingAnalytics(APIView):
    """GET /api/analytics/category-pricing/ - per-category pricing and
    discount averages, biggest average discount first.
    """

    def get(self, request):
        rows = (
            with_discount(Product.objects.all())
            .values("category__name")
            .annotate(
                product_count=Count("id"),
                avg_retail_price=Avg("retail_price"),
                avg_sale_price=Avg("sale_price"),
                avg_discount_pct=Avg("discount_pct_db"),
            )
            .order_by("-avg_discount_pct")
        )
        return Response(rows)