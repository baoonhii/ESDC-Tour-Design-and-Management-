# Enterprise_TDMS
repo for enterprise system analysis and design project - Tour Design and Management System (TDMS)

## Steps for setup
1. Install PostgreSQL 16

    [PostgreSQL](https://www.postgresql.org/download/windows/) 
    (Choose version `16 - latest`)

    - Note: Install everything, especially `pgAdmin`

2. Git clone this repo

3. Install Python
    - Python 3.11.4 (Not sure if the version matters that much for now)
    - Install pip (must)
    - Create a virtual environment: 

        ```python -m venv venv```

    - Activate the environment
    
        ```"venv\Scripts\activate"```

4. Install Django

    ```
    pip install Django
    pip install djangorestframework
    pip install psycopg2
    pip install requests
    pip install numpy
    pip install scikit-learn
    ```

5. Setup the project

    ```
    django-admin startproject theTourCorporation
    ```

6. Create new server in pgAdmin
    - Open pgAdmin
    - Create new Server
    - Info: 
        ```
            Name: tourmannerDB
            Hostname: localhost
            Port: 5432
            Username: postgres
            Password: [see on the doc]
            Save password? [Check - on]

        ```
    - In `tourmannerDB`, create db `tdmsDB`

7. Start the project
    ```
    cd theTourCorporation
    python manage.py startapp TDMS
    ```

8. Set up the TDMS_main/TDMS_main/settings.py
    Create theTourCorporation\theTourCorporation\super_secrets.py 
    ```
        from super_secrets import db_pass
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'tdmsDB',
                'USER': 'postgres',
                'PASSWORD': db_pass,
                'HOST': 'localhost',
                'PORT': '5432',
            }
        }
    ```
9. Run migrations
    ```
        python manage.py makemigrations
        python manage.py migrate
    ```

10. Collect static files
    ```
        python manage.py collectstatic
    ```

11. Run the project
    ```
        python manage.py runserver
    ```

12. Create superuser
    ```
        python manage.py createsuperuser
    ```

13. Update db if you imported cvs:
    ```
        python manage.py sqlsequencereset TDMS
    ```