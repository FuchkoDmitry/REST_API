
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import MethodNotAllowed
from drf_yasg.utils import swagger_auto_schema
from users.models import User, ConfirmEmailToken, UserInfo
from users.permissions import IsOwner, NotSocial
from users.serializers import (
    UserRegisterSerializer, UserLoginSerializer,
    ResetPasswordConfirmSerializer, UserProfileViewSerializer,
    UserContactsViewSerializer
)
from users.tasks import (
    user_register_email_task, account_confirmed_email_task,
    reset_password_email_task, reset_password_confirmed_email_task
)


class RegisterUserView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer

    def post(self, request, *args, **kwargs):
        """
        Сохраняем нового пользователя и отправляем email
        с подтверждением регистрации.
        """
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            data = {
                'message': "Вы успешно зарегистрировались. Инструкция по "
                           "подтверждению учетной записи отправлена вам на почту."
            }
            data.update(serializer.validated_data)
            user_register_email_task.delay(user.id)
            return Response(data,
                            status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class ConfirmAccountView(APIView):

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "email": openapi.Schema(type=openapi.FORMAT_EMAIL, description='user email'),
            "token": openapi.Schema(type=openapi.TYPE_STRING, description="token from email")
        },
        required=['email', 'token']
    ), responses={200: "Вы подтвердили учетную запись.",
                  400: "Вы указали некорректные данные."})
    def post(self, request):
        """
        Подтверждение аккаунта пользователя, активация профиля
        и отправка email в случае успеха
        """
        if {'email', 'token'}.issubset(request.data):
            token = ConfirmEmailToken.objects.filter(
                user__email=request.data['email'],
                token=request.data['token']
            ).first()
            if token is None:
                return JsonResponse({"error": "Вы указали некорректные данные."},
                                    status=status.HTTP_400_BAD_REQUEST)
            token.user.is_active = True
            token.user.save()
            account_confirmed_email_task.delay(request.data['email'])
            token.delete()
            return JsonResponse({"success": "Вы подтвердили учетную запись."},
                                status=status.HTTP_200_OK)
        return JsonResponse({"error": "Необходимо указать email и токен."},
                            status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Аутентификация пользователя в сервисе и получение
    им токена для выполнения запросов к API
    """
    serializer_class = UserLoginSerializer

    @swagger_auto_schema(request_body=UserLoginSerializer, responses={200: UserLoginSerializer()})
    def post(self, request):

        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token, _ = Token.objects.get_or_create(user=user)
            return JsonResponse({'username': user.username,
                                 'email': user.email,
                                 'token': token.key,
                                 'message': 'Вы успешно вошли. Используйте ваш токен для запросов'},
                                status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated, NotSocial]

    @swagger_auto_schema(responses={200: "Вы успешно вышли из системы"},
                         operation_description='Недоступно для авторизованных через соц сети')
    def post(self, request):
        user = request.user
        user_token = Token.objects.get(user=user)
        user_token.delete()

        return Response({'status': f'{user}, Вы успешно вышли из системы'},
                        status=status.HTTP_200_OK)


class ResetPasswordView(APIView):

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.FORMAT_EMAIL)
        },
        required=['email']
    ), responses={
        200: 'Вам на почту отправлено письмо с инструцией по смене пароля',
        400: 'Пользователя с данным email не существует'
        }
    )
    def post(self, request):
        email = request.data.get('email')
        if email is None:
            return Response({'email': 'email is required field'},
                            status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email=email).first()
        if user is None:
            return Response({'email': 'Пользователя с данным email не существует'},
                            status=status.HTTP_400_BAD_REQUEST)
        reset_password_email_task.delay(user.id)
        return Response(
            {'message': f'{user}, Вам на почту отправлено письмо с инструцией по смене пароля'},
            status=status.HTTP_200_OK
        )


class ResetPasswordConfirmView(APIView):
    '''
    Класс для смены пароля. При успешной смене пароля
    токен пользователя удаляется и необходимо снова
    выполнить вход с обновленными учетными данными.
    '''

    serializer_class = ResetPasswordConfirmSerializer

    @swagger_auto_schema(
        request_body=ResetPasswordConfirmSerializer,
        responses={200: "Пароль успешно обновлен",
                   400: "Некорректные токен и/или email // Пароли не совпадают."}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(email=serializer.validated_data['email'])
            user.set_password(serializer.validated_data['password'])
            user.save()
            reset_password_confirmed_email_task.delay(user.id)
            token = Token.objects.filter(user=user).first()
            if token:
                token.delete()
            return Response({'status': f'{user}, Пароль успешно обновлен'},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    '''
    Класс для просмотра и изменения профиля пользователя.
    При изменении пароля токен удаляется и пользователю
    необходимо выполнить вход с новым паролем.
    '''
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = UserProfileViewSerializer

    @swagger_auto_schema(
        operation_description='Просмотр профиля пользователя',
        responses={200: openapi.Response(description='Профиль пользователя',
                                         schema=UserProfileViewSerializer(read_only=True)
                                         )
                   }
    )
    def get(self, request):
        user = request.user
        serializer = self.serializer_class(instance=user)
        return Response(serializer.data)

    @swagger_auto_schema(operation_description='Изменить данные профиля пользователя',
                         request_body=UserProfileViewSerializer(partial=True))
    def patch(self, request):
        serializer = self.serializer_class(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_description='Создать новые контакты'))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_description='Получить контакты по id'))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_description='обновить(полностью) контакты'))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_description='обновить(частично) контакты'))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_description='удалить контакты по id'))
class UserContactsViewSet(ModelViewSet):
    """
    Создать, получить, изменить(частично или полностью)
    и удалить контакты пользователя.
    """
    queryset = UserInfo.objects.all()
    serializer_class = UserContactsViewSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(auto_schema=None)
    def list(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)
