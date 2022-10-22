from django.contrib import admin

# Register your models here.
from users.models import User, ConfirmEmailToken, UserInfo


class UserInfoInline(admin.TabularInline):
    model = UserInfo
    extra = 1
    readonly_fields = ["user", "city", "street", "house", "apartment", "phone"]




@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'username']
    list_display_links = ['email']
    inlines = [UserInfoInline]
    save_on_top = True


@admin.register(UserInfo)
class UserInfo(admin.ModelAdmin):
    list_display = ["id", "user", "city", "street", "house", "apartment", "phone"]
    # readonly_fields = ["id", "user", "city", "street", "house", "apartment", "phone"]
