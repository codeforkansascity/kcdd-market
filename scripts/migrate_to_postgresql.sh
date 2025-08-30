#!/bin/bash

# Migration script from SQLite to PostgreSQL
# This script automates the migration process

set -e  # Exit on any error

echo "🚀 Starting SQLite to PostgreSQL migration..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if we have the current SQLite database
if [ ! -f "db.sqlite3" ]; then
    print_warning "No SQLite database found. Creating fresh PostgreSQL database..."
    FRESH_START=true
else
    FRESH_START=false
fi

# Step 1: Export data from SQLite (if exists)
if [ "$FRESH_START" = false ]; then
    print_status "Step 1: Exporting data from SQLite..."
    
    # Create a temporary settings file for SQLite export
    cat > config/settings_sqlite.py << EOF
from .settings import *
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
EOF
    
    # Export data
    python3 manage.py migrate_to_postgresql --export-only --export-file sqlite_export.json
    
    # Clean up temporary settings
    rm config/settings_sqlite.py
    
    print_status "Data export completed."
else
    print_status "No existing data to export. Starting fresh."
fi

# Step 2: Start PostgreSQL container
print_status "Step 2: Starting PostgreSQL container..."
docker-compose up -d db

# Wait for PostgreSQL to be ready
print_status "Waiting for PostgreSQL to be ready..."
until docker-compose exec -T db pg_isready -U kcdd_user -d kcdd_market; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

print_status "PostgreSQL is ready!"

# Step 3: Update Django settings to use PostgreSQL
print_status "Step 3: Updating Django settings for PostgreSQL..."

# Create environment file
cat > .env << EOF
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_HOST=db
DB_PORT=5432
DB_NAME=kcdd_market
DB_USER=kcdd_user
DB_PASSWORD=kcdd_password

# Site Configuration
SITE_URL=http://localhost:8000
EOF

print_status "Environment file created."

# Step 4: Run migrations on PostgreSQL
print_status "Step 4: Running Django migrations on PostgreSQL..."
python3 manage.py migrate

print_status "Migrations completed."

# Step 5: Import data (if we had data to export)
if [ "$FRESH_START" = false ] && [ -f "sqlite_export.json" ]; then
    print_status "Step 5: Importing data to PostgreSQL..."
    python3 manage.py migrate_to_postgresql --import-only --export-file sqlite_export.json
    
    # Create superuser if needed
    print_status "Creating superuser..."
    python3 manage.py createsuperuser --noinput || true
    
    print_status "Data import completed."
else
    print_status "Step 5: Creating sample data..."
    python3 manage.py create_sample_data
fi

# Step 6: Start the full application
print_status "Step 6: Starting the full application..."
docker-compose up -d

print_status "Migration completed successfully! 🎉"
echo ""
echo "Your application is now running with PostgreSQL!"
echo "Access it at: http://localhost:8000"
echo ""
echo "To stop the application: docker-compose down"
echo "To view logs: docker-compose logs -f"
echo ""
echo "Note: Your SQLite database has been preserved as 'db.sqlite3'"
echo "The exported data is in 'sqlite_export.json'"
