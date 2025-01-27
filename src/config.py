import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self.db_user = os.getenv('DB_USERNAME')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_host = os.getenv('DB_HOST')
        self.db_database = os.getenv('DB_DATABASE')
        self.backup_dir = os.getenv('BACKUP_DIRECTORY', './backups')
        self.gpg_passphrase = os.getenv('GPG_PASSPHRASE')
        self.aws_s3_bucket = os.getenv('AWS_S3_BUCKET')
