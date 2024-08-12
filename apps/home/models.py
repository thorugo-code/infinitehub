import json
import qrcode
import random
import string
import requests
from io import BytesIO
from django.db import models
from bs4 import BeautifulSoup
from datetime import datetime
from djmoney.money import Money
from urllib.parse import urljoin
from django.core.files import File
from django.utils.text import slugify
from djmoney.models.fields import MoneyField
from apps.authentication.models import AuthEmail
from picklefield.fields import PickledObjectField
from django.contrib.auth.models import User, Group
from apps.home.storage_backends import PublicMediaStorage
from core.settings import CORE_DIR


BANKS = json.load(open(f'{CORE_DIR}/apps/static/assets/banks.json', 'r', encoding='utf-8'))
BANK_CODES = ((k, f'{k} ({v})') for k, v in BANKS.items())
BANK_NAMES = ((v, f'{v} ({k})') for k, v in BANKS.items())


def get_favicon(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            favicon_link = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')

            if favicon_link:
                favicon_url = favicon_link.get('href')
                absolute_favicon_url = urljoin(url, favicon_url)

                return absolute_favicon_url

    except Exception as e:
        print(f"Error fetching favicon: {e}")

    return None


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
    proj_inst = instance.project
    client = proj_inst.client.name.replace(" ", "_") if proj_inst.client else proj_inst.client_str.replace(" ", "_")
    project_name = proj_inst.title.replace(" ", "_")
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    return f'projects/{client}/{project_name}/{year}/{month}/{filename}'


def upload_path_bills(instance, filename):
    if isinstance(instance, Bill):
        obj = instance
    else:
        obj = instance.bill

    if obj.client:
        path = obj.client.name.replace(" ", "_")
    elif obj.office:
        path = obj.office.company_name.replace(" ", "_")
    else:
        path = 'others'

    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    return f'proofs/bills/{path}/{year}/{month}/{filename}'


def custom_upload_path_documents(instance, filename):
    if instance.user:
        collab_name = instance.user.get_full_name().replace(" ", "_")
        path = f'collaborators/{collab_name}'
    elif instance.client:
        client_name = instance.client.name.replace(" ", "_")
        path = f'clients/{client_name}'
    else:
        path = 'others'

    category = instance.category.replace(" ", "_") if instance.category else 'others'
    return f'documents/{path}/{category}/{filename}'


############################################################


class Equipments(models.Model):
    acquisition_date = models.DateField(default=datetime.now)
    name = models.CharField(max_length=100, default='Untitled')
    series = models.CharField(max_length=100, default='N/A')
    supplier = models.CharField(max_length=100, default='')
    price = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', default=0)
    description = models.TextField(default='')
    custom_id = models.CharField(max_length=100, default='')
    qrcode = models.ImageField(upload_to=f'qrcodes/equipments/{datetime.now().strftime("%Y")}/',
                               default='placeholder.webp')

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

        temp_file = BytesIO()
        img.save(temp_file, format='PNG')
        temp_file.seek(0)

        self.qrcode.save(f'{self.custom_id}_{self.name.lower()}.png', File(temp_file))

        self.save()

    def generate_custom_id(self):
        return f'{self.acquisition_date.strftime("%Y%m")}{self.id:03d}'

    def save(self, *args, **kwargs):

        super().save()

        if self.series == '':
            self.series = 'N/A'

        if not self.custom_id or self.custom_id == '':
            self.custom_id = self.generate_custom_id()

        if self.qrcode.name == 'placeholder.webp':
            self.generate_qrcode()

        super(Equipments, self).save(*args, **kwargs)


class Project(models.Model):
    slug = models.SlugField(max_length=100, default='')

    # Foreign Keys and Relationships
    manager = models.ForeignKey(User, related_name='managed_projects', on_delete=models.SET_NULL, null=True)
    client = models.ForeignKey('Client', related_name='projects', on_delete=models.SET_NULL, null=True)
    office = models.ForeignKey('Office', related_name='projects', on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(User, related_name='created_projects', on_delete=models.SET_NULL, null=True)
    assigned_to = models.ManyToManyField(User, related_name='assigned_projects')

    # Char and Text Fields
    title = models.CharField(max_length=100)
    client_str = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    about = models.TextField()

    # Boolean Fields
    working = models.BooleanField(default=True)
    finished = models.BooleanField(default=False)
    archive = models.BooleanField(default=False)

    # Date Fields
    start_date = models.DateField(blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)

    # Money Fields
    budget = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', default=0)

    # Image Fields
    img = models.ImageField(upload_to=f'project_pics',
                            default='placeholder.webp')

    # Integer Fields
    completition = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if kwargs.get('update_tasks'):
            total_tasks = self.tasks.count()
            completed_tasks = self.tasks.filter(completed=True).count()

            self.completition = int((completed_tasks / total_tasks) * 100)

        if self.client and 'placeholder' in self.img.name:
            if 'placeholder' not in self.client.avatar.name:
                self.img = self.client.avatar

        super().save()

        if not self.slug and self.title != '':
            self.slug = slugify(self.title + '-' + str(self.id))
            self.save()
        elif self.slug != slugify(self.title + '-' + str(self.id)) or kwargs.get('slug'):
            self.slug = slugify(self.title + '-' + str(self.id))
            self.save()
        elif self.title == '':
            self.slug = slugify(str(self.id))
            self.save()
        elif self.slug.endswith('none'):
            self.slug = self.slug.replace('none', str(self.id))
            self.save()
        else:
            pass


class Profile(models.Model):
    slug = models.SlugField(max_length=100, default='')

    # Foreign Keys and Relationships
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    office = models.ForeignKey('Office', related_name="collaborators", on_delete=models.SET_NULL, null=True)
    authentication = models.ForeignKey(AuthEmail, related_name='profile', on_delete=models.CASCADE, null=True)

    # File Fields
    avatar = models.ImageField(upload_to='profile_pics',
                               default='placeholder.webp',
                               storage=PublicMediaStorage())
    qrcode = models.ImageField(upload_to=f'qrcodes/members/',
                               storage=PublicMediaStorage(),
                               null=True, blank=True)

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
    identification = models.IntegerField(default=None, null=True, blank=True)

    # Date Fields
    aso = models.DateField(null=True, blank=True, default=None)
    admission = models.DateField(null=True, blank=True, default=None)
    birthday = models.DateField(null=True, blank=True, default=None)

    # Text Fields
    about = models.TextField(default='')

    # Boolean Fields
    first_access = models.BooleanField(default=True)

    # URL Fields
    website = models.URLField(null=True, blank=True)
    linkedin = models.URLField(null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    instagram = models.URLField(null=True, blank=True)
    twitter = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    def generate_qrcode(self):
        info = "https://hub.infinitefoundry.com/members/" + self.user.username.split('@')[0]

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(info)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        temp_file = BytesIO()
        img.save(temp_file, format='PNG')
        temp_file.seek(0)

        self.qrcode.save(f'{slugify(self.user.get_full_name())}_{self.id}.png', File(temp_file))

        self.save()

    def save(self, *args, **kwargs):
        super().save()

        if not self.slug and self.user.get_full_name() != '':
            self.slug = slugify(self.user.get_full_name() + '-' + str(self.user.id))
            self.save()
        elif self.slug != slugify(self.user.get_full_name() + '-' + str(self.user.id)) or kwargs.get('slug'):
            self.slug = slugify(self.user.get_full_name() + '-' + str(self.user.id))
            self.save()
        elif self.user.get_full_name() == '' and not self.slug:
            self.slug = slugify(str(self.user.id))
            self.save()
        elif self.slug.endswith('none'):
            self.slug = self.slug.replace('none', str(self.user.id))
            self.save()
        else:
            pass


class UploadedFile(models.Model):
    project = models.ForeignKey(Project, related_name='uploaded_files', on_delete=models.SET_NULL, null=True)
    client = models.ForeignKey('Client', related_name='uploaded_files', on_delete=models.SET_NULL, null=True)
    uploaded_by = models.ForeignKey(User, related_name='uploaded_files', on_delete=models.SET_NULL, default=1, null=True)

    file = models.FileField(upload_to=custom_upload_path_projects, max_length=500)

    custom_name = models.CharField(max_length=100, default='')
    category = models.CharField(max_length=100, default='others')

    uploaded_at = models.DateTimeField(auto_now_add=True)

    value = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', default=0)

    description = models.TextField(default='')

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
    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE, null=True, blank=True)
    meeting = models.ForeignKey('Meeting', related_name='tasks', on_delete=models.SET_NULL, null=True, blank=True)

    title = models.CharField(max_length=100)
    description = models.TextField()
    deadline = models.DateField(null=True, blank=True)
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

        if self.project:
            total_tasks = self.project.tasks.count()
            completed_tasks = self.project.tasks.filter(completed=True).count()
            self.project.completition = int((completed_tasks / total_tasks) * 100)
            self.project.save()


class SubTask(models.Model):
    task = models.ForeignKey(Task, related_name='subtasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    deadline = models.DateField(null=True, blank=True)
    priority = models.IntegerField(default=0)

    completed = models.BooleanField(default=False)
    completed_at = models.DateField(null=True, blank=True)
    completed_by = models.ForeignKey(User, related_name='completed_subtasks', on_delete=models.SET_NULL, null=True,
                                     blank=True)

    created_at = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='created_subtasks', on_delete=models.SET_NULL, default=1, null=True)

    owner = models.ForeignKey(User, related_name='user_subtasks', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *arg, **kwargs):
        super().save()

        if self.task:
            total_subtasks = self.task.subtasks.count()
            completed_subtasks = self.task.subtasks.filter(completed=True).count()
            self.task.completed = total_subtasks == completed_subtasks
            self.task.save()


class Office(models.Model):
    slug = models.SlugField(max_length=100, default='')

    avatar = models.ImageField(upload_to='uploads/offices/avatar',
                               default='placeholder.webp')

    company_name = models.CharField(max_length=100, default='')
    fantasy_name = models.CharField(max_length=100, default='')
    cnpj = models.CharField(max_length=100, default='')
    duns = models.CharField(max_length=9, default='')
    address = models.CharField(max_length=100, default='')
    municipal_inscription = models.CharField(max_length=20, default='')
    state_inscription = models.CharField(max_length=20, default='')

    pgr = models.DateField(null=True, blank=True, default=None)
    pcmso = models.DateField(null=True, blank=True, default=None)

    description = models.TextField(default='')

    def delete(self, *args, **kwargs):
        if 'placeholder.webp' not in self.avatar:
            self.avatar.delete(save=False)

        super(Office, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        super().save()

        if not self.slug and self.company_name != '':
            self.slug = slugify(self.company_name + '-' + str(self.id))
            self.save()
        elif self.slug != slugify(self.company_name + '-' + str(self.id)) or kwargs.get('slug'):
            self.slug = slugify(self.company_name + '-' + str(self.id))
            self.save()
        elif self.company_name == '':
            self.slug = slugify(str(self.id))
            self.save()
        elif self.slug.endswith('none'):
            self.slug = self.slug.replace('none', str(self.id))
            self.save()
        else:
            pass


class Client(models.Model):
    slug = models.SlugField(max_length=100, default='')
    avatar = models.ImageField(upload_to='client_pics',
                               default='placeholder.webp')

    # Foreign Keys and Relationships
    office = models.ForeignKey(Office, related_name='clients', on_delete=models.SET_NULL, null=True)

    # Char Fields
    name = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=100)
    xml_email = models.CharField(max_length=100, default='')
    contact_email = models.CharField(max_length=100, default='')
    phone = models.CharField(max_length=14, default='')
    area = models.CharField(max_length=100)
    location = models.CharField(max_length=200)

    # Text Fields
    description = models.TextField()

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if 'placeholder.webp' not in self.avatar.name:
            self.avatar.delete(save=False)

        super(Client, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        super().save()

        if not self.slug and self.name != '':
            self.slug = slugify(self.name + '-' + str(self.id))
            self.save()
        elif self.slug != slugify(self.name + '-' + str(self.id)) or kwargs.get('slug'):
            self.slug = slugify(self.name + '-' + str(self.id))
            self.save()
        elif self.name == '':
            self.slug = slugify(str(self.id))
            self.save()
        elif self.slug.endswith('none'):
            self.slug = self.slug.replace('none', str(self.id))
            self.save()
        else:
            pass


class Branch(models.Model):
    # Foreign Keys and Relationships
    client = models.ForeignKey(Client, related_name='branches', on_delete=models.CASCADE)

    # Char Fields
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.name} ({self.client.name})'


# TODO: Add currency
class Bill(models.Model):
    # Foreign Keys and Relationships
    client = models.ForeignKey(Client, related_name='bills', on_delete=models.SET_NULL, null=True, blank=True)
    payer = models.ForeignKey(Branch, related_name='bills', on_delete=models.SET_NULL, null=True)
    office = models.ForeignKey(Office, related_name='bills', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='created_bills', on_delete=models.SET_NULL, null=True)

    # Char Fields
    title = models.CharField(max_length=100)
    method = models.CharField(max_length=100, null=True, blank=True)
    origin = models.CharField(max_length=100, null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    code = models.CharField(max_length=100, null=True, blank=True)

    # Date Fields
    created_at = models.DateField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    issue_date = models.DateField(blank=True, null=True)
    paid_at = models.DateField(blank=True, null=True)

    # Money Fields
    total = MoneyField(max_digits=14, decimal_places=2, default_currency='BRL', default=0)
    partial = MoneyField(max_digits=14, decimal_places=2, default_currency='BRL', default=0)

    # Boolean Fields
    reconciled = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    late = models.BooleanField(default=False)

    # Integer Fields
    installments_number = models.IntegerField(default=0)
    installments_frequency = models.IntegerField(default=0)

    # File Fields
    proof = models.FileField(upload_to=upload_path_bills, null=True, blank=True)

    # URL Fields
    link = models.URLField(null=True, blank=True)

    # Text Fields
    payment_info = models.TextField(default='')

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        self.proof.delete(save=False)
        for proof in self.proofs.all():
            proof.delete()

        super(Bill, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.due_date:
            check_late = datetime.strptime(str(self.due_date), '%Y-%m-%d').date() < datetime.now().date()
            if check_late and not self.paid:
                self.late = True
        else:
            self.late = False

        super().save(*args, **kwargs)

        if self.paid:
            self.late = False
            if self.installments_number > 1:
                self.partial = sum([installment.value for installment in self.installments.filter(paid=True)])
            else:
                self.partial = self.total

        else:
            if int(self.installments_number) > 1 and self.installments.exists():
                self.partial = sum([installment.value for installment in self.installments.filter(paid=True)])
            else:
                self.partial = 0

        super().save(*args, **kwargs)


class BillInstallment(models.Model):
    # Foreign Keys and Relationships
    bill = models.ForeignKey(Bill, related_name='installments', on_delete=models.CASCADE)

    # Date Fields
    due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateField(null=True, blank=True)

    # Boolean Fields
    paid = models.BooleanField(default=False)

    # Numerical Fields
    partial_id = models.IntegerField(default=0)
    value = MoneyField(max_digits=14, decimal_places=2, default_currency='BRL', default=0)

    # Text Fields
    payment_info = models.TextField(default='')

    def __str__(self):
        return f'[{self.partial_id}/{self.bill.installments}] {self.bill.title} - {self.due_date}'

    def save(self, *args, **kwargs):
        super().save()
        self.bill.save()


class BillProof(models.Model):
    bill = models.ForeignKey(Bill, related_name='proofs', on_delete=models.CASCADE, null=True)
    file = models.FileField(upload_to=upload_path_bills, null=True, blank=True)

    def __str__(self):
        if self.bill:
            return f'{self.bill.title} - {self.file.name}'
        else:
            return self.file.name

    def delete(self, *args, **kwargs):
        self.file.delete(save=False)
        super(BillProof, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Document(models.Model):
    # Foreign Keys and Relationships
    user = models.ForeignKey(User, related_name='documents', on_delete=models.CASCADE, null=True, default=None)
    client = models.ForeignKey(Client, related_name='documents', on_delete=models.CASCADE, null=True, default=None)
    office = models.ForeignKey(Office, related_name='documents', on_delete=models.SET_NULL, null=True, default=None)
    branch = models.ForeignKey(Branch, related_name='documents', on_delete=models.SET_NULL, null=True, default=None)
    uploaded_by = models.ForeignKey(User, related_name='uploaded_documents', on_delete=models.SET_NULL, null=True,
                                    default=None)

    # Char Fields
    category = models.CharField(max_length=50)
    name = models.CharField(max_length=100)

    # Text Fields
    description = models.TextField()

    # Date Fields
    expiration = models.DateField(default=None, null=True, blank=True)
    uploaded_at = models.DateField(auto_now_add=True, null=True)

    # Boolean Fields
    expired = models.BooleanField(default=False)
    shared = models.BooleanField(default=False)

    # File Fields
    file = models.FileField(upload_to=custom_upload_path_documents, max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        self.file.delete(save=False)
        super(Document, self).delete(*args, **kwargs)

        if self.category == 'ASO':
            user_profile = Profile.objects.get(user=self.user)
            aso_files = sorted(Document.objects.filter(user=self.user, category__iexact='ASO'), key=lambda x: x.expiration)
            last_aso = aso_files[-1] if aso_files else None
            user_profile.aso = last_aso.expiration if aso_files else None
            user_profile.save()

        elif self.category == 'PGR':
            office = Office.objects.get(id=self.office.id)
            pgr_files = sorted(Document.objects.filter(office=self.office, category__iexact='PGR'), key=lambda x: x.expiration)
            last_pgr = pgr_files[-1] if pgr_files else None
            office.pgr = last_pgr.expiration if pgr_files else None
            office.save()

        elif self.category == 'PCMSO':
            office = Office.objects.get(id=self.office.id)
            pcmso_files = sorted(Document.objects.filter(office=self.office, category__iexact='PCMSO'), key=lambda x: x.expiration)
            last_pcmso = pcmso_files[-1] if pcmso_files else None
            office.pcmso = last_pcmso.expiration if pcmso_files else None
            office.save()

    def save(self, *args, **kwargs):
        super().save()

        if self.category == 'ASO' and self.expiration is not None:
            try:
                expiration_date = datetime.strptime(self.expiration, '%Y-%m-%d').date()
            except TypeError:
                expiration_date = self.expiration

            user_profile = Profile.objects.get(user=self.user)
            user_profile.aso = expiration_date if user_profile.aso is None or user_profile.aso < expiration_date else user_profile.aso
            user_profile.save()

        if self.category == 'PGR' and self.expiration is not None:
            try:
                expiration_date = datetime.strptime(self.expiration, '%Y-%m-%d').date()
            except TypeError:
                expiration_date = self.expiration

            office = Office.objects.get(id=self.office.id)
            office.pgr = expiration_date if office.pgr is None or office.pgr < expiration_date else office.pgr
            office.save()

        if self.category == 'PCMSO' and self.expiration is not None:
            try:
                expiration_date = datetime.strptime(self.expiration, '%Y-%m-%d').date()
            except TypeError:
                expiration_date = self.expiration

            office = Office.objects.get(id=self.office.id)
            office.pcmso = expiration_date if office.pcmso is None or office.pcmso < expiration_date else office.pcmso
            office.save()


class Link(models.Model):
    # Foreign Keys and Relationships
    project = models.ForeignKey(Project, related_name='links', on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Client, related_name='links', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='created_links', on_delete=models.SET_NULL, null=True)

    # URL
    path = models.URLField()

    # Date Fields
    created_at = models.DateField(auto_now_add=True)

    # Char and Text Fields
    title = models.CharField(max_length=100)
    icon = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.path

    def save(self, *args, **kwargs):
        super().save()

        # Correlation
        correlation = {
            'my.sharepoint.com': 'onedrive.svg',
            'onedrive': 'onedrive.svg',
            'drive.google.com': 'google-drive.svg',
            'youtube': 'youtube.svg',
            'github': 'github.svg',
        }

        if not self.icon:
            for key, value in correlation.items():
                if key in self.path:
                    self.icon = f'/static/assets/img/icons/common/{value}'
                    break

            if not self.icon:
                favicon = get_favicon(self.path)
                self.icon = favicon if favicon else 'https://img.icons8.com/ios/50/ios-application-placeholder.png'

            self.save()

        if not self.title:
            self.title = self.path.split('//')[-1]
            self.save()


class Meeting(models.Model):
    project = models.ForeignKey(Project, related_name='meetings', on_delete=models.SET_NULL, null=True)
    client = models.ForeignKey(Client, related_name='meetings', on_delete=models.SET_NULL, null=True)
    participants = models.ManyToManyField(User, related_name='meetings')
    owner = models.ForeignKey(User, related_name='owned_meetings', on_delete=models.SET_NULL, null=True)

    external_owner = models.CharField(max_length=100, default='')
    title = models.CharField(max_length=100)

    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)

    questions = PickledObjectField(default=list)
    topics = PickledObjectField(default=list)
    external_participants = PickledObjectField(default=list)
    invited_participants = PickledObjectField(default=list)

    summary = models.TextField(default='')

    url = models.URLField()


class BankAccount(models.Model):
    # Foreign Keys and Relationships
    user = models.ForeignKey(User, related_name='bank_accounts', on_delete=models.CASCADE, null=True, blank=True)
    office = models.ForeignKey(Office, related_name='bank_accounts', on_delete=models.CASCADE, null=True, blank=True)

    # Integer Fields
    bank_code = models.CharField(max_length=3, default='', choices=BANK_CODES)
    agency = models.CharField(max_length=4, default='')
    account = models.CharField(max_length=10, default='')

    # Char Fields
    bank_name = models.CharField(max_length=150, default='', choices=BANK_NAMES)
    pix = models.CharField(max_length=100, default='', null=True, blank=True)
    account_type = models.CharField(
        max_length=2,
        choices=(
            ('PF', 'Pessoa Física'),
            ('PJ', 'Pessoa Jurídica')
        ),
    )

    def __str__(self):
        return f'{self.bank_name} - {self.agency} - {self.account}'

    def save(self, *args, **kwargs):
        if not self.bank_name or self.bank_name != BANKS[self.bank_code]:
            self.bank_name = BANKS[self.bank_code]

        super().save(*args, **kwargs)
