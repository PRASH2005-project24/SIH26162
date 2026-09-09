# ============================================================================
# Dockerfile for SIH26162 Frontend
# React + TypeScript development server
# ============================================================================

FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* yarn.lock* ./

# Install dependencies
RUN npm ci || npm install

# Copy frontend code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "start"]
