import os
import qrcode
import random
import string
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User, Group
from djmoney.models.fields import MoneyField
from django.utils.text import slugify
from djmoney.money import Money


def rand_slug():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20))


def unmask_money(value, currency):
    if value == "":
        return 0.0
    elif currency == 'BRL':
        value = value.replace('R$ ', '')
        value = value.replace('BRL ', '')
        value = value.replace('.', '')
        value = value.replace(',', '.')
    elif currency == 'USD':
        value = value.replace('$ ', '')
        value = value.replace('USD ', '')
        value = value.replace(',', '')
    else:
        value = value.replace('€ ', '')
        value = value.replace('EUR ', '')
        value = value.replace('.', '')
        value = value.replace(',', '.')

    return float(value)


def custom_upload_path_projects(instance, filename):
    client = instance.project.client.replace(" ", "_")
    project_name = instance.project.title.replace(" ", "_")
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    return f'uploads/projects/{client}/{project_name}/{year}/{month}/{filename}'


def upload_path_bills(instance, filename):
    office = instance.office.name.replace(" ", "_") if instance.office else 'none'
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    return f'uploads/proofs/bills/{office}/{year}/{month}/{filename}'


def custom_upload_path_documents(instance, filename):
    collab_name = instance.user.get_full_name().replace(" ", "_")
    category = instance.category.replace(" ", "_")
    return f'uploads/documents/{collab_name}/{category}/{filename}'


class Equipments(models.Model):
    acquisition_date = models.DateField(default=datetime.now)
    name = models.CharField(max_length=100, default='Untitled')
    series = models.CharField(max_length=100, default='N/A')
    supplier = models.CharField(max_length=100, default='')
    price = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', default=0)
    description = models.TextField(default='')
    qrcode = models.TextField(default='')
    custom_id = models.CharField(max_length=100, default='')

    def __str__(self):
        return self.name

    def generate_qrcode(self):
        info = (f'Name: {self.name}\n'
                f'Series: {self.series}\n'
                f'ID: {self.custom_id}\n'
                f'Acquisition: {self.acquisition_date.strftime("%d/%m/%Y")}')

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(info)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        img_name = f'{self.name}_{self.id}.png'

        image_dir = f'apps/static/assets/uploads/qrcodes/equipments/{self.acquisition_date.strftime("%Y")}/' \
                    f'{self.acquisition_date.strftime("%m")}/{self.name}/'

        os.makedirs(image_dir, exist_ok=True)

        image_path = os.path.join(image_dir, img_name)

        img.save(image_path)

        return image_path

    def generate_custom_id(self):
        return f'{self.acquisition_date.strftime("%Y%m")}{self.id:03d}'

    def save(self, *args, **kwargs):

        super().save()

        if self.series == '':
            self.series = 'N/A'

        if not self.qrcode or self.qrcode == '':
            self.qrcode = self.generate_qrcode()

        if not self.custom_id or self.custom_id == '':
            self.custom_id = self.generate_custom_id()

        super(Equipments, self).save(*args, **kwargs)


class Project(models.Model):
    working = models.BooleanField(default=True)
    title = models.CharField(max_length=100)
    client = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    client_area = models.CharField(max_length=100)
    start_date = models.DateField()
    deadline = models.DateField()
    about = models.TextField()
    budget = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', default=0)
    img = models.ImageField(upload_to=f'apps/static/assets/uploads/',
                            default='apps/static/assets/img/icons/custom/1x/placeholder.webp')
    completition = models.IntegerField(default=0)
    finished = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if kwargs.get('update_tasks'):
            total_tasks = self.tasks.count()
            completed_tasks = self.tasks.filter(completed=True).count()

            self.completition = int((completed_tasks / total_tasks) * 100)

        super().save()


class Profile(models.Model):
    slug = models.SlugField(max_length=100, default='')

    # Foreign Keys and Relationships
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    office = models.ForeignKey('Office', related_name="collaborators", on_delete=models.SET_NULL, null=True)

    # File Fields
    avatar = models.ImageField(upload_to='apps/static/assets/uploads/profile_pics',
                               default='apps/static/assets/img/icons/custom/1x/placeholder.webp')

    # Char Fields
    cpf = models.CharField(max_length=20, default='')
    street = models.CharField(max_length=150, default='')
    street_number = models.CharField(max_length=20, default='')
    city = models.CharField(max_length=100, default='')
    state = models.CharField(max_length=100, default='')
    country = models.CharField(max_length=100, default='')
    postal_code = models.CharField(max_length=20, default='')
    contract = models.CharField(max_length=100, default='')
    phone = models.CharField(max_length=20, default='')
    position = models.CharField(max_length=100, default='')

    # Integer Fields
    identification = models.IntegerField(default=0)

    # Date Fields
    aso = models.DateField(null=True, blank=True, default=None)
    admission = models.DateField(null=True, blank=True, default=None)
    birthday = models.DateField(null=True, blank=True, default=None)

    # Text Fields
    about = models.TextField(default='')

    # Boolean Fields
    first_access = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        if not self.slug and self.user.get_full_name() != '':
            self.slug = slugify(self.user.get_full_name() + '-' + str(self.user.id))
        elif self.slug != slugify(self.user.get_full_name() + '-' + str(self.user.id)) or kwargs.get('slug'):
            self.slug = slugify(self.user.get_full_name() + '-' + str(self.user.id))
        elif self.user.get_full_name() == '':
            self.slug = slugify(str(self.user.id))
        elif self.slug.endswith('none'):
            self.slug = self.slug.replace('none', str(self.user.id))
        else:
            pass

        super().save()


