# Data Engineering Pipeline with Docker Compose

This project demonstrates how to set up a Data Engineering pipeline using Docker Compose. The pipeline integrates Airflow, Kafka, and the ELK stack (Elasticsearch, Logstash, and Kibana) to simulate, process, and visualize sensor data.

## Project Overview

- **Airflow**: Orchestrates and manages workflows.
- **Kafka**: Handles real-time data streaming.
- **Elasticsearch**: Stores and indexes data.
- **Kibana**: Provides visualization and exploration of data.

## Architecture
![alt text](image.png)


## Detailed Instructions
Medium Post: https://medium.com/p/336d5728ccf1/


## Setup Instructions

1. **Clone the Repository**

    ```bash
    git clone https://github.com/PrabakarSundar/Data-Engineering-Pipeline-Using-Kafka-Airflow-ELK.git
    cd Data-Engineering-Pipeline-Using-Kafka-Airflow-ELK
    ```
2. **Install Docker and Docker Compose**

    Follow the official [Docker documentation](https://docs.docker.com/engine/install/) for installation. After installing Docker, complete the [post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/) and add Docker to the admin group.

    Check docker using the command,
    
        docker ps

3. **Start the Services**

    Use Docker Compose to start the services:

    Move into each folders and start all services using the command 
    
        cd kafka
        docker compose up -d

        cd airflow
        docker compose up -d

        cd elk
        docker compose up -d
    
    This command will pull the necessary Docker images, build them, and create the containers for Airflow, Kafka, and ELK.

4. **Access Kafka Control Center**

    Once the Kafka containers are up and running, access the Kafka Control Center at http://localhost:9021. Here, you can view and manage Kafka topics.


5. **Configure Airflow**

    Once the Airflow containers are up and running, access the Airflow Web UI at http://localhost:8080.

    Sign in to Airflow using ```username: airflow, password: airflow```

    You should see two DAGs listed. These DAGs are initially paused.
    Unpause the DAGs from the Airflow UI. 

    **Producer DAG**
    Producer DAG will be triggered automatically based on the 5 mins scheduled interval.
    
    **Consumer DAG**
    Consumer DAG should be triggered manually as it is set to run @yearly
    

6. **Create Data Views in Kibana**

    Once the elk containers are up and running,

    Access Elasticsearch at http://localhost:9200 and Kibana at http://localhost:5601

    Sign in to Kibana using ```username: elastic, password: changeme```

    Navigate to Kibana -> Stack Management -> Index Management to verify the sensor_data index.
    Create a data view by going to Kibana -> Data Views.
    Click Create Data View, set sensor_data as the name and index pattern, and choose Timestamp as the timestamp field.

7. **Visualize Data**

    Create a Kibana dashboard to visualize the data. The dashboard creation process is not covered here, but a pre-configured dashboard is provided.

8. **Import Pre-configured Dashboard**

    You can find the dashboard saved object sensor_data.ndjson in the repository.
    Upload this file in Kibana to quickly set up the visualizations.
