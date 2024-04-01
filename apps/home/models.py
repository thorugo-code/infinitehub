import qrcode
import random
import string
import requests
from io import BytesIO
from django.db import models
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from django.core.files import File
from djmoney.money import Money
from django.utils.text import slugify
from djmoney.models.fields import MoneyField
from django.contrib.auth.models import User, Group
from apps.home.storage_backends import PublicMediaStorage
from apps.authentication.models import AuthEmail


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
    proj_inst = instance.project
    client = proj_inst.client.name.replace(" ", "_") if proj_inst.client else proj_inst.client_str.replace(" ", "_")
    project_name = proj_inst.title.replace(" ", "_")
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    return f'projects/{client}/{project_name}/{year}/{month}/{filename}'


def upload_path_bills(instance, filename):
    office = instance.office.name.replace(" ", "_") if instance.office else 'none'
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    return f'proofs/bills/{office}/{year}/{month}/{filename}'


def custom_upload_path_documents(instance, filename):
    if instance.user:
        collab_name = instance.user.get_full_name().replace(" ", "_")
        category = instance.category.replace(" ", "_")
        return f'documents/{collab_name}/{category}/{filename}'
    elif instance.client:
        client_name = instance.client.name.replace(" ", "_")
        category = instance.category.replace(" ", "_")
        return f'documents/{client_name}/{category}/{filename}'
    else:
        category = instance.category.replace(" ", "_")
        return f'documents/others/{category}/{filename}'


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
    # Foreign Keys and Relationships
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

    # Date Fields
    start_date = models.DateField()
    deadline = models.DateField()

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

        super().save()


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

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        super().save()

        if not self.slug and self.user.get_full_name() != '':
            self.slug = slugify(self.user.get_full_name() + '-' + str(self.user.id))
            self.save()
        elif self.slug != slugify(self.user.get_full_name() + '-' + str(self.user.id)) or kwargs.get('slug'):
            self.slug = slugify(self.user.get_full_name() + '-' + str(self.user.id))
            self.save()
        elif self.user.get_full_name() == '':
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
    file = models.FileField(upload_to=custom_upload_path_projects, max_length=500)
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
                               default='placeholder.webp')
    name = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.TextField(default='')


class Client(models.Model):
    slug = models.SlugField(max_length=100, default='')
    avatar = models.ImageField(upload_to='uploads/clients/avatar',
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


# Add currency
class Bill(models.Model):
    # Foreign Keys and Relationships
    client = models.ForeignKey(Client, related_name='bills', on_delete=models.SET_NULL, null=True, blank=True)
    office = models.ForeignKey(Office, related_name='bills', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='created_bills', on_delete=models.SET_NULL, null=True)

    # Char Fields
    title = models.CharField(max_length=100)
    method = models.CharField(max_length=100, null=True, blank=True)
    origin = models.CharField(max_length=100, null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    # payer = models.CharField(max_length=100, null=True, blank=True) # ???

    # Date Fields
    created_at = models.DateField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    paid_at = models.DateField(blank=True, null=True)

    # Money Fields
    total = MoneyField(max_digits=14, decimal_places=2, default_currency='BRL', default=0)

    # Boolean Fields
    reconciled = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    late = models.BooleanField(default=False)

    # Integer Fields
    installments_number = models.IntegerField(default=0)
    # code = models.IntegerField(default=0) # ???

    # File Fields
    proof = models.FileField(upload_to=upload_path_bills, null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.due_date:
            check_late = datetime.strptime(str(self.due_date), '%Y-%m-%d').date() < datetime.now().date()
            if check_late and not self.paid:
                self.late = True

        super().save()


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

    def __str__(self):
        return f'[{self.partial_id}/{self.bill.installments}] {self.bill.title} - {self.due_date}'

    def save(self, *args, **kwargs):
        super().save()


class Document(models.Model):
    # Foreign Keys and Relationships
    user = models.ForeignKey(User, related_name='documents', on_delete=models.CASCADE, null=True, default=None)
    client = models.ForeignKey(Client, related_name='documents', on_delete=models.CASCADE, null=True, default=None)
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
        super().delete(*args, **kwargs)

        if self.category == 'ASO':
            user_profile = Profile.objects.get(user=self.user)
            aso_files = sorted(Document.objects.filter(user=self.user, name__iexact='aso'), key=lambda x: x.expiration)
            last_aso = aso_files[-1] if aso_files else None
            user_profile.aso = last_aso.expiration if aso_files else None
            user_profile.save()

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
