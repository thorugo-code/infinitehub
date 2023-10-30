import os
import qrcode
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from djmoney.models.fields import MoneyField
from djmoney.money import Money


def custom_upload_path(instance, filename):
    client = instance.project.client.replace(" ", "_")
    project_name = instance.project.title.replace(" ", "_")
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    return f'uploads/projects/{client}/{project_name}/{year}/{month}/{filename}'


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

        # Specify the directory where you want to save the image
        image_dir = f'apps/static/assets/uploads/qrcodes/equipments/{self.acquisition_date.strftime("%Y")}/' \
                    f'{self.acquisition_date.strftime("%m")}/{self.name}/'

        # Create the directory if it doesn't exist
        os.makedirs(image_dir, exist_ok=True)

        # Specify the full path to save the image
        image_path = os.path.join(image_dir, img_name)

        # Save the QR code image to the specified path
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
    first_login = models.BooleanField(default=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    avatar = models.ImageField(upload_to='apps/static/assets/uploads/profile_pics',
                               default='apps/static/assets/img/icons/custom/1x/placeholder.webp')

    # birthday = models.DateField(null=True, blank=True)

    about = models.TextField(default='')

    address = models.CharField(max_length=150, default='')

    city = models.CharField(max_length=100, default='')
    state = models.CharField(max_length=100, default='')
    country = models.CharField(max_length=100, default='')
    postal_code = models.CharField(max_length=20, default='')

    # phone = models.CharField(max_length=20, default='')

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save()
        user = self.user
        user.save()


class UploadedFile(models.Model):

    project = models.ForeignKey(Project, related_name='uploaded_files', on_delete=models.CASCADE)
    file = models.FileField(upload_to=custom_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, related_name='uploaded_files', on_delete=models.CASCADE, default=1)
    category = models.CharField(max_length=100, default='others')
    description = models.TextField(default='')
    value = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', default=0)

    def __str__(self):
        return self.file.name

    def fileExtension(self):
        return self.file.name.split('.')[-1]

    def fileCategory(self):
        models_3d = ['rvt', 'stp', 'igs', 'ifc', 'sat', 'dxf', 'dwg', 'prt', 'catpart', 'catproduct', 'cgr', 'obj',
                     'stl', 'jt', 'dgn', 'fbx', 'sldprt', 'sldasm', 'x_t', 'x_b']

        clouds = ['rcp', 'rcs', 'pod', 'fls', 'las', 'e57']

        scripts = ['py', 'html', 'css', 'js', 'cs', 'c', 'cpp', 'json', 'xml', 'kt', 'kts']

        executable = ['exe', 'msi', 'bat', 'sh', 'apk']

        folders = ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'iso', 'dmg', 'pkg', 'deb', 'rpm']

        unity = ['unitypackage', 'assets', 'prefab', 'mat', 'unity', 'unity3d', 'unitypackage', 'asset', 'meta', 'ress']

        database = ['db', 'sql', 'sqlite', 'sqlite3', 'db3', 'sqlite2', 'sqlite3-shm', 'sqlite3-wal']

        office = ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp', 'rtf', 'txt', 'pdf', 'csv', 'md']

        images = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'ico', 'tif', 'tiff', 'psd', 'ai', 'eps', 'ps', 'indd',
                  'raw', 'webp']

        video = ['mp4', 'avi', 'mov', 'wmv', 'flv', '3gp', 'webm', 'mkv', 'vob', 'ogv', 'ogg', 'drc', 'gifv', 'mng',
                 'qt', 'yuv', 'rm', 'rmvb', 'asf', 'amv', 'm4p', 'm4v', 'mpg', 'mp2', 'mpeg', 'mpe', 'mpv', 'm2v',
                 'svi', '3g2', 'mxf', 'roq', 'nsv', 'f4v', 'f4p', 'f4a', 'f4b']

        if self.fileExtension() in models_3d:
            return '3d-models'
        elif self.fileExtension() in scripts:
            return 'scripts'
        elif self.fileExtension() in unity:
            return 'unity'
        elif self.fileExtension() in clouds:
            return 'clouds'
        elif self.fileExtension() in executable:
            return 'executable'
        elif self.fileExtension() in folders:
            return 'folders'
        elif self.fileExtension() in database:
            return 'database'
        elif self.fileExtension() in office:
            return 'office'
        elif self.fileExtension() in images:
            return 'images'
        elif self.fileExtension() in video:
            return 'video'
        else:
            return 'others'

    def save(self, *args, **kwargs):

        super().save()

        project = self.project
        total_budget = project.uploaded_files.aggregate(models.Sum('value'))['value__sum'] or Money(0, 'USD')

        project.budget = total_budget
        project.save()


class Task(models.Model):
    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    deadline = models.DateField()
    priority = models.IntegerField(default=0)

    completed = models.BooleanField(default=False)
    completed_at = models.DateField(null=True, blank=True)
    completed_by = models.ForeignKey(User, related_name='completed_tasks', on_delete=models.CASCADE, null=True,
                                     blank=True)

    created_at = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='created_tasks', on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.title

    def save(self, *arg, **kwargs):
        super().save()

        project = self.project
        total_tasks = project.tasks.count()
        completed_tasks = project.tasks.filter(completed=True).count()

        project.completition = int((completed_tasks / total_tasks) * 100)
        project.save()
