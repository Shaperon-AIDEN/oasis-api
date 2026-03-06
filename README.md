# OASis REST API Server

This repository contains a standalone, lightweight FastAPI server to serve the **OASis (Observed Antibody Space) database** over a REST API. It is designed to decouple the 22GB SQLite database dependency from the core BioPhi agent skill, allowing AI agents to query humanness scores and peptides dynamically.

## 🚀 Features
- **FastAPI Backend**: Built with Python and FastAPI for high-performance async processing (although using `sqlite3` natively for robust data binding).
- **Lightweight**: No Flask, Celery, or Redis dependencies. Purely focuses on API serving.
- **Azure CI/CD Integration**: Fully integrated with Azure App Service (Containers) and Azure Container Registry (ACR) via Webhooks.

---

## 📖 API Specification

### 1. Health Check
Determine if the API server is alive and running.

- **Endpoint**: `GET /health`
- **Response**: `200 OK`
  ```json
  {"status": "ok"}
  ```

### 2. Peptide Lookup
Query the 22GB OASis database for specific 9-mer peptides to retrieve their occurrences across subjects.

- **Endpoint**: `POST /api/peptides/`
- **Headers**:
  - `Content-Type: application/json`
- **Request Body Parameters**:
  - `peptides` (List[str], Required): A list of 9-mer peptide strings to search for.
  - `filter_chain` (str, Optional): Filter by chain type (`"Heavy"` or `"Light"`).

**Example Request**:
```bash
curl -X POST "https://biophioasisapi.azurewebsites.net/api/peptides/" \
     -H "Content-Type: application/json" \
     -d '{
           "peptides": ["QVQLQQSGA", "ELVRPGASV"],
           "filter_chain": "Heavy"
         }'
```

**Example Response**:
```json
{
  "num_total_oas_subjects": 12500,
  "hits": [
    {
      "peptide": "QVQLQQSGA",
      "subject": 209,
      "count": 125
    },
    {
      "peptide": "ELVRPGASV",
      "subject": 197,
      "count": 4
    }
  ]
}
```
- `num_total_oas_subjects`: The total number of valid subjects in the local OASis database (used for calculating humanness scores in the BioPhi core).
- `hits`: Array of objects detailing the occurrences of the requested peptides across different dataset subjects.

---

## 🏗️ Architecture & Deployment (Azure)

Because the OASis DB is 22GB in size, the database itself is **not** bundled into the Docker Image. Instead, it is mounted securely via Azure Storage File Shares.

### CI/CD Workflow
1. **GitHub Actions**: When code is pushed to the `main` branch, a GitHub Action automatically builds the Docker image and pushes it to Azure Container Registry (ACR: `shaperon.azurecr.io`).
2. **ACR Webhook**: The ACR is configured with a Webhook that notifies the Azure App Service.
3. **App Service**: The App Service (`biophioasisapi`) pulls the latest image and restarts automatically. The 22GB database remains safely mounted on `/app/data/OASis_9mers_v1.db`.

### Local Development
To run this API server locally for testing:
1. Ensure you have downloaded `OASis_9mers_v1.db` to your machine.
2. Build and run the docker container, mounting the DB path:
   ```bash
   docker build -t oasis-api-local .
   docker run -p 8080:80 \
      -v /absolute/path/to/your/db/dir:/app/data \
      -e OASIS_DB_PATH=/app/data/OASis_9mers_v1.db \
      oasis-api-local
   ```
3. The API will be available at `http://localhost:8080`.
