# AI Content Detection System - Backend

A high-performance machine learning backend service for detecting AI-generated content in academic documents. This system provides enterprise-grade AI detection capabilities with 90-95% accuracy using advanced ensemble ML models and comprehensive linguistic feature analysis.

## 🎯 Overview

This backend service analyzes academic documents (assignments, research papers, thesis, etc.) to identify AI-generated content at both document and paragraph levels. It combines multiple machine learning algorithms with 43+ linguistic features to deliver accurate detection results, grammar scoring, and detailed analysis reports.

## ✨ Key Features

- **High Accuracy Detection**: 90-95% accuracy using ensemble ML models
- **Paragraph-Level Analysis**: Identifies specific AI-generated sections within documents
- **Comprehensive Feature Extraction**: 43+ linguistic and stylistic features including:
  - Text statistics (word count, sentence length, lexical diversity)
  - Readability metrics (Flesch-Kincaid, Gunning Fog, Coleman-Liau)
  - Grammar & style analysis (error detection, passive voice, punctuation)
  - AI-specific patterns (perplexity, burstiness, predictability)
  - N-gram repetition and coherence scoring
- **Grammar Scoring**: Automated grammar analysis with detailed error reporting
- **Scalable Architecture**: Async processing with Redis queue and multiple ML workers
- **Fast Processing**: Optimized for quick turnaround on large documents
- **PDF Support**: Native PDF parsing and text extraction
- **Report Generation**: Detailed PDF reports with highlighted AI sections

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                  Django REST Framework API                   │
│                  - Authentication & Authorization            │
│                  - File Upload Management                    │
│                  - Job Queue Management                      │
└────────────────────────┬────────────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │    Redis Queue      │
              │   (Celery/RQ)       │
              └──────────┬──────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌────────▼────────┐
│  FastAPI ML     │            │  FastAPI ML     │
│  Worker 1       │            │  Worker 2       │
│  - PDF Parsing  │            │  - PDF Parsing  │
│  - Feature Ext  │            │  - Feature Ext  │
│  - ML Inference │            │  - ML Inference │
│  - Report Gen   │            │  - Report Gen   │
└─────────────────┘            └─────────────────┘
```

## 🤖 ML Models

### Ensemble Approach
- **Random Forest** (30% weight): Robust classification with 500 estimators
- **XGBoost** (30% weight): Gradient boosting for complex patterns
- **LightGBM** (25% weight): Fast and efficient tree-based learning
- **CatBoost** (15% weight): Categorical feature handling

### Optional Deep Learning
- **DistilBERT** (20% weight): Fine-tuned transformer for edge cases
- Used as fallback when feature-based confidence < 75%

## 🛠️ Tech Stack

### Backend Framework
- **Django REST Framework**: RESTful API development
- **FastAPI**: High-performance ML inference service
- **Celery/RQ**: Distributed task queue for async processing

### Machine Learning
- **scikit-learn**: ML model training and ensemble methods
- **XGBoost, LightGBM, CatBoost**: Gradient boosting frameworks
- **Transformers**: Optional deep learning models
- **NLTK, spaCy**: NLP and linguistic analysis
- **LanguageTool**: Grammar checking

### Data Processing
- **PyMuPDF (fitz)**: PDF parsing and text extraction
- **pdfplumber**: Advanced PDF table and layout extraction
- **pandas, numpy**: Data manipulation and numerical computing

### Infrastructure
- **PostgreSQL**: Primary database
- **Redis**: Caching and job queue
- **MinIO/S3**: File storage
- **Docker**: Containerization

## 📦 Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose (optional)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ai-detection-backend.git
cd ai-detection-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment configuration**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Database setup**
```bash
python manage.py migrate
python manage.py createsuperuser
```

6. **Download ML models**
```bash
python scripts/download_models.py
```

7. **Run services**
```bash
# Terminal 1 - Django API
python manage.py runserver

# Terminal 2 - Celery Worker
celery -A config worker -l info

