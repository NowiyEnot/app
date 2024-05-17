from django.contrib.admin import ModelAdmin,register,site

from django.contrib.auth.admin import UserAdmin

from main.models import MyUser, UserUUID, StudentGroup

# from main.models import Accaunt

# Register your models here.

@register(MyUser)
class AccauntmodelAdmin(ModelAdmin):
    list_display = ['email','first_name','last_name','course','group','can_create','is_active','is_staff','registration_date']



@register(UserUUID)
class MyUUIDAdmin(ModelAdmin):
    pass

@register(StudentGroup)
class MyGroupAdmin(ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

 