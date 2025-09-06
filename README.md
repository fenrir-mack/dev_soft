#  EstudaAI – Sistema de Recomendação de Trilhas de Aprendizagem

Membros:
- Gustavo Ebeling de Almeida
- Ian Erichsen Pacher De Araujo
- Guilerme Guimaraes Lopes
- Guilerme Diego Sanches
- Andre Tozi Magalhaes 
- Lucas Diniz Ferreira Masteguim 
- Lucas Oliveira Da Silva
- Joao De Sa Calvano Bezerra

---

## Table of Contents

- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Server](#running-the-server)
- [Next Steps](#next-steps)
- [Notes](#notes)

---

## Project Structure


projeto/ <br />
├── config/          # Django project folder (settings and configuration)<br />
├── core/            # Main app (models, views, urls, serializers)<br />
├── manage.py        # Django management script<br />
├── requirements.txt # Python dependencies<br />
└── .gitignore       # Files to ignore in Git<br />


---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/fenrir-mack/dev_soft.git
cd dev_soft
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:

- **Windows:**
```powershell
venv\Scripts\activate
```

- **Mac/Linux:**
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Running the Server

Start the Django development server:

```bash
python manage.py runserver
```

Test the endpoints:

- Homepage (optional): `http://127.0.0.1:8000/`  
- Ping endpoint: `http://127.0.0.1:8000/api/ping/` → returns:

```json
{"message": "pong!"}
```

---

## Next Steps

- See the YoutTrack page for more informations

https://eemackenzie.youtrack.cloud/dashboard?id=169-0 


---
