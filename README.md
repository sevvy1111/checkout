Marketplace Application
This is a Django-based marketplace application. It allows users to create listings, message sellers in real-time, and more.

Prerequisites
Before you begin, ensure you have the following installed:

Python 3.11 or later

Git

Getting Started
Follow these steps to get the project running on your local machine.

1. Clone the Repository

Bash

git clone <repository-url>
cd destination path
2. Set up the Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

Bash

python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
3. Install Dependencies

Install the required packages using pip.

Bash
pip install daphne
pip install channels
pip install channels_redis
pip install crispy-bootstrap4
pip install -r requirements.txt
4. Database Migrations

Apply the database migrations to set up the database tables.

Bash

python manage.py makemigrations
python manage.py migrate
5. Create a Superuser

This step is optional but recommended for accessing the Django admin panel.

Bash

python manage.py createsuperuser
6. Run the Development Server

The project uses Daphne as an ASGI server to handle websockets for real-time features.

Bash
wsl --install
run WSL
sudo apt-get install redis-server
sudo apt-get update
sudo service redis-server start

daphne marketplace.asgi:application
This will start the server on http://127.0.0.1:8000. Your marketplace application is now running.
