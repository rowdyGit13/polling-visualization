# Django Polling Application

A feature-rich polling application built with Django, PostgreSQL, and modern best practices.

## Features

- **Advanced Poll Management**: Create, update, and manage polls with categories and metadata
- **User Authentication**: Register, login, and manage user accounts
- **User Voting**: Users can vote on polls and change their votes
- **Analytics**: Track voting statistics and generate reports
- **RESTful API**: Complete API for all application features
- **PostgreSQL Integration**: Leverages advanced PostgreSQL features
- **Background Tasks**: Uses Celery for asynchronous processing
- **Caching**: Implements performance optimization via caching

## Technology Stack

- **Backend**: Python 3.x + Django 5.x
- **Database**: PostgreSQL
- **API**: Django REST Framework
- **Task Queue**: Celery + Redis
- **Testing**: pytest + Django test framework
- **Deployment**: Docker-ready with Gunicorn

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/django-polling-app.git
cd django-polling-app
```

2. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure PostgreSQL
   - Install PostgreSQL if not already installed
   - Create a database: `createdb mydb`

5. Configure environment variables (or use .env file)
```bash
cp .env.example .env
# Edit .env with your database credentials
```

6. Run migrations
```bash
python manage.py migrate
```

7. Create a superuser
```bash
python manage.py createsuperuser
```

8. Start the development server
```bash
python manage.py runserver
```

## Running with Docker

```bash
# Build the docker image
docker-compose build

# Start the services
docker-compose up

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## API Documentation

The API is available at `/api/` and includes the following endpoints:

- `/api/questions/` - Poll questions
- `/api/choices/` - Poll choices
- `/api/responses/` - User responses
- `/api/analytics/` - Voting analytics

Authentication is required for most endpoints. Use token authentication:

```bash
# Get auth token
curl -X POST -d "username=user&password=pass" http://localhost:8000/api-token-auth/
```

## Running Tests

```bash
pytest
# Or with coverage report
coverage run -m pytest && coverage report
```

## Background Tasks

Celery is used for background processing, including:

- Updating analytics data
- Generating daily reports
- Exporting poll data

To run Celery:

```bash
# Start worker
celery -A mysite worker -l info

# Start beat scheduler
celery -A mysite beat -l info

# Start Flower for monitoring (optional)
celery -A mysite flower
```

## Code Quality

This project follows PEP 8 style guide and uses the following tools:

- Black for code formatting
- Flake8 for linting
- isort for import sorting

## License

This project is licensed under the MIT License - see the LICENSE file for details. # polling-visualization

## NBA Polling App Debugging Summary

### Issues Fixed

1. **URL Reverse Error**: Fixed the `Reverse for 'category' with arguments '('',)' not found` error by:
   - Adding a conditional check in the template to skip empty categories
   - Improving the query in `views.py` to exclude empty category values

2. **Missing Template**: Created the missing `category.html` template for displaying questions by category.

3. **Database Compatibility**: Updated the models to work with both PostgreSQL and SQLite:
   - Added conditional imports for PostgreSQL-specific fields
   - Created SQLite-compatible alternatives for PostgreSQL fields
   - Updated the admin interface to handle both database types

4. **Code Improvements**:
   - Enhanced error handling
   - Improved UI with NBA-themed styling
   - Added data visualization with matplotlib
   - Optimized database queries

### Running the Application

1. Make sure all dependencies are installed:
   ```
   pip install -r requirements.txt
   ```

2. Create and apply migrations:
   ```
   python manage.py makemigrations polls
   python manage.py migrate
   ```

3. Add NBA questions to the database:
   ```
   python manage.py add_nba_questions
   ```

4. Run the development server:
   ```
   python manage.py runserver
   ```

5. Visit http://127.0.0.1:8000/ in your browser

### Features

- Modern UI with NBA-themed design
- Interactive charts using matplotlib
- User authentication and response tracking
- Mobile-responsive design
- REST API for programmatic access
- Database-agnostic implementation
