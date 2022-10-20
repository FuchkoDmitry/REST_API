from django.contrib import admin

# Register your models here.
from users.models import User, ConfirmEmailToken, UserInfo


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'email']


@admin.register(UserInfo)
class UserInfo(admin.ModelAdmin):
    list_display = ["id", "user", "city", "street", "house", "apartment", "phone"]
