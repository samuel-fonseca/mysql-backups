import subprocess, os, logging, boto3
from datetime import datetime
from dotenv import load_dotenv, dotenv_values
from botocore.exceptions import ClientError

def generate_mysql_dump(
    user,
    password,
    host,
    database,
    output_file='backups/backup-dump.sql'
):
    """
    Generate a MySQL dump file.

    :param user: MySQL user.
    :param password: MySQL password.
    :param host: MySQL host.
    :param database: MySQL database.
    :param output_file: Output file.
    """

    command = [
        "mysqldump",
        f"-u{user}",
        f"-p{password}",
        f"-h{host}",
        database,
    ]

    with open(output_file, 'w', encoding='utf-8') as f:
        try:
            subprocess.run(command, stdout=f, stderr=subprocess.PIPE, check=True)
            print(f"Backup generated successfully: {output_file}")
        except subprocess.CalledProcessError as e:
            print("Error generating backup:")
            print(e.stderr.decode())

def encrypt_mysql_dump(file, passphrase):
    """
    Encrypt the MySQL dump file.

    :param file: File to encrypt.
    :param passphrase: GPG passphrase.
    :return: Encrypted file path.
    """

    encrypted_output_file = f"{file}.gpg"

    command = [
        "gpg",
        "--batch",
        "--yes",
        "--passphrase", passphrase,
        "--symmetric",
        "--cipher-algo", "AES256",
        "--output", encrypted_output_file,
        file
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Backup encrypted successfully: {file}.gpg")
        return encrypted_output_file
    except subprocess.CalledProcessError as e:
        print("Error encrypting backup:")
        print(e.stderr.decode())

def upload_file_to_s3_bucket(file, bucket, object_name=None):
    """
    Upload a file to an S3 bucket.

    :param file: File to upload.
    :param bucket: Bucket to upload to.
    :param object_name: S3 object name.
    :return: True if the file was uploaded, else False.
    """

    if object_name is None:
        object_name = os.path.basename(file)

    s3_client = boto3.client('s3')

    try:
        response = s3_client.upload_file(file, bucket, object_name)
        print(f"Backup uploaded successfully: {object_name}")
    except ClientError as e:
        logging.error(e)
        return False
    return True

def timestamp():
    return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

if __name__ == '__main__':
    load_dotenv()
    logging.debug(f"[{timestamp()}] Starting backup process...")
    backup_dir = os.getenv('BACKUP_DIRERCTORY')
    output_file = f"{backup_dir}/backup-dump-{timestamp()}.sql"

    generate_mysql_dump(
        user=os.getenv('DB_USERNAME'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_DATABASE'),
        output_file=output_file
    )

    if not os.path.exists(output_file):
        print("Backup not generated. Upload cancelled.")
        logging.error(f"[{timestamp()}] Backup not generated. Upload cancelled.")
        exit(1)
    else: 
        print("Backup generated successfully.")
        logging.debug(f"[{timestamp()}] Backup generated successfully.")

    passphrase = os.getenv('GPG_PASSPHRASE')

    if not passphrase:
        print("GPG passphrase not found. Backup has been generated, but not encrypted. Upload cancelled.")
        logging.error(f"[{timestamp()}] GPG passphrase not found. Backup has been generated, but not encrypted. Upload cancelled.")
        exit(1)

    encrypted_output_file = encrypt_mysql_dump(output_file, passphrase)

    if not os.path.exists(encrypted_output_file):
        print("Backup not encrypted. Upload cancelled.")
        logging.error(f"[{timestamp()}] Backup not encrypted. Upload cancelled.")
        exit(1)
    else:
        print("Backup encrypted successfully.")
        logging.debug(f"[{timestamp()}] Backup encrypted successfully.")

    bucket = os.getenv('AWS_S3_BUCKET')
    object_name = f"backup-dump-{timestamp()}.sql.gpg"

    if not bucket:
        print("S3 bucket not defined. Upload cancelled.")
        logging.error(f"[{timestamp()}] S3 bucket not defined. Upload cancelled.")
        exit(1)

    if not upload_file_to_s3_bucket(encrypted_output_file, bucket, object_name):
        print("Backup not uploaded.")
        logging.error(f"[{timestamp()}] Backup not uploaded.")
        exit(1)
    else:
        print("Backup uploaded successfully.")
        logging.debug(f"[{timestamp()}] Backup uploaded successfully.")
        exit(0)
