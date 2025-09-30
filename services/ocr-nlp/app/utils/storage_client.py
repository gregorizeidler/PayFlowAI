"""
Cliente para interação com MinIO/S3
"""

from minio import Minio
from minio.error import S3Error
import tempfile
import os
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

class StorageClient:
    """Cliente para operações com MinIO/S3"""
    
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
            else:
                logger.info(f"✅ Bucket {settings.minio_bucket_name} já existe")
        except S3Error as e:
            logger.error(f"❌ Erro ao verificar/criar bucket: {e}")
    
    async def download_file(self, file_path: str) -> Optional[str]:
        """
        Baixa arquivo do MinIO para um arquivo temporário local
        Retorna o caminho do arquivo local
        """
        try:
            logger.info(f"📥 Baixando arquivo: {file_path}")
            
            # Criar arquivo temporário
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=self._get_file_extension(file_path))
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Baixar arquivo do MinIO
            self.client.fget_object(
                settings.minio_bucket_name,
                file_path,
                temp_file_path
            )
            
            logger.info(f"✅ Arquivo baixado para: {temp_file_path}")
            return temp_file_path
            
        except S3Error as e:
            logger.error(f"❌ Erro ao baixar arquivo {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao baixar arquivo: {e}")
            return None
    
    async def upload_file(self, local_file_path: str, remote_file_path: str) -> bool:
        """
        Faz upload de arquivo local para o MinIO
        """
        try:
            logger.info(f"📤 Fazendo upload: {local_file_path} -> {remote_file_path}")
            
            self.client.fput_object(
                settings.minio_bucket_name,
                remote_file_path,
                local_file_path
            )
            
            logger.info(f"✅ Upload concluído: {remote_file_path}")
            return True
            
        except S3Error as e:
            logger.error(f"❌ Erro ao fazer upload: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado no upload: {e}")
            return False
    
    async def cleanup_temp_file(self, temp_file_path: str):
        """Remove arquivo temporário"""
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.info(f"🗑️ Arquivo temporário removido: {temp_file_path}")
        except Exception as e:
            logger.error(f"❌ Erro ao remover arquivo temporário: {e}")
    
    def _get_file_extension(self, file_path: str) -> str:
        """Extrai extensão do arquivo"""
        return os.path.splitext(file_path)[1] or '.tmp'
    
    async def file_exists(self, file_path: str) -> bool:
        """Verifica se arquivo existe no MinIO"""
        try:
            self.client.stat_object(settings.minio_bucket_name, file_path)
            return True
        except S3Error:
            return False
    
    async def get_file_info(self, file_path: str) -> Optional[dict]:
        """Obtém informações do arquivo"""
        try:
            stat = self.client.stat_object(settings.minio_bucket_name, file_path)
            return {
                "size": stat.size,
                "last_modified": stat.last_modified,
                "content_type": stat.content_type,
                "etag": stat.etag
            }
        except S3Error as e:
            logger.error(f"❌ Erro ao obter info do arquivo {file_path}: {e}")
            return None
