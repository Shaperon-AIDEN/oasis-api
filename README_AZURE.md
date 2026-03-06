# Azure OASis API Deployment Guide

This folder contains a standalone, lightweight FastAPI server to serve the 22GB OASis SQLite database over REST API.

## Requirements
- Docker
- Azure CLI
- Azure Container Registry (or Docker Hub)
- Azure App Service (Azure Web App for Containers)
- Optional: Azure Files (to mount the 22GB DB without building it into the docker image)

## Local Testing
1. Download the OASis database and place it in the same directory (or point `OASIS_DB_PATH` to it).
2. Build Image:
   ```bash
   docker build -t oasis-api .
   ```
3. Run Container:
   ```bash
   docker run -p 8080:80 -v /path/to/downloaded/db/:/app/data \
      -e OASIS_DB_PATH=/app/data/OASis_9mers_v1.db oasis-api
   ```
4. Check Health: `http://localhost:8080/health`

## Azure Deployment
Because the OASis DB is 22GB, it is highly recommended **NOT** to copy it into the Docker image directly. Instead, mount it as an Azure Storage claim.

1. Create Azure Storage Account, and create a File Share named `oasis-data`.
2. Upload `OASis_9mers_v1.db` to the Azure File Share (`oasis-data`).
3. Build and push this Docker image to Azure Container Registry (ACR).
4. Create an **Azure Web App for Containers**.
5. Under Configuration -> Path mappings, mount the Azure File Share to `/app/data` in the container.
6. Set the Environment Variable: `OASIS_DB_PATH=/app/data/OASis_9mers_v1.db` in App Service configuration.
7. Start the App Service.

## API Usage

**Endpoint:** `POST /api/peptides/`

**Request Body:**
```json
{
  "peptides": ["QVQLVQSGA", "SGAEVKKPG"],
  "filter_chain": "Heavy" 
}
```

**Response:**
```json
{
  "num_total_oas_subjects": 12500,
  "hits": [
    ... matching rows from db ...
  ]
}
```
