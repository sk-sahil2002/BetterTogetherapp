# better together - Crowdfunding Platform


design developed owned by Ali, Hayder, Sahil.
A modern crowdfunding platform built with Django that enables users to create and manage fundraising campaigns for various causes.



## Features

### User Management
- User registration and authentication
- Profile management with avatar support
- Password change functionality
- Account settings customization

### Campaign Management
- Create and manage fundraising campaigns
- Rich text editor for campaign descriptions
- Campaign categorization
- Campaign status tracking (active, pending, completed)
- Campaign progress tracking
- Image upload support
- Campaign sharing functionality

### Donation System
- Secure donation processing
- Anonymous donation option
- Multiple payment gateway support
- Donation tracking and statistics
- Minimum donation validation
- Donation comments

### Dashboard
- User campaign dashboard
- Campaign statistics
- Donation history
- Campaign performance metrics

### Search & Discovery
- Category-based browsing
- Search functionality
- Featured campaigns
- Recent campaigns showcase
- Campaign filtering

### Additional Features
- Responsive design
- Social media sharing
- Email notifications
- Campaign embedding
- Progress tracking
- Real-time statistics


## Tech Stack

### Backend
- Python 3.x
- Django 4.x
- PostgreSQL
- Django REST Framework

### Frontend
- HTML5
- CSS3
- JavaScript
- Bootstrap 4
- jQuery
- Font Awesome
- TinyMCE Editor

### Additional Tools
- Pillow for image processing
- Django Humanize
- Django Crispy Forms
- Python Decouple
- Django Debug Toolbar

## Installation

1. Clone the repository
```bash
git clone 
cd fundly
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate # On Windows use: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run migrations
```bash
python manage.py migrate
```

5. Create a superuser
```bash
python manage.py createsuperuser
```

6. Generate sample data (optional)
```bash
python manage.py generate_sample_data
```

7. Run the development server
```bash
python manage.py runserver
```


