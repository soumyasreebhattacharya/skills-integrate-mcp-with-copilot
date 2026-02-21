# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Data persists across app restarts using SQLite

## Getting Started

1. Install the dependencies:

   ```
   pip install -r ../requirements.txt
   ```

2. Run the application:

   ```
   uvicorn app:app --reload
   ```

## Database-backed mode

The API now uses a relational SQLite database by default.

- Default DB file: `src/activities.db`
- Override location with `DATABASE_PATH`, for example:

  ```
  DATABASE_PATH=./school.db uvicorn app:app --reload
  ```

On first startup, the app creates the schema and seeds initial activity/student/registration data.

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities**:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - Linked registrations

2. **Students**:
   - Email

3. **Registrations**:
   - Activity-to-student relationship records

Data is persisted in SQLite and survives server restarts.
