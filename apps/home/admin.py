from django.contrib import admin
from .models import *


class OfficeAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'cnpj')


class MeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'start', 'url')


class UploadFileAdmin(admin.ModelAdmin):
    list_display = ('custom_name', 'file', 'uploaded_at')


admin.site.register(Equipments)
admin.site.register(Project)
admin.site.register(Profile)
admin.site.register(UploadedFile)
admin.site.register(Task)
admin.site.register(SubTask)
admin.site.register(Office, OfficeAdmin)
admin.site.register(Client)
admin.site.register(Branch)
admin.site.register(Bill)
admin.site.register(BillInstallment)
admin.site.register(Document)
admin.site.register(Link)
admin.site.register(Meeting, MeetingAdmin)
admin.site.register(BankAccount)
admin.site.register(BillProof)
