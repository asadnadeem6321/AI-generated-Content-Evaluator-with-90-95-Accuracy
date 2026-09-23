<div align="center">

# 🤖 AI Content Evaluator

### _Intelligent Academic Integrity & Content Analysis Platform_

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-REST_Framework-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-ML_Service-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-Queue-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

<br/>

> **University of Education, Lahore — Department of Information Sciences**
> BS Information Technology (Post ADP) · 2024–2026
> Project ID: BSIT-APDP-F22-M-31 · Supervisor: Dr. Uzma Omer

<br/>

_A web-based intelligent platform that detects AI-generated academic content, evaluates grammar, and generates comprehensive feedback reports — helping educators maintain academic integrity with 90–95% detection accuracy._

</div>

---

## 🎯 Overview

The **AI Content Evaluator** addresses a critical challenge in modern education: as AI tools become ubiquitous, distinguishing between human-written and AI-generated academic work has become increasingly difficult.

This platform provides:

- 🔍 **AI vs Human authorship detection** at document and paragraph level
- ✏️ **Grammar & linguistic analysis** with correction suggestions
- 📊 **Comprehensive annotated PDF reports** with color-coded feedback
- 👥 **Role-based interfaces** for Students, Teachers, Admins, and Guests
- ⚡ **Async processing** with Redis queues and multiple ML workers

---

## ✨ Key Features

| Feature                         | Description                                                      |
| ------------------------------- | ---------------------------------------------------------------- |
| 🎯 **High Accuracy**            | 90–95% detection accuracy using ensemble ML models               |
| 🔬 **45 Linguistic Features**   | Covers text stats, readability, syntax, stylometrics & semantics |
| 📄 **Paragraph-Level Analysis** | Flags specific AI-generated sections within documents            |
| ✅ **Grammar Scoring**          | Automated grammar analysis with detailed error reporting         |
| 📑 **Annotated PDF Reports**    | Color-coded feedback with highlighted corrections                |
| 🏫 **Class Management**         | Full LMS workflow: classes → assignments → submissions → reports |
| 👤 **Guest Access**             | Quick evaluation without institutional enrollment                |
| ⚡ **Scalable Architecture**    | Async processing with Redis + multiple ML workers                |

---

## 🤖 Methodology

![Methodology Diagram](./screenshot/5.png)

---

## 👥 User Roles & Workflows

### Guest Workflow

![Guest Workflow](./screenshot/4.png)

### Teacher Workflow

![Teacher Workflow](./screenshot/2.png)

### Student Workflow

![Student Workflow](./screenshot/1.png)

### Admin Workflow

![Admin Workflow](./screenshot/3.png)

---

## 🛠️ Tech Stack

### Backend

- **Django REST Framework** — RESTful API, auth, file management
- **FastAPI** — High-performance ML inference service
- Celery — Distributed async task queue

### Machine Learning

- **scikit-learn** — Ensemble methods & model training
- **XGBoost, RandomForest, CatBoost** — Gradient boosting frameworks
- **LanguageTool** — Grammar checking

### Data Processing

- **PyMuPDF (fitz)** — PDF parsing & text extraction
- **pdfplumber** — Advanced PDF layout extraction
- **pandas, numpy** — Data manipulation & numerical computing

### Infrastructure

- **PostgreSQL** — Primary relational database
- **Redis** — Caching and job queue
- **MinIO / S3** — File storage
- **Docker & Docker Compose** — Containerization

### Frontend

- **React** — Component-based UI
- **Tailwind CSS** — Utility-first styling

---

## 📦 Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose _(optional)_

### Setup

**1. Clone the repository**

```bash
git clone https://github.com/yourusername/ai-detection-backend.git
cd ai-detection-backend
```

**2. Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment**

```bash
cp .env.example .env
# Edit .env with your configuration
```

**5. Database setup**

```bash
python manage.py migrate
python manage.py createsuperuser
```

**6. Download ML models**

```bash
python scripts/download_models.py
```

**7. Run all services**

```bash
# Terminal 1 — Django API
python manage.py runserver

# Terminal 2 — Celery Worker
celery -A config worker -l info -Q submissions,default,celery

# Terminal 3 — FastAPI ML Service
uvicorn app.main:app --reload --port 8001
```

---

## 🐳 Docker Deployment

```bash
# Build and start all services
sudo docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

---

---

## 🚀 Performance Optimization

- **Parallel Processing** — Multiprocessing for feature extraction
- **Model Caching** — Pre-loaded ML models in memory
- **Redis Caching** — Frequent query results cached
- **Batch Inference** — Multiple paragraphs processed simultaneously
- **Async I/O** — FastAPI async endpoints for non-blocking operations
- **Connection Pooling** — Database connection reuse

---

## 🔒 Security

- JWT-based authentication
- Rate limiting on API endpoints
- File type validation and size limits
- SQL injection prevention (Django ORM)
- CORS configuration
- Role-based access control (Student / Teacher / Admin / Guest)
- Environment-based secrets management
- Encrypted communication between all services

---

## 🔮 Future Work

- 📱 Mobile application for on-the-go access
- 🔗 Integration with external plagiarism APIs
- 📈 Analytics dashboard for performance trends
- ☁️ Cloud deployment for horizontal scalability
- 🌐 Multi-language support
- 🧠 Advanced semantic grading of complex academic theories

---

## UI Screenshots

![Guest Workflow](./screenshot/landing/Gemini_Generated_Image_etm83cetm83cetm8-clean.png)

### Landing Page

![Guest Workflow](./screenshot/landing/2.png)
![Guest Workflow](./screenshot/landing/3.png)

### Teacher Portal

![Guest Workflow](./screenshot/teacher/Gemini_Generated_Image_hmn1iwhmn1iwhmn1-clean.png)
![Teacher Workflow](./screenshot/teacher/1.png)
![Teacher Workflow](./screenshot/teacher/2.png)
![Teacher Workflow](./screenshot/teacher/3.png)
![Teacher Workflow](./screenshot/teacher/4.png)
![Teacher Workflow](./screenshot/teacher/5.png)
![Teacher Workflow](./screenshot/teacher/6.png)

### Student Student

![Guest Workflow](./screenshot/student/Gemini_Generated_Image_d9yfb9d9yfb9d9yf-clean.png)
![Teacher Workflow](./screenshot/student/1.png)
![Teacher Workflow](./screenshot/student/2.png)
![Teacher Workflow](./screenshot/student/3.png)
![Teacher Workflow](./screenshot/student/4.png)
![Teacher Workflow](./screenshot/student/5.png)
![Teacher Workflow](./screenshot/student/6.png)
![Teacher Workflow](./screenshot/student/7.png)
![Teacher Workflow](./screenshot/student/8.png)

### Guest

![Guest Workflow](./screenshot/guest/Gemini_Generated_Image_ymdo0lymdo0lymdo-clean.png)
![Teacher Workflow](./screenshot/guest/1.png)
![Teacher Workflow](./screenshot/guest/1.png)
![Teacher Workflow](./screenshot/guest/1.png)
![Teacher Workflow](./screenshot/guest/1.png)

### Admin

![Guest Workflow](./screenshot/admin/Gemini_Generated_Image_uawn7uawn7uawn7u-clean.png)
![Teacher Workflow](./screenshot/admin/1.png)
![Teacher Workflow](./screenshot/admin/2.png)

---

## 🙏 Acknowledgments

- Dataset sources and academic writing contributors
- Open-source ML libraries and frameworks
- Academic research on AI text detection methodologies
- University of Education, Lahore — Department of Information Sciences

---

<div align="center">

Made with ❤️ at **University of Education, Lahore**

_June 2026_

</div>