class UploadedFile(models.Model):
    project = models.ForeignKey(Project, related_name='uploaded_files', on_delete=models.SET_NULL, null=True)
    client = models.ForeignKey('Client', related_name='uploaded_files', on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to=custom_upload_path_projects)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, related_name='uploaded_files', on_delete=models.SET_NULL, default=1,
                                    null=True)
    category = models.CharField(max_length=100, default='others')
    description = models.TextField(default='')
    value = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', default=0)

    def __str__(self):
        return self.file.name

    def fileExtension(self):
        return self.file.name.split('.')[-1]

    def fileCategory(self):
        correlation = {
            '3d-models': ['rvt', 'stp', 'igs', 'ifc', 'sat', 'dxf', 'dwg', 'prt', 'catpart', 'catproduct', 'cgr', 'obj',
                          'stl', 'jt', 'dgn', 'fbx', 'sldprt', 'sldasm', 'x_t', 'x_b'],
            'clouds': ['rcp', 'rcs', 'pod', 'fls', 'las', 'e57'],
            'scripts': ['py', 'html', 'css', 'js', 'cs', 'c', 'cpp', 'json', 'xml', 'kt', 'kts'],
            'executable': ['exe', 'msi', 'bat', 'sh', 'apk'],
            'folders': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'iso', 'dmg', 'pkg', 'deb', 'rpm'],
            'unity': ['unitypackage', 'assets', 'prefab', 'mat', 'unity', 'unity3d', 'unitypackage', 'asset', 'meta',
                      'ress'],
            'database': ['db', 'sql', 'sqlite', 'sqlite3', 'db3', 'sqlite2', 'sqlite3-shm', 'sqlite3-wal'],
            'office': ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp', 'rtf', 'txt', 'pdf', 'csv',
                       'md'],
            'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'ico', 'tif', 'tiff', 'psd', 'ai', 'eps', 'ps',
                       'indd', 'raw', 'webp'],
            'video': ['mp4', 'avi', 'mov', 'wmv', 'flv', '3gp', 'webm', 'mkv', 'vob', 'ogv', 'ogg', 'drc', 'gifv',
                      'mng', 'qt', 'yuv', 'rm', 'rmvb', 'asf', 'amv', 'm4p', 'm4v', 'mpg', 'mp2', 'mpeg', 'mpe',
                      'mpv', 'm2v', 'svi', '3g2', 'mxf', 'roq', 'nsv', 'f4v', 'f4p', 'f4a', 'f4b'],
        }

        for key, value in correlation.items():
            if self.fileExtension() in value:
                return key

    def save(self, *args, **kwargs):

        super().save()

        project = self.project

        if project:
            total_budget = project.uploaded_files.aggregate(models.Sum('value'))['value__sum'] or Money(0, 'USD')
            project.budget = total_budget
            project.save()
            client = self.project.client

        super().save()


class Task(models.Model):
    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    deadline = models.DateField()
    priority = models.IntegerField(default=0)

    completed = models.BooleanField(default=False)
    completed_at = models.DateField(null=True, blank=True)
    completed_by = models.ForeignKey(User, related_name='completed_tasks', on_delete=models.SET_NULL, null=True,
                                     blank=True)

    created_at = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='created_tasks', on_delete=models.SET_NULL, default=1, null=True)

    owner = models.ForeignKey(User, related_name='user_tasks', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *arg, **kwargs):
        super().save()

        project = self.project
        total_tasks = project.tasks.count()
        completed_tasks = project.tasks.filter(completed=True).count()

        project.completition = int((completed_tasks / total_tasks) * 100)
        project.save()


class Office(models.Model):
    avatar = models.ImageField(upload_to='uploads/offices/avatar',
                               default='apps/static/assets/img/icons/custom/1x/placeholder.webp')
    name = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.TextField(default='')


