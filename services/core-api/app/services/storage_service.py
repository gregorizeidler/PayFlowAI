"""
Serviço de armazenamento usando MinIO
"""

from minio import Minio
from minio.error import S3Error
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    """Serviço para operações com MinIO/S3"""
    
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        
        # Garantir que o bucket existe
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Garante que o bucket existe"""
        try:
            if not self.client.bucket_exists(settings.minio_bucket_name):
                self.client.make_bucket(settings.minio_bucket_name)
                logger.info(f"✅ Bucket {settings.minio_bucket_name} criado")
        except S3Error as e:
            logger.error(f"❌ Erro ao verificar/criar bucket: {e}")
    
    async def upload_file(self, local_file_path: str, remote_file_path: str) -> bool:
        """
        Faz upload de arquivo local para o MinIO
        """
        try:
            logger.info(f"📤 Upload: {local_file_path} -> {remote_file_path}")
            
            self.client.fput_object(
                settings.minio_bucket_name,
                remote_file_path,
                local_file_path
            )
            
            logger.info(f"✅ Upload concluído: {remote_file_path}")
            return True
            
        except S3Error as e:
            logger.error(f"❌ Erro no upload: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado no upload: {e}")
            return False
    
    async def download_file(self, remote_file_path: str, local_file_path: str) -> bool:
        """
        Baixa arquivo do MinIO para local
        """
        try:
            self.client.fget_object(
                settings.minio_bucket_name,
                remote_file_path,
                local_file_path
            )
            return True
        except S3Error as e:
            logger.error(f"❌ Erro no download: {e}")
            return False
    
    async def file_exists(self, file_path: str) -> bool:
        """Verifica se arquivo existe"""
        try:
            self.client.stat_object(settings.minio_bucket_name, file_path)
            return True
        except S3Error:
            return False
    
    async def delete_file(self, file_path: str) -> bool:
        """Remove arquivo do storage"""
        try:
            self.client.remove_object(settings.minio_bucket_name, file_path)
            return True
        except S3Error as e:
            logger.error(f"❌ Erro ao deletar arquivo: {e}")
            return False
