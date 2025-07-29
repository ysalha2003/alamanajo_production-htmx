#!/usr/bin/env python
import os
import sys

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alamana_repair.settings')

# Setup Django
import django
django.setup()

# Run migrations
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'makemigrations'])
execute_from_command_line(['manage.py', 'migrate'])
