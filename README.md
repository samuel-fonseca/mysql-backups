# MySQL Backups

I created this simple Python script to generate a `mysqldump` output, encrypt it (using GPG), then upload it to an S3 bucket.

## Get Started

1. Copy the `.env.example` file as `.env`. 
2. Fill in the variables in the .env file
3. Run `python ./src/backup.py`

## Requirements

This python code depends on a few local dependencies:

1. [Mysql Client](https://www.mysql.com/) (`mysqldump`)
2. [GPG](https://gnupg.org/)
