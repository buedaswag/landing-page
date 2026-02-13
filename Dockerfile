FROM node:22-alpine

WORKDIR /app

# Copy package.json
COPY package.json ./

# Install dependencies
RUN npm install

# Set proper permissions for the app directory
RUN chown -R node:node /app

# Switch to non-root user
USER node

# Copy the rest of the application
COPY --chown=node:node . .

EXPOSE 4444

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "4444"]
