from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from editregions.admin.modeladmins import SupportsEditRegions


class UserAdmin(SupportsEditRegions, DjangoUserAdmin):
    filter_vertical = ('user_permissions', 'groups')
    pass

try:
    admin.site.unregister(User)
except NotRegistered:
    pass
admin.site.register(User, UserAdmin)
