# Quick Fix for Docker Network Issues

## Steps to Resolve TLS Handshake Timeout:

1. **Open Docker Desktop**
2. Click the **Settings (gear icon)**
3. Go to **Docker Engine**
4. Replace the entire configuration with:

```json
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "dns": ["8.8.8.8", "8.8.4.4"],
  "experimental": false
}
```

5. Click **Apply & Restart**
6. Wait for Docker to restart completely
7. Try running: `docker-compose up --build` again

## Alternative: Pull Images Manually

If the above doesn't work, pull images one by one:

```powershell
docker pull node:18-alpine
docker pull python:3.9
docker pull mysql:8.0
```

Then try `docker-compose up --build` again.
