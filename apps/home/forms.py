from django import forms
from .models import Category
from django.contrib.contenttypes.models import ContentType


class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        valid_content_types = ContentType.objects.filter(app_label='home').exclude(model='category')
        valid_content_types = valid_content_types.filter(model__in=[
            ct.model for ct in valid_content_types
            if ct.model_class() and hasattr(ct.model_class(), 'category')
        ])

        self.fields['model'].queryset = valid_content_types
        self.fields['model'].label_from_instance = lambda obj: obj.model_class()._meta.verbose_name.capitalize()

    class Meta:
        model = Category
        fields = '__all__'


