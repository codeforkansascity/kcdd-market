#!/bin/bash

# Exit on any error
set -e

echo "Starting KCDD Market application..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Database is ready!"

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create admin user if it doesn't exist
echo "Creating admin user..."
python manage.py create_admin --username admin --email admin@example.com --password admin123

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the Django development server
echo "Starting Django development server..."
exec python manage.py runserver 0.0.0.0:8000
