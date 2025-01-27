#!/usr/bin/env python3
from config import Config
from mysql_backup_manager import MysqlBackupManager

def main():
    manager = MysqlBackupManager(Config())
    manager.backup()

main()
