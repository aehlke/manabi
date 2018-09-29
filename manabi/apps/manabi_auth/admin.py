from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from impersonate.admin import UserAdminImpersonateMixin


class ImpersonatableUserAdmin(UserAdminImpersonateMixin, UserAdmin):
    open_new_window = True


admin.site.unregister(User)
admin.site.register(User, ImpersonatableUserAdmin)
