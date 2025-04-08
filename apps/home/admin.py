from django.contrib import admin
from .models import *
from .forms import *


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'cnpj')


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'start', 'url')


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('custom_name', lambda x: x.file.name.split('/')[-1], 'project', 'uploaded_at')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'model')
    form = CategoryForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "model":
            kwargs["queryset"] = ContentType.objects.filter(
                ~Q(model='category'),
                app_label='home'
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Equipments)
admin.site.register(Project)
admin.site.register(Profile)
admin.site.register(Task)
admin.site.register(SubTask)
admin.site.register(Bill)
admin.site.register(BillInstallment)
admin.site.register(Client)
admin.site.register(Branch)
admin.site.register(Document)
admin.site.register(Link)
admin.site.register(BankAccount)
admin.site.register(BillProof)
admin.site.register(SubCategory)
