

1. Clone the Repository

Bash

git clone https://github.com/sevvy1111/checkout
cd destination path


Create Virtual Env.

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

Database Migrations

python manage.py makemigrations
python manage.py migrate

Create .env file root directory(Create Cloudinary Account for media handling and get your keys)
CLOUDINARY_API_KEY=yourapikey
CLOUDINARY_API_SECRET=yoursecretkey
CLOUDINARY_CLOUD_NAME=yourcloudname

Run the Development Server

python manage.py runserver
