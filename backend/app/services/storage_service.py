import boto3
from botocore.exceptions import ClientError
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION
        )
        self.bucket = settings.S3_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket)
                logger.info(f"S3 Bucket '{self.bucket}' created")
            except Exception as e:
                logger.error(f"Failed to create S3 bucket: {e}")

    def upload_file(self, file_path: str, object_name: str, content_type: str = "application/pdf") -> bool:
        """Загружает файл в S3"""
        try:
            self.s3_client.upload_file(
                file_path, 
                self.bucket, 
                object_name,
                ExtraArgs={'ContentType': content_type}
            )
            return True
        except Exception as e:
            logger.error(f"S3 Upload Error: {e}")
            return False

    def get_presigned_url(self, object_name: str) -> str:
        """Генерирует ссылку на скачивание (действует ограниченное время)"""
        try:
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': object_name},
                ExpiresIn=settings.PRESIGNED_URL_EXPIRATION
            )
        except Exception as e:
            logger.error(f"S3 Presigned URL Error: {e}")
            return ""

storage_service = StorageService()