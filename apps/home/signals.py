import os
import boto3
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import BillProof
from .models import upload_path_bills


@receiver(post_save, sender=BillProof)
def move_file_to_final_location(sender, instance, created, **kwargs):
    if instance.bill and 'temp' in instance.file.name and not created:
        final_path = 'media/' + upload_path_bills(instance, os.path.basename(instance.file.name))

        s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        temp_path = 'media/' + instance.file.name

        s3.copy_object(
            Bucket=bucket_name,
            CopySource={'Bucket': bucket_name, 'Key': temp_path},
            Key=final_path
        )

        s3.delete_object(Bucket=bucket_name, Key=temp_path)

        instance.file.name = final_path
        instance.save()
