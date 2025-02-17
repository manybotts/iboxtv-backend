# Backend for iBOX TV

This is the backend service for the iBOX TV application, implemented using FastAPI and PostgreSQL. 

## Deployment

To deploy this backend, you can use Docker or any compatible cloud service that supports Python and FastAPI.

### Building with Docker

1. Build the Docker image:
   ```bash
   docker build -t ibox-tv-backend .
2.Run the Docker container:
   docker run -p 8000:8000 ibox-tv-backend
   
This backend exposes several endpoints to interact with the iBOX TV database, such as fetching new shows, listing all shows, and checking the stream status of individual shows.
