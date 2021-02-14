## Build the Docker image for FastAPI (backend)

* Go to the backend directory.

* Run the following command to build the FastAPI image:
`docker build -t fastapi-image:v1 .`

* You can confirm that this has worked by running the command:
`docker images`

# Start the Docker container

* Run a container based on the image:
`docker run -d --name backend-container -p 8081:8081 fastapi-image:v1`


## Build the Docker Image for the HTML Server (frontend)

* Go to the frontend directory.

* Run the following command to build the server image:
`docker build -t html-server-image:v1 .`

* You can confirm that this has worked by running the command:
`docker images`

# Start the Docker container

* Run the following command to run the HTML container server:
`docker run -d --name frontend-container -p 80:80 html-server-image:v1`