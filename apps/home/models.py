
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from djmoney.models.fields import MoneyField
from djmoney.money import Money


class Project(models.Model):

    title = models.CharField(max_length=100)
    client = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    client_area = models.CharField(max_length=100)
    start_date = models.DateField()
    deadline = models.DateField()
    about = models.TextField()
    budget = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', default=0)
    img = models.ImageField(upload_to=f'apps/static/assets/uploads/', default='apps/static/assets/img/icons/custom/1x/placeholder.webp')


def custom_upload_path(instance, filename):
    client = instance.project.client.replace(" ", "_")
    project_name = instance.project.title.replace(" ", "_")
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    return f'uploads/projects/{client}/{project_name}/{year}/{month}/{filename}'


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
        else:
            return 'others'

    def save(self, *args, **kwargs):

        self.category = self.fileCategory()
        super().save()

        project = self.project
        total_budget = project.uploaded_files.aggregate(models.Sum('value'))['value__sum'] or Money(0, 'USD')

        project.budget = total_budget
        project.save()



