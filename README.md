# PASOK: a portable student attendance system for PUP CCIS using QR code

## Instructions
1. Clone the repository
2. Run the following command to install the required packages:
```pip install -r requirements.txt```
3. Run the following commands to initialize the database:
```
flask db init
flask db migrate
flask db upgrade
```
4. Run the system with
```python manage.py run```