class Client(models.Model):
    avatar = models.ImageField(upload_to='uploads/clients/avatar',
                               default='apps/static/assets/img/icons/custom/1x/placeholder.webp')
    name = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=100)
    email = models.CharField(max_length=100, default='')
    phone = models.CharField(max_length=14, default='')
    area = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    description = models.TextField()


# Adicionar currency
class Bill(models.Model):
    # Foreign Keys and Relationships
    project = models.ForeignKey(Project, related_name='bills', on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Client, related_name='bills', on_delete=models.SET_NULL, null=True, blank=True)
    office = models.ForeignKey(Office, related_name='bills', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='created_bills', on_delete=models.SET_NULL, null=True)

    # Char Fields
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=100, default='others')
    subcategory = models.CharField(max_length=100, null=True, blank=True)
    method = models.CharField(max_length=100, default='others')

    # Date Fields
    created_at = models.DateField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    paid_at = models.DateField(blank=True, null=True)

    # Text Fields
    description = models.TextField()

    # Money Fields
    installments_value = MoneyField(max_digits=14, decimal_places=2, default_currency='BRL', default=0)
    fees = MoneyField(max_digits=14, decimal_places=2, default_currency='BRL', default=0)
    discount = MoneyField(max_digits=14, decimal_places=2, default_currency='BRL', default=0)
    total = MoneyField(max_digits=14, decimal_places=2, default_currency='BRL', default=0)

    # Boolean Fields
    paid = models.BooleanField(default=False)
    late = models.BooleanField(default=False)
    income = models.BooleanField(default=False)

    # Integer Fields
    installments = models.IntegerField(default=0)

    # File Fields
    proof = models.FileField(upload_to=upload_path_bills, null=True, blank=True)

    def __str__(self):
        return self.title

    def select_subcategory(self):
        correlation = {
            'Bank': ['Bank fees'],
            'Financial': ['Loan interest', 'Fines for late payment', 'IOF/IR on applications'],
            'Maintenance': ['Equipments', 'Cleaning and hygiene', 'Repairs and work', 'Utensils'],
            'Public fees': ['IPTU', 'State tax', 'Municipal tax', 'City hall fees', "Employers' union",
                            'Business license'],
            'Staff': ['Salary', 'Union contribution', 'Confraternization', 'Bonus', 'Salary', 'FGTS', 'INSS',
                      'Uniforms', 'Transportation voucher', 'Individual protection equipment', 'Training',
                      'Occupational medicine', 'Food'],
        }

        for key, value in correlation.items():
            if self.subcategory in value:
                return key

        return 'Others'

    def save(self, *args, **kwargs):

        if kwargs.get('paid'):
            self.paid_at = datetime.now()
            self.late = False
        elif not kwargs.get('paid'):
            self.paid_at = None

        if self.due_date and datetime.strptime(str(self.due_date),
                                               '%Y-%m-%d').date() < datetime.now().date() and not self.paid:
            self.late = True

        if not self.income and self.subcategory is None:
            self.subcategory = self.select_subcategory()

        super().save()


class Document(models.Model):
    user = models.ForeignKey(User, related_name='documents', on_delete=models.CASCADE, null=True, default=None)
    category = models.CharField(max_length=50)
    description = models.TextField()
    expiration = models.DateField()
    expired = models.BooleanField(default=False)
    file = models.FileField(upload_to=custom_upload_path_documents, blank=True, null=True)
    name = models.CharField(max_length=100)
    uploaded_at = models.DateField(auto_now_add=True, null=True)
    uploaded_by = models.ForeignKey(User, related_name='uploaded_documents', on_delete=models.SET_NULL, null=True,
                                    default=None)

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        if str(self.name).lower() == 'aso':
            user_profile = Profile.objects.get(user=self.user)
            aso_files = sorted(Document.objects.filter(user=self.user, name__iexact='aso'), key=lambda x: x.expiration)
            last_aso = aso_files[-1] if aso_files else None
            user_profile.aso = last_aso.expiration if aso_files else None
            user_profile.save()

        if str(self.name).lower() == 'asos':
            user_profile = Profile.objects.get(user=self.user)
            aso_files = sorted(Document.objects.filter(user=self.user, name__iexact='asos'), key=lambda x: x.expiration)
            last_aso = aso_files[-1] if aso_files else None
            user_profile.aso = last_aso.expiration if aso_files else None
            user_profile.save()

    def save(self, *args, **kwargs):
        super().save()

        if str(self.name).lower() == 'aso':
            try:
                expiration_date = datetime.strptime(self.expiration, '%Y-%m-%d').date()
            except TypeError:
                expiration_date = self.expiration

            user_profile = Profile.objects.get(user=self.user)
            user_profile.aso = expiration_date if user_profile.aso is None or user_profile.aso < expiration_date else user_profile.aso
            user_profile.save()
