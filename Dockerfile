FROM node:18-bullseye

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

RUN npx astro sync

EXPOSE 4444
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "4444"]
