from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter(name='file_extension_icon')
@stringfilter
def file_extension_icon(value):
    extensions_to_icons = {
        'rvt': 'rvt.png',
        'stp': 'stp.png',
        'igs': 'igs.png',
        'ifc': 'ifc.png',
        'sat': 'sat.png',
        'dxf': 'dxf.png',
        'dwg': 'dwg.png',
        'prt': 'prt.png',
        'catpart': 'catpart.png',
        'catproduct': 'catproduct.png',
        'cgr': 'cgr.png',
        'obj': 'obj.png',
        'stl': 'stl.png',
        'jt': 'jt.png',
        'dgn': 'dgn.png',
        'fbx': 'fbx.png',
        'sldprt': 'sldprt.png',
        'sldasm': 'sldasm.png',
        'rcp': 'rcp.png',
        'rcs': 'rcs.png',
        'pod': 'pod.png',
        'fls': 'fls.png',
        'las': 'las.png',
        'e57': 'e57.png',
        'py': 'py.png',
        'html': 'html.png',
        'css': 'css.png',
        'js': 'js.png',
        'cs': 'cs.png',
        'c': 'c.png',
        'cpp': 'cpp.png',
        'json': 'json.png',
        'xml': 'xml.png',
        'kt': 'kt.png',
        'kts': 'kts.png',
        'exe': 'exe.png',
        'zip': 'zip.png',
        'rar': 'rar.png',
        'assets': 'assets.png',
        'asset': 'assets.png',
        'ress': 'ress.png',
        'sqlite3': 'sqlite3.png',
        'xlsx': 'xlsx.png',
        'docx': 'docx.png',
        'pptx': 'pptx.png',
        'pdf': 'pdf.png',
        'ai': 'ai.png',
        'jpg': 'jpg.png',
        'jpeg': 'jpeg.png',
        'png': 'png.png',
        'webp': 'webp.png',
        'mp4': 'mp4.png',
        'txt': 'txt.png',
        'gif': 'gif.png',
        'ico': 'ico.png',
        'avi': 'avi.png',
        'mkv': 'mkv.png',
        'wmv': 'wmv.png',
        'x_t': 'x_t.png',
        'x_b': 'x_b.png',
        'apk': 'apk.png',
    }
    extension = value.split('.')[-1].lower()
    return extensions_to_icons.get(extension, 'default.png')


@register.filter(name='file_name_only')
@stringfilter
def file_name_only(value):
    file_name = value.split('/')[-1]
    extension = file_name.split('.')[-1]
    file_name = file_name[:-len(extension) - 1]
    return file_name


@register.filter(name='file_name_only_with_extension')
@stringfilter
def file_name_only_with_extension(value):
    return value.split('/')[-1]
