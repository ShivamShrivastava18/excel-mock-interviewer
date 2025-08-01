#!/bin/bash

# Start the Next.js frontend
echo "Starting Excel Skills Assessment Frontend..."

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install --force
fi

# Set backend URL for development
export NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Start the development server
echo "Starting Next.js development server on http://localhost:3000"
npm run dev
