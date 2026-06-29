FROM node:18-alpine

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Set work directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production --legacy-peer-deps || npm install --production --legacy-peer-deps

# Copy project files
COPY . .

# Build next.js app
RUN npm run build

# Expose port
EXPOSE 3000

# Start development or production server
CMD ["npm", "run", "start"]
