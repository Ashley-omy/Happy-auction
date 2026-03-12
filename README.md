# Online Auction Web Application

This is a full-stack auction web application built with Django.  
Users can create auction listings, place bids, add items to a watchlist, and close auctions.

# Demo / How to Use
Watch a short demo video explaining how to use this app:

[![Watch the demo](https://img.youtube.com/vi/h6Qw_l6Fpas?si=6EzjyUfLW_kfA6d7/0.jpg)](https://youtu.be/h6Qw_l6Fpas?si=6EzjyUfLW_kfA6d7)
---

# Live Demo

You can access the deployed application here:

🔗 https://happy-auction.onrender.com/my-auctions

---

# Features

## Guest Users

Guests can browse the site but have limited functionality.

- View all auction listings
- View listing details

Guests **cannot:**

- Create auction listings
- Add items to their watchlist
- Participate in bidding

---

## Registered Users

After logging in, users can:

- Create auction listings
- Place bids on other users’ auctions
- Add items to their watchlist
- Comment on listings
- View closed auctions

---

## Auction Creator

Users can create an auction listing by providing:

- **Item title**
- **Description**
- **Category** (optional)
- **Image URL** (optional)
- **Starting bid**

### Validation

If a user attempts to bid **below the starting bid**, an error will be displayed.

### Auction Management

The creator of an auction can:

- Monitor bids
- Read comments
- Close the auction whenever they decide the bid is satisfactory.

---

## Auction Winner

When an auction is closed:

- The user with the **highest bid** becomes the winner.
- The winning user will see the message:


This message appears on the **Closed Auctions tab**.

---

# Test Accounts

You can use the following accounts for testing:

| Username | Password |
|----------|----------|
| test1 | 12345 |
| test2 | 12345 |

---

# Technology Stack

### Backend
- Django (Python)

### Frontend
- HTML
- CSS

### Database
- PostgreSQL

### Features Implemented
- User authentication system
- Auction bidding system
- Watchlist functionality
- Comment system
- Auction closing mechanism

---

# Project Background

This project was developed as the **third project (Commerce)** in the **CS50 Web Programming with Python and JavaScript course**.

The following components were designed and implemented independently:

- Application architecture
- Backend logic
- Database schema
- User interface

---

# Author

Ashley Omy
