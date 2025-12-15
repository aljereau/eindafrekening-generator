FROM node:22-alpine

WORKDIR /app

# Copy package.json and lock file
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose Vite default port
EXPOSE 5173

# Run in development mode exposed to host
CMD ["npm", "run", "dev", "--", "--host"]
