# Happy Auction

A full-stack web application that allows users to create, browse, and interact with online auction listings.

## Live Demo

Frontend: https://master.d5h48p7i3yhj3.amplifyapp.com  
Backend API: https://api.happy-auction.omizoasuna.com

## Features

- User authentication (login / logout, session-based)
- Create new auction listings with image upload
- Browse active and closed listings
- Add and remove items from a watchlist
- View user-specific listings ("My Auctions")
- Post comments on listings
- Place bids on active auctions
- Upload and display images

## Tech Stack

### Frontend

- React (Vite)
- JavaScript (ES6+)
- CSS

### Backend

- Django
- Django REST Framework

### Infrastructure

- Nginx (reverse proxy and media serving)
- Gunicorn (WSGI server)
- SQLite (database)

### Deployment

- Frontend: AWS Amplify
- Backend: AWS EC2 (Ubuntu)

## Architecture

React (Amplify)
↓ (API requests with credentials)
Django REST API (EC2 + Gunicorn)
↓
SQLite Database
↓
Media files served by Nginx

## Authentication

- Session-based authentication
- CSRF protection enabled
- Cookies configured for cross-origin requests (SameSite=None, Secure)

## Project Structure

Happy-auction/
├── auctions/
│ ├── backend/ # Django project
│ └── frontend/ # React application
├── freeImage/ # Sample images

## Setup (Local Development)

### Backend

cd auctions/backend  
python -m venv venv  
source venv/bin/activate  
pip install -r requirements.txt  
python manage.py migrate  
python manage.py runserver

### Frontend

cd auctions/frontend  
npm install  
npm run dev

## API Example

GET /api/auctions/?status=active  
POST /api/auth/login/  
POST /api/auth/logout/  
GET /api/auth/me/

## Notes

- Media files are served from /media/ via Nginx
- SQLite is used for simplicity and development purposes
- Cross-origin requests require credentials and proper CSRF handling

## Future Improvements

- Migrate database to PostgreSQL
- Use AWS S3 for media storage

## Author

Asuna Omizo
