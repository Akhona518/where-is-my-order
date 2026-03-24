# Where Is My Order? - MVP

A simple Flask app that lets customers track their orders using an order number or tracking number.

## Features
- Public tracking page
- Admin login
- Create, update, and delete orders
- Tracking timeline/history
- SQLite database for easy local setup
- Demo seed command

## Quick Start

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

Mac/Linux:

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
export ADMIN_PASSWORD=yourpassword
export SECRET_KEY=replace-me
```

Windows PowerShell:

```powershell
$env:FLASK_APP="app.py"
$env:FLASK_ENV="development"
$env:ADMIN_PASSWORD="yourpassword"
$env:SECRET_KEY="replace-me"
```

### 4. Seed demo data (optional)

```bash
flask seed
```

### 5. Run the app

```bash
flask run
```

Open the app in your browser at the local address Flask prints.

## Demo login
If you do not set `ADMIN_PASSWORD`, the default admin password is:

```text
admin1234
```

## Demo tracking
After running `flask seed`, use either:

```text
AKH12345
```

or

```text
TRK987654
```

## Next upgrades I would add
- Real courier integrations
- Email or WhatsApp notifications
- Customer login/accounts
- CSV bulk upload for orders
- Role-based admin accounts
- Dashboard analytics for delayed orders
