FROM node:18

WORKDIR /app

# Copy only package manifests first to leverage docker cache
COPY package*.json ./

# Install dependencies inside the image (prefer npm ci if lockfile present)
RUN npm ci --silent || npm install --silent

# Ensure node_modules exists and set ownership to the non-root 'node' user
RUN mkdir -p /app/node_modules && chown -R node:node /app

# Copy application files as the node user to preserve ownership
COPY --chown=node:node . .

# Switch to the non-root user
USER node

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]