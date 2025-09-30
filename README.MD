Sample Car Catalog on Django

Steps to install:
1. Install requirements.txt  
    ```pip install -r requirements.txt```<br /><br />
2. Setup database credentials in .env file<br />
    rename .env.example to .env and fill in the credentials<br /><br />
3. Migrations  
    ```python manage.py makemigrations```<br />
    ```python manage.py migrate```<br /><br />
4. Create superuser<br />
    ```python manage.py createsuperuser```<br /><br />
5. Run server<br />
    ```python manage.py runserver```