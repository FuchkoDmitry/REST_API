
from rest_framework import serializers


class URLSerializer(serializers.Serializer): # noqa
    url = serializers.URLField(write_only=True, required=True, label='URL адрес для импорта товаров')
