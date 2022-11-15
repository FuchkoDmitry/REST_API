from django.urls import path
from rest_framework.routers import DefaultRouter

from shop.views import (
    ImportProductsView, ProductView, ProductsView, BasketView,
    ConfirmOrderView, GetOrders, GetOrderDetail, GetOrUpdateStatus,
    GetPartnerOrders, CategoriesViewSet, ShopsViewSet
)


router = DefaultRouter()
router.register('categories', CategoriesViewSet, basename='categories')
router.register('shops', ShopsViewSet, basename='shops')

urlpatterns = [
    path('partner/update/', ImportProductsView.as_view()),
    path('partner/status/<int:pk>/', GetOrUpdateStatus.as_view(), name='partner-details'),
    path('partner/orders/', GetPartnerOrders.as_view()),
    path('products/', ProductsView.as_view(), name='products-list'),
    path('products/<int:pk>/', ProductView.as_view(), name='product-detail'),
    path('basket/', BasketView.as_view()),
    path('basket/confirm/', ConfirmOrderView.as_view()),
    path('orders/', GetOrders.as_view()),
    path('orders/<int:pk>/', GetOrderDetail.as_view())
] + router.urls
