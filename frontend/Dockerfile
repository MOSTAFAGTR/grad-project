FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the code
COPY . .

# Add node_modules/.bin to the PATH explicitly
ENV PATH /app/node_modules/.bin:$PATH

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]