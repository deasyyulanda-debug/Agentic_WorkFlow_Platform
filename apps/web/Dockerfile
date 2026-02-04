FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci || npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Development command (overridden in docker-compose)
CMD ["npm", "run", "dev"]
