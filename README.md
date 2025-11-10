# 🐏 RamFinder – Campus Resource Finder

**RamFinder** is a lightweight web app built to help CSU students, staff, and visitors easily locate on-campus resources such as printers, study rooms, labs, vending machines, and medical providers.

This project demonstrates Agile development using **Scrum** and showcases an incremental, user-focused design with modern front-end technologies.

---

## 🚀 Overview

RamFinder allows users to:
- 🔍 **Search** for campus resources by name, type, or location.
- 🕒 **Check availability** (open or closed) in real time.
- 🗺️ **View directions** to the resource using Google Maps.
- ⭐ **Save favorites** for quick access.
- 🔐 **Authenticate users** with email-based login.
- 🧑‍💼 **Manage resources and admins** through a secure admin dashboard.
- 🌗 **Toggle themes** (light/dark).
- 🗂️ **View results by category** with optional grouped/accordion view.

---

## 🧱 Project Structure

```
RamFinder/
│
├── index.html               # Main search and home page
├── resource.html            # Resource detail page
├── login.html               # Login and sign-up page
├── favorites.html           # View user favorites
├── admin.html               # Admin management console
│
├── assets/
│   ├── styles.css           # Global site styles (light/dark themes)
│   ├── store.js             # Handles data storage and fetching
│   ├── auth.js              # Manages authentication and sessions
│   ├── favs.js              # Handles user favorites
│
├── data/
│   ├── resources.json       # Resource data (main database)
│   ├── admins.json          # Admin credentials
│   └── users.json           # User accounts (optional)
│
├── app.py                   # Optional Flask server for persistence
└── README.md                # Project documentation
```
---

## ⚙️ Setup Instructions

### 1️⃣ Download the Project

#### Option A – From ZIP
1. Download the ZIP file containing all project files.
2. Extract it to a local folder (e.g., `~/Documents/RamFinder`).

#### Option B – From GitHub
```bash
git clone https://github.com/yourusername/ramfinder.git
cd ramfinder
```

### 2️⃣ Run the App Locally
1. Run the server
```bash
cd ramfinder
python -m http.server 8000
```

2. Run flask
```bash
python app.py
```
