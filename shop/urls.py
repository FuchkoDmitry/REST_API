from django.urls import path

from shop.views import ImportProductsView, ShopsView, CategoriesView, ProductsView

urlpatterns = [
    path('partner/update/', ImportProductsView.as_view()),
    path('shops/', ShopsView.as_view()),
    path('categories/', CategoriesView.as_view()),
    # path('products/<int:pk>/', ProductsView.as_view()),
    path('products/', ProductsView.as_view())
]
