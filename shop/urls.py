from django.urls import path

from shop.views import ImportProductsView

urlpatterns = [
    path('update/', ImportProductsView.as_view()),
]
