"""HTML views for the catalog app: the main page and the add-product form.

The REST endpoints live in api.py; these views are the browser-facing side.
"""
import sys

import django
import rest_framework
from django.shortcuts import redirect, render

from .forms import ProductForm
from .models import Brand, Category, Product


def index(request):
    """Main page: every endpoint as a clickable link, plus the environment
    details the brief asks for (versions, packages, admin login).
    """
    # sample rows so the parameterised endpoints are clickable
    product = Product.objects.first()
    category = Category.objects.first()
    brand = Brand.objects.first()

    context = {
        "product": product,
        "category": category,
        "brand": brand,
        "python_version": sys.version.split()[0],
        "django_version": django.get_version(),
        "drf_version": rest_framework.VERSION,
    }
    return render(request, "catalog/index.html", context)



def product_add(request):
    """Add a product through a normal HTML form.

    GET renders an empty form; POST validates and saves, then redirects to
    the new product's API detail page (so a refresh can't resubmit).
    """
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            return redirect("catalog:product-detail", pk=product.pk)
    else:
        form = ProductForm()
    return render(request, "catalog/product_add.html", {"form": form})

def deals_page(request):
    """Interactive deals browser. The page itself is server-rendered (the
    category dropdown comes from the DB); the results table is filled
    client-side by deals.js calling the /api/deals/ endpoint.
    """
    categories = Category.objects.all()
    return render(request, "catalog/deals.html", {"categories": categories})

