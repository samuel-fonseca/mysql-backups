import subprocess, os
from datetime import datetime
from dotenv import load_dotenv, dotenv_values

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

if __name__ == '__main__':
    load_dotenv()
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_file = f"backups/backup-dump-{timestamp}.sql"

    generate_mysql_dump(
        user=os.getenv('DB_USERNAME'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_DATABASE'),
        output_file=output_file
    )