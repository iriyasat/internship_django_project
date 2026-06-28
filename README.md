# Django Project Setup Guide (macOS)

Welcome to your new machine setup! Below are the step-by-step instructions to get this Django project up and running on macOS.

---

## Step 1: Clone and Navigate to the Project

Open your Terminal on macOS and clone/navigate to the project repository:
```bash
cd "path/to/cloned/Django Project"
```

---

## Step 2: Set Up Python and Virtual Environment

On macOS, the python command is usually `python3`. 

1. **Create a new virtual environment**:
   ```bash
   python3 -m venv venv
   ```

2. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```

3. **Install the required packages**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

> [!NOTE]
> If you run into issues installing dependencies (e.g. `mysqlclient` or `PyMySQL` compilation errors), ensure you have Xcode Command Line Tools installed by running `xcode-select --install`.

---

## Step 3: Set Up XAMPP MySQL Database

1. Open **XAMPP** on your Mac.
2. Start the **MySQL Database** service.
3. Open **phpMyAdmin** in your browser (usually `http://localhost/phpmyadmin`).
4. Click on **New** on the left panel, name the database `car_sales`, select collation `utf8mb4_general_ci`, and click **Create**.

---

## Step 4: Unzip and Import the SQL Dataset

Because the SQL dataset is **133 MB**, it exceeds the default phpMyAdmin web upload limits. You can import it using one of two methods:

### Method A: Command Line (Recommended & Fastest)

This method bypasses any file upload limits or browser time-outs.

1. **Unzip the dataset** in your project folder:
   You can right-click `project1/dataset/car_sales_final.zip` in Finder and select **Extract**, or run this terminal command:
   ```bash
   unzip project1/dataset/car_sales_final.zip -d project1/dataset/
   ```

2. **Import the SQL file via XAMPP MySQL CLI**:
   Run the following command to import the SQL directly (replace `root` if you have set a MySQL password):
   ```bash
   /Applications/XAMPP/xamppfiles/bin/mysql -u root -p car_sales < project1/dataset/car_sales_final.sql
   ```
   *If prompted for a password and you haven't set one, just press **Enter**.*

---

### Method B: phpMyAdmin Web GUI (Alternative)

If you prefer using phpMyAdmin, you must first increase XAMPP's PHP upload limits:

1. Open your XAMPP directory and locate `php.ini` (usually at `/Applications/XAMPP/xamppfiles/etc/php.ini`).
2. Open `php.ini` in a text editor and search for/modify the following configurations:
   ```ini
   upload_max_filesize = 256M
   post_max_size = 256M
   max_execution_time = 300
   ```
3. Restart Apache and MySQL services in the XAMPP Control Panel.
4. Go to phpMyAdmin, select the `car_sales` database, click **Import**, choose `project1/dataset/car_sales_final.sql`, and run the import.

---

## Step 5: Verify Port and DB Configurations

In `project1/project1/settings.py`, the database settings are currently set to port `33007`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'car_sales',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '33007',  # <-- Verify this port
        # ...
    }
}
```

> [!IMPORTANT]
> Standard XAMPP installations on macOS use the default MySQL port `3306`. 
> If your XAMPP MySQL is running on `3306`, edit [settings.py](file:///project1/project1/settings.py) and change `'PORT': '33007'` to `'PORT': '3306'` depending on your XAMPP network configuration.

---

## Step 6: Run the Server

Once the virtual environment is active and the database is imported:

1. Navigate to the inner `project1` directory (where `manage.py` is located):
   ```bash
   cd project1
   ```

2. Run the development server:
   ```bash
   python manage.py runserver
   ```

3. Open your browser and navigate to `http://127.0.0.1:8000`.
