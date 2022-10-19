from django.urls import path

from shop.views import ImportProductsView, ShopsView, CategoriesView, CategoryItemsView, ShopItemsView, \
    ProductView, ProductsView, BasketView, ConfirmOrderView, GetOrders, GetOrderDetail, GetOrUpdateStatus

urlpatterns = [
    path('partner/update/', ImportProductsView.as_view()),
    path('partner/status/<int:pk>/', GetOrUpdateStatus.as_view()),
    path('shops/', ShopsView.as_view()),
    path('shops/<int:pk>/', ShopItemsView.as_view(), name='shop-detail'),
    path('categories/', CategoriesView.as_view()),
    path('categories/<int:pk>/', CategoryItemsView.as_view(), name='category-products'),
    path('products/', ProductsView.as_view()),
    path('products/<int:pk>/', ProductView.as_view(), name='product-detail'),
    path('basket/', BasketView.as_view()),
    path('basket/confirm/', ConfirmOrderView.as_view()),
    path('orders/', GetOrders.as_view()),
    path('orders/<int:pk>/', GetOrderDetail.as_view())
]
