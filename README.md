# MathQuest Backend API

This is the backend API for the MathQuest application, built with Flask and deployed on Vercel.

## Features

- RESTful API endpoints for lessons and problem management
- User streak tracking
- Problem submission and validation
- PostgreSQL database integration
- Alembic database migrations

## Tech Stack

- **Framework**: Flask
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Deployment**: Vercel

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL database
- pip

### Setup

1. **Clone the repository**:
   ```bash
   git clone <your-backend-repo-url>
   cd mathquest-backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/mathquest
   APP_SECRET_KEY=your-secret-key-here
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start the development server**:
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:5001`

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/lessons` - Get all lessons
- `GET /api/lessons/{id}` - Get specific lesson
- `POST /api/submit` - Submit problem solution
- `GET /api/streak` - Get user streak
- `POST /api/streak` - Update user streak

## Database

The application uses PostgreSQL with the following main tables:
- `lessons` - Lesson information
- `problems` - Math problems
- `user_streaks` - User streak tracking

## Deployment on Vercel

### Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI** (optional): `npm i -g vercel`

### Deployment Steps

1. **Connect to Vercel**:
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Environment Variables**:
   In Vercel dashboard, add these environment variables:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `APP_SECRET_KEY`: A secure secret key

3. **Deploy**:
   Vercel will automatically deploy on every push to main branch

### Environment Variables

Required environment variables for production:

- `DATABASE_URL`: PostgreSQL connection string
- `APP_SECRET_KEY`: Secret key for Flask app

## Database Setup

### Option 1: Vercel Postgres (Recommended)

1. In Vercel dashboard, go to your project
2. Click "Storage" → "Create Database"
3. Select "Postgres"
4. Vercel will automatically set the `DATABASE_URL` environment variable

### Option 2: External Database

Use any PostgreSQL provider (Supabase, AWS RDS, etc.) and set the `DATABASE_URL` environment variable.

## Testing

Run tests with pytest:

```bash
pytest
```

## Project Structure

```
backend/
├── alembic/           # Database migrations
├── api/              # API routes
├── src/              # Source code
│   ├── models.py     # Database models
│   ├── routes.py     # API routes
│   └── services/     # Business logic
├── tests/            # Test files
├── app.py            # Main application
├── requirements.txt  # Python dependencies
└── vercel.json       # Vercel configuration
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License