# Terminal 3 - FastAPI ML Service
uvicorn ml_service.main:app --reload --port 8001
```

## 🐳 Docker Deployment
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📡 API Endpoints

### Authentication
```
POST   /api/auth/register          - User registration
POST   /api/auth/login             - User login
POST   /api/auth/logout            - User logout
```

### Document Analysis
```
POST   /api/submissions            - Upload document for analysis
GET    /api/submissions/{id}       - Get submission details
GET    /api/submissions/{id}/status - Check processing status
```

### Results
```
GET    /api/results/{id}           - Get analysis results
GET    /api/results/{id}/report    - Download detailed PDF report
```

### Admin
```
GET    /api/stats                  - System statistics
GET    /api/health                 - Health check
```

## 🔬 Feature Categories

### 1. Text Statistics (8 features)
- Word count, character count, sentence count
- Average sentence/word/paragraph length
- Text length variance

### 2. Linguistic Complexity (7 features)
- Lexical diversity, type-token ratio
- Hapax legomena ratio, long word ratio
- Syllable complexity, vocabulary sophistication
- Academic word ratio

### 3. Readability Metrics (5 features)
- Flesch Reading Ease, Flesch-Kincaid Grade
- Gunning Fog Index, Coleman-Liau Index
- Automated Readability Index

### 4. Grammar & Style (8 features)
- Grammar/spelling error counts
- Punctuation ratio, comma splices
- Passive voice ratio, sentence fragments
- Run-on sentences, subject-verb agreement

### 5. AI Detection Patterns (10+ features)
- Predictability score, burstiness
- Perplexity, n-gram repetition
- Transition word frequency, hedge words
- Sentence starter diversity, coherence
- Stylistic consistency, unnatural word order

### 6. Sentiment & Tone (3 features)
- Sentiment polarity, subjectivity
- Emotional variability

## 📊 Response Format

### Analysis Result
```json
{
  "submission_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "results": {
    "ai_percentage": 45.5,
    "human_percentage": 54.5,
    "grammar_score": 72.0,
    "total_paragraphs": 25,
    "ai_paragraphs": 11,
    "flagged_paragraphs": [2, 4, 7, 9, 12, 15, 18, 20, 22, 24, 25],
    "processing_time": 6.8
  },
  "report_url": "/api/results/123e4567/report"
}
```

### Paragraph-Level Detail
```json
{
  "paragraph_number": 2,
  "text": "Artificial intelligence has revolutionized...",
  "ai_probability": 0.89,
  "is_flagged": true,
  "confidence": 0.94,
  "features": {
    "predictability_score": 0.92,
    "burstiness": 0.15,
    "grammar_errors": 0,
    "lexical_diversity": 0.45
  }
}
```

## 🧪 Testing
```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report

# ML model tests
pytest tests/ml/

# API endpoint tests
pytest tests/api/
```

## 🚀 Performance Optimization

- **Parallel Processing**: Multiprocessing for feature extraction
- **Model Caching**: Pre-loaded models in memory
- **Redis Caching**: Frequent query results cached
- **Batch Inference**: Process multiple paragraphs simultaneously
- **Async I/O**: FastAPI async endpoints for non-blocking operations
- **Connection Pooling**: Database connection reuse

## 📈 Monitoring

- **Health Checks**: `/api/health` endpoint for service monitoring
- **Metrics**: Processing time, queue length, error rates
- **Logging**: Structured logging with rotation
- **Performance**: Request/response time tracking

## 🔒 Security

- JWT-based authentication
- Rate limiting on API endpoints
- File type validation and size limits
- SQL injection prevention (Django ORM)
- CORS configuration
- Environment-based secrets management

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📧 Contact

For questions or support, please contact [your-email@example.com](mailto:your-email@example.com)

## 🙏 Acknowledgments

- Dataset sources and contributors
- Open-source ML libraries and frameworks
- Academic research on AI text detection