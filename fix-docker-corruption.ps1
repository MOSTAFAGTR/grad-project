# Fix Docker Image Corruption
# Run this script to clean up corrupted Docker images and rebuild

Write-Host "Stopping all containers..." -ForegroundColor Yellow
docker-compose down

Write-Host "`nRemoving corrupted backend image..." -ForegroundColor Yellow
docker rmi grad-project-backend -f

Write-Host "`nPruning Docker system (removing unused data)..." -ForegroundColor Yellow
docker system prune -a -f

Write-Host "`nCleaning build cache..." -ForegroundColor Yellow
docker builder prune -a -f

Write-Host "`nRebuilding from scratch..." -ForegroundColor Green
docker-compose build --no-cache

Write-Host "`nStarting services..." -ForegroundColor Green
docker-compose up
