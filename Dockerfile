# Stage 1: Build Frontend
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Setup Backend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt ./

# Install dependencies
# Use --extra-index-url to prefer CPU versions of PyTorch if available
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Remove build dependencies to save space
RUN apt-get remove -y build-essential && \
    apt-get autoremove -y && \
    apt-get clean
    
RUN pip install gunicorn

# Copy backend code
COPY backend/ /app/backend

# Copy built frontend assets to backend/static
COPY --from=frontend-build /app/frontend/dist /app/backend/static

# Set environment variables
ENV FLASK_APP=simple_app.py
ENV FLASK_ENV=production
ENV PORT=5000
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend

# Expose port
EXPOSE 5000

# Set working directory to backend
WORKDIR /app/backend

# Run the application
CMD ["gunicorn", "simple_app:app", "-b", "0.0.0.0:5000", "--timeout", "120"]
