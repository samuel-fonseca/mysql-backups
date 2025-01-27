from config import Config
import subprocess, os, logging, boto3, shutil
from datetime import datetime
from dotenv import load_dotenv, dotenv_values
from botocore.exceptions import ClientError
from typing import Optional

class MysqlBackupManager:
    def __init__(self, config: Config):
        self.config = config
        self.backup_dir = config.backup_dir
        self.db_user = config.db_user
        self.db_password = config.db_password
        self.db_host = config.db_host
        self.db_database = config.db_database
        self.gpg_passphrase = config.gpg_passphrase
        self.aws_s3_bucket = config.aws_s3_bucket
        self.validate_dependencies()

    def validate_dependencies(self) -> None:
        if not all([self.db_user, self.db_password, self.db_host, self.db_database]):
            raise ValueError("Missing database configuration values.")

        if not self.gpg_passphrase:
            raise ValueError("Missing GPP configuration values")

        if not self.aws_s3_bucket:
            raise ValueError("Missing AWS S3 bucket configuration value")

        if not os.path.isdir(self.backup_dir):
            os.makedirs(self.backup_dir)

        if not shutil.which('mysqldump'):
            raise ValueError("mysqldump not found in PATH")

        if not shutil.which('gpg'):
            raise ValueError("gpg not found in PATH")

    def generate_dump(self, output_file: str) -> bool:
        command = [
            "mysqldump",
            f"-u{self.db_user}",
            f"-p{self.db_password}",
            f"-h{self.db_host}",
            self.db_database,
        ]

        with open(output_file, 'w', encoding='utf-8') as f:
            try:
                subprocess.run(command, stdout=f, stderr=subprocess.PIPE, check=True)
                print(f"Backup generated successfully: {output_file}")

                return True
            except subprocess.CalledProcessError as e:
                print("Error generating backup:")
                print(e.stderr.decode())

                return False

    def encrypt_dump(self, file: str) -> Optional[str]:
        encrypted_output_file = f"{file}.gpg"

        command = [
            "gpg",
            "--batch",
            "--yes",
            "--passphrase", self.gpg_passphrase,
            "--symmetric",
            "--cipher-algo", "AES256",
            "--output", encrypted_output_file,
            file
        ]

        try:
            subprocess.run(command, check=True)
            print(f"Backup encrypted successfully: {encrypted_output_file}")
            return encrypted_output_file
        except subprocess.CalledProcessError as e:
            print("Error encrypting backup:")
            print(e.stderr.decode())
            return None

    def upload_to_s3(self, file: str, object_name=None) -> bool:
        s3 = boto3.client('s3')

        try:
            s3.upload_file(file, self.aws_s3_bucket, object_name or file)
            print(f"Backup uploaded successfully: {file}")

            return True
        except ClientError as e:
            print("Error uploading backup:")
            print(e)

            return False

    def generate_backup_file_name(self) -> str:
        if not os.path.isdir(self.backup_dir):
            os.makedirs(self.backup_dir)
        timestamp_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        return os.path.join(self.backup_dir, f"backup-dump-{timestamp_str}.sql")

    def cleanup(self) -> None:
        for file in os.listdir(self.backup_dir):
            # remove files with a timestamp greater than 7 days
            timestamp = file.replace('backup-dump-', '').replace('.sql', '').replace('.gpg', '')
            try:
                file_timestamp = datetime.strptime(timestamp, '%Y-%m-%d_%H-%M-%S')
            except ValueError:
                continue

            if (datetime.now() - file_timestamp).days > 7:
                os.remove(os.path.join(self.backup_dir, file))

    def backup(self) -> None:
        # Generate a timestamped SQL dump filename
        sql_path = self.generate_backup_file_name()

        # Generate a MySQL dump & encrypt it
        if (not self.generate_dump(sql_path)):
            self.cleanup()
            exit(1)

        encrypted_path = self.encrypt_dump(sql_path)

        # Upload the encrypted backup to S3
        object_name = os.path.basename(encrypted_path)
        self.upload_to_s3(encrypted_path, object_name)

        # Cleanup old backups
        self.cleanup()
