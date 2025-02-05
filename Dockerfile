FROM node:18-alpine

WORKDIR /app

# Copy package.json
COPY package.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Set proper permissions
RUN chown -R node:node /app

# Switch to non-root user
USER node

EXPOSE 4444

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "4444"]
