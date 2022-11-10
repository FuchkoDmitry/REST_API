

from django.contrib.auth import authenticate
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework.authtoken.models import Token

from users.models import User, ConfirmEmailToken, UserInfo


class UserContactsViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserInfo
        fields = ('id', 'city', 'street', 'house', 'apartment', 'phone')


class UserRegisterSerializer(serializers.ModelSerializer):

    password2 = serializers.CharField(write_only=True, label='Повторите пароль', required=True)
    message = serializers.CharField(max_length=100, read_only=True)
    contacts = UserContactsViewSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'password',
            'password2', 'first_name', 'last_name',
            'company', 'position', 'role', 'message',
            'contacts'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'write_only': True},
            'last_name': {'write_only': True},
            'company': {'write_only': True},
            'position': {'write_only': True},
            'role': {'write_only': True}
        }
        read_only_fields = ('id',)

    def validate(self, attrs):
        password = attrs['password']
        password2 = attrs.pop('password2', '')
        if password != password2:
            raise serializers.ValidationError(
                {'password': "Пароли не совпадают"}
            )
        try:
            validate_password(password)
        except Exception as er:
            raise serializers.ValidationError(
                {'password': er}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        contacts = validated_data.pop('contacts', {})

        user = User(is_active=False, **validated_data)
        user.set_password(password)
        user.save()
        UserInfo.objects.create(user=user, **contacts)
        return user


class UserLoginSerializer(serializers.Serializer):
    token = serializers.CharField(read_only=True)
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=128, write_only=True)
    email = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs['username']
        password = attrs['password']
        user = authenticate(username=email, password=password)
        if user is None:
            raise serializers.ValidationError(
                {"error": "Некорректные имя пользователя и/или пароль"}
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {"error": "Учетная запись не активна. Пожалуйста, подтвердите учетную запись."}
            )
        return user


class ResetPasswordConfirmSerializer(serializers.Serializer): # noqa
    password = serializers.CharField(max_length=128, write_only=True, required=True)
    password2 = serializers.CharField(max_length=128, write_only=True, required=True, label='Повторите пароль')
    token = serializers.CharField(write_only=True, required=True)
    email = serializers.CharField(required=True)

    def validate(self, attrs):
        token = ConfirmEmailToken.objects.filter(
            token=attrs['token'],
            user__email=attrs['email']
        ).first()
        if token is None:
            raise serializers.ValidationError(
                {'error': 'Некорректные токен и/или email'}
            )

        password = attrs['password']
        password2 = attrs.pop('password2')
        if password != password2:
            raise serializers.ValidationError(
                {'password': 'Пароли не совпадают.'}
            )
        try:
            validate_password(password)
        except Exception as er:
            raise serializers.ValidationError(
                {'password': er}
            )
        token.delete()
        return attrs


class UserProfileViewSerializer(serializers.ModelSerializer):
    contacts = UserContactsViewSerializer(required=False, read_only=True, many=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'company', 'position', 'role', 'password', 'contacts')
        extra_kwargs = {
            'password': {'write_only': True}}

    def validate(self, attrs):
        password = attrs.get('password', False)
        if password:
            try:
                validate_password(password)
            except Exception as er:
                raise serializers.ValidationError(
                    {'password': er}
                )
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop('password', False)
        contacts = validated_data.pop('contacts', False)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
            token = Token.objects.get(user=instance)
            token.delete()
        if contacts:
            UserInfo.objects.update_or_create(user=instance, defaults=contacts)
        return instance


