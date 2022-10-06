# from pprint import pprint

# from django.core.validators import URLValidator
from django.forms import model_to_dict
from requests import get
import yaml
from rest_framework import status
# from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from yaml.loader import SafeLoader

from shop.models import Shop
from shop.permissions import IsShop
from shop.serializers import URLSerializer

# url = 'https://raw.githubusercontent.com/netology-code/pd-diplom/master/data/shop1.yaml'

# f = get(url).content
# data = yaml.load(f, Loader=SafeLoader)
# pprint(data)


# with open('./data/shop1.yaml') as f:
#     data = yaml.load(f, Loader=SafeLoader)
    # pprint(data)


class ImportProductsView(APIView):
    '''
    Класс для импорта товаров магазином
    '''

    permission_classes = (IsAuthenticated, IsShop)
    serializer_class = URLSerializer

    def post(self, request):
        serializer = URLSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        url = serializer.validated_data.get('url')
        stream = get(url).content
        data = yaml.load(stream, Loader=SafeLoader)
        # тестирую
        # with open('./data/shop1.yaml') as f:
        #     data = yaml.load(f, Loader=SafeLoader)
        #     shop_data = data['shop']
        #     shop = Shop.objects.create(user=request.user, **shop_data)
        shop_data = data['shop']
        shop = Shop.objects.get_or_create(user=request.user, **shop_data)
        return Response({'status': model_to_dict(shop)}, status=status.HTTP_200_OK)
