# Collaborative Text Editor

A web-based collaborative text editor built with Django and Django Channels. This editor allows multiple users to collaborate on text documents in real-time.

---

## Features

- Real-time text collaboration using WebSockets
- User authentication for secure document access
- Document version history
- Role-based access control for users (e.g., read-only vs. edit permissions)

---

## Requirements

- Python 3.8 or higher
- pip for package management
- git for version control

---

## Getting Started

Follow these steps to set up the project on your local machine.

### 1. Clone the Repository

```bash
git clone https://github.com/BaliBot2/colab-text-editor.git
cd colab-text-editor
```
---

### 2. Set Up a Virtual Environment

Create and activate a virtual environment:

**Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

---

### 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

---

### 4. Configure the Database

Apply database migrations to set up the required tables:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 5. Run the Development Server

Start the Django development server:

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser to access the application.

---

## Usage

### 1. Create a User Account

- Register for an account by visiting the signup page.
- Log in to access the editor.

### 2. Create or Open a Document

- Start a new document or open an existing one from your dashboard.

### 3. Collaborate

- Share the document link with collaborators to work together in real time.

---

## Configuration -- Environment Variables

Create a `.env` file in the project directory to define sensitive settings such as:

```plaintext
SECRET_KEY=<your_secret_key>
DEBUG=True
DATABASE_URL=<your_database_url>
```
----

## Contributing

Contributions are welcome! Follow these steps to contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/new-feature`).
3. Commit your changes (`git commit -m "Add new feature"`).
4. Push to the branch (`git push origin feature/new-feature`).
5. Open a pull request.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Acknowledgments

- [Django](https://www.djangoproject.com/)
- [Django Channels](https://channels.readthedocs.io/)
- [Bootstrap](https://getbootstrap.com/) (for frontend styling)

---

For additional help or questions, feel free to reach out via [aditya.bali_ug25@ashoka.edu.in](mailto:aditya.bali_ug25@ashoka.edu.in).

