# CDC Data Architecture with OpenSource and Microsoft Fabric
*Real-time data Capturing*

# Introduction
As billions of data gets generated daily and having a robust system that can manage such an influx of data is of high importance. With OpenSource technology achieving such a process is possible but the question arises how can this be done also on an enterprise level for business users?
# Project Requirement
In company XYZ Limited your AppDev(Software Department) currently has a web application that sends to a PostgreSQL Database via a Connection String. As a senior data engineer for XYZ Limited, you have been tasked to create a CDC approach to connect to Azure PostgreSQL and capture the data in real life as they get inserted into the database and then stored in a NoSQL Database which will be Elasticsearch.

The Analytic Department uses Microsoft Power BI for reporting, and you also want to capture the same data of CDC in Microsoft using the Microsoft Fabric component available. The architecture below explains the entire process and what we aim to achieve.

👉🏽 Image

# Project Sections
This project will be divided into several sections to aid readers in understanding.

●	**Section 1:** Provisioning the necessary resources in Azure using Azure CLI

●	**Section 2:** Setting up Docker-compose.yml file for CDC streaming process.

●	**Section 3:** Setting up the CDC streaming process in Microsoft Fabric.

●	**Section 4:** Setting up a RAG model in Fabric Notebook using Open API Key and Tokens.

## Prerequisite
To follow along with this project the following requirements are needed
●	Basic Python Knowledge

●	Docker Desktop Installed

●	Azure Subscription

●	Microsoft Account with Fabric Enabled

●	VSCode or any preferred IDE

●	Be Open Minded 😊

# Section 1: Provisioning Resources with Azure CLI
## What is Azure CLI
This is a command-line interface (CLI) tool that lets you control Azure resources. It is an effective tool that allows you to use your terminal or command prompt to automate processes and script and communicate with Azure services.

## Provision Azure Storage Account Using Azure CLI
The following step should be followed to create a data lake gen 2 using the Azure CLI environment.

### Step 1: Login and Select Azure Account
After successfully logging in to Azure you should get the following subscription information.

👉🏽 Image

### Step 2: Create Resource Group
In Azure, similar resources are logically contained under resource groups. It's a method for jointly managing and organizing your Azure resources. Consider it as a directory or folder where you can organize and store resources with similar lifecycles or purposes.

First, let's start by selecting the subscription ID in your Azure Portal, selecting the subscription, and picking the copy of the subscription ID information.

👉🏽👉🏽

With the subscription id head to your Azure CLI and put in the following information.
```
az account set --subscription "YourSubscriptionId"
```

Now that we have our subscription select use the command below to create a new resource group.

```
az group create --name YourResourceGroupName --location YourLocation
```

👉🏽👉🏽

### Step 3: Create a Storage Account
The below CLI command will be used in creating a Data Lake Gen 2 storage account in Azure with the necessary formations.

```
az storage account create --name YourStorageAccountName --resource-group YourResourceGroupName --location YourLocation --sku Standard_LRS --kind StorageV2 --hierarchical-namespace true
```

After successfully creating the storage account we need to create a file system that is analogous to a container. Consider your data as a high-level organizational structure contained within a storage account when managing and organizing it.

```
az storage fs create --name YourFileSystemName --account-name YourStorageAccountName
```

## Step 4: Set Service Principal in Azure Contain
We may establish a service principle that will have access to the Azure Data Lake Gen and be able to obtain the required credentials, including Client ID, Tenant ID, and Client Secret, by using the Azure CLI.

👉🏽👉🏽 

### Set Permission
We must grant the following permission to the built app to have access to Azure Storage after obtaining the required credentials.

We are required to support the Storage Blob Data Contributor role for the service primary app. This will enable you to read, write, and remove blob data from Azure storage with the required permissions.

```
# Assign the Storage Blob Data Contributor role to the service principal
az role assignment create --assignee <client-id> --role "Storage Blob Data Contributor" --scope "/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.Storage/storageAccounts/<account-name>"
```

### Step 5: Create PostgreSQL with WAL (Write Ahead Logging)
We need to activate the CDC features in Azure PostgreSQL to achieve this when provisioning Azure PostgreSQL we need to consider the WAL property.

A PostgreSQL feature called WAL (Write-Ahead Logging) records database modifications before they are made, guaranteeing data consistency and durability.
The quantity of data that is written to the WAL is determined by the wal_level parameter in PostgreSQL, which has various levels for WAL.

In the database there are two types of WAL we can choose from:
●	**replica:** The default WAL setting is adequate for physical replication but insufficient for logical replication.
●	**Logical:** This layer offers more thorough WAL data, facilitating logical replication—a prerequisite for change data capture (CDC) systems like Debezium or row-level change tracking systems like Airflow used for event streaming or replication.

### Set Variables in Azure CLI
We need to set the following Variables in our command prompt which will be used for setting up the necessary infrastructure. 

```
set RESOURCE_GROUP=docker_rg
set SERVER_NAME=postgreflexibleserver
set LOCATION=centralus
set ADMIN_USER=xxxxxxxxxxxxxxxx
set ADMIN_PASSWORD=xxxxxxxxxxxxxxxxxx
set SKU=Standard_B1ms
set STORAGE_SIZE=32
set VERSION=13
set DATABASE_NAME=xxxxxxxxxxxxxxxxx
```

### Create a PostgreSQL Flexible Server
Use the command below to create a flexible server in Azure PostgreSQL that will be needed for our CDC functionality.

```
az postgres flexible-server create ^
    --resource-group %RESOURCE_GROUP% ^
    --name %SERVER_NAME% ^
    --location %LOCATION% ^
    --admin-user %ADMIN_USER% ^
    --admin-password %ADMIN_PASSWORD% ^
    --sku-name %SKU% ^
    --storage-size %STORAGE_SIZE% ^
    --version %VERSION%
```
### Configure wal_level
Using the command to configure the server to logical which supports CDC in the PostgreSQL Database.

```
az postgres flexible-server parameter set ^
    --resource-group %RESOURCE_GROUP% ^
    --server-name %SERVER_NAME% ^
    --name wal_level ^
    --value logical
```

### Create a firewall rule to allow connections (Optional)
For development purposes, I would enable the developer to access the database server just for development purposes.

```
az postgres flexible-server firewall-rule create ^
    --resource-group %RESOURCE_GROUP% ^
    --name %SERVER_NAME% ^  
    --rule-name AllowAllIPs ^  
    --start-ip-address 0.0.0.0 ^
    --end-ip-address 255.255.255.255
```

### Display the connection string
This command below is used to generate the connection string if needed for connecting to a 3rd party application.

```
az postgres flexible-server show-connection-string --server-name %SERVER_NAME%
```

### Create the PostgreSQL database
Use this command to create a database in the PostgreSQL Server.

```
az postgres flexible-server db create ^
    --resource-group %RESOURCE_GROUP% ^
    --server-name %SERVER_NAME% ^
    --database-name %DATABASE_NAME%
```

### Privileges
Superuser Privileges: Ensure that the PostgreSQL user you’re using for Debezium has the SUPERUSER privilege. Alternatively, the user must have the REPLICATION role.
```
ALTER USER temidayo WITH REPLICATION;
```
# Section 2: Setting up Docker-compose.yml file for the CDC streaming process
Now that we have successfully provisioned all the necessary resources let's get started by setting up the environment needed for the process.

## Create a Virtual Environment in Python
In Python, a virtual environment is a segregated setting where you can install and maintain packages apart from your system-wide installation. This lessens the likelihood of conflicts arising from several projects requiring various versions of the same package.

The command below is used in creating a folder in Python needed for our project.
👉🏽👉🏽 

Create a virtual Python environment with the command below, this will create a subfolder in our project directory.
```
python -m venv fabric_env
```

Once the virtual environment is created you need to activate it with this command below.
```
fabric_env\Scripts\activate
```

👉🏽👉🏽 

## Create Docker-Compose.yml File for Project
We need to set up all the necessary resources for the project by creating a docker file that has a container that houses all our images.

Multiple Docker containers can be defined and configured as a single application using a Docker Compose file, which is a YAML file. It enables you to control and plan the start, stop, and start-up of numerous connected containers.

Create a new file called docker-compose.yml in your project folder and put in the following command.
👉🏽👉🏽👉🏽 

👉🏽 **Click:** [Docker-compose.yml](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/docker-compose.yml)

### Docker-compose.yml Breakdown

**Elasticsearch**

●	Image: Uses the official Elasticsearch image version 7.17.9.

●	Environment Variables:

    ○	discovery.type=single-node: Configures Elasticsearch to run in single-node mode, suitable for development.
    
    ○	ES_JAVA_OPTS=-Xms512m -Xmx512m: Sets Java heap size to 512 MB for both minimum and maximum.
    
●	Ports: Exposes ports 9200 (HTTP) and 9300 (transport).

●	Networks: Connects to app-network.

**Kibana**

●	Image: Uses the official Kibana image version 7.17.9.

●	Environment Variables:

    ○	ELASTICSEARCH_HOSTS=http://elasticsearch:9200: Configures Kibana to connect to the Elasticsearch service.
    
●	Ports: Exposes port 5601 for accessing Kibana's web interface.

●	Depends On: Ensures that Elasticsearch starts before Kibana.

●	Networks: Connects to app-network.

**Zookeeper**

●	Image: Uses the latest Wurstmeister Zookeeper image.

●	Ports: Exposes port 2181, which is used by Kafka for coordination.

●	Networks: Connects to app-network.

**Kafka**

●	Image: Uses the latest Wurstmeister Kafka image.

●	Ports:

    ○	9092: Internal listener for Kafka.
    
    ○	9093: External listener for clients connecting from outside the Docker network.
    
●	Environment Variables:

    ○	Configures listeners and security protocols for internal and external communication.
    
    ○	Connects to Zookeeper at zookeeper:2181.
    ○	Creates a default topic named debezium-topic with 3 partitions and 1 replica.
    
●	Depends On: Ensures Zookeeper starts before Kafka.

●	Networks: Connects to app-network.

**Debezium**

●	Image: Uses the Debezium connector image version 2.2.

●	Hostname and Container Name: Set to "debezium".

●	Ports: Exposes port 8083 for the Debezium REST API.

●	Environment Variables:

    ○	Configures connection settings for Kafka and storage topics for connector configurations and offsets.
    
    ○	Specifies JSON converters for key and value serialization.
    
●	Depends On: Requires Kafka and Elasticsearch to start first.

●	Healthcheck: Checks if the Debezium service is healthy by querying its connectors endpoint.

●	Networks: Connects to app-network.

**Debezium UI**

●	Image: Uses the Debezium UI image version 2.2.

●	Ports: Exposes port 8080 for accessing the Debezium UI web interface.

●	Environment Variables:

    ○	Specifies the URI of the Debezium service for configuration access.
    
●	Depends On: Waits until the Debezium service is healthy before starting.

●	Networks: Connects to app-network.

**Networks**

By using the bridge driver to define a single network called app-network, all services can communicate with one another.

### Start Docker
To start our docker-compose.yml file we are going to use the command below to achieve this. The process might take a couple of minutes depending on your internet connection.

```
docker-compose up -d
```

## Create a Producer App
The producer will be used to send real-time data to the Azure PostgreSQL database. The idea around this scenario is that if transactions happen in the database it is inserted realtime into the PostgreSQL database.

⚠️**Disclaimer:** Due to the fact we cannot get a working application, we would create a scenario for a real-time producer app using Python Script.

### Step 1: Install Necessary Libraries
Create a requirements.txt file in the same project folder to install all necessary libraries. These are the libraries that would be needed for the project.

👉🏽👉🏽 

### Step 2: Create a Producer Script
With docker up and running we need to create a Producer script that will be picking data from a website, converting it to a dataframe, and inserting it into a PostgreSQL database table called user_data.

👉🏽 **Click:** [Producer Script](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/producer.py)

### Step 3: Test Producer Script
After successfully creating the script let's test it by running it on our VSCode with the line of code below.

👉🏽👉🏽👉🏽

From the image, you would notice data are being inserted into our PostgreSQL Database.

👉🏽👉🏽👉🏽 

## Setup CDC with Debezium
Debezium is an open-source distributed platform for Change Data Capture. Its purpose is to record changes in databases at the row level and transmit these changes as events. Applications can now respond in real-time to changes in data, opening a variety of use cases, including:

●	Data synchronization between databases or systems is known as data replication.

●	Event-driven architectures: Activating programs in response to modifications in a database.

●	Data warehousing: Adding new data to data warehouses.

●	Analyzing data as it changes is known as real-time analytics.

**Key attributes and advantages of Debezium:**

●	Real-time data streaming: Sends updates to Kafka topics in real-time as they happen. 

●	Durability: Makes sure that, even in the event of failures, no data is lost. 

●	Scalability: Able to manage numerous databases and substantial data volumes. 

●	Flexibility: Supports several different databases, such as Oracle, PostgreSQL, MySQL, and others. 

●	Integration with Kafka: Makes use of Kafka's capabilities for streaming and distributed processing.

### Step 1: Create New Connection
Ensure your Docker Desktop is still running then perform the following connection. Open your browser and enter the url http://localhost:8080/ which is the debezium UI URL.

👉🏽👉🏽👉🏽 

In the new window select the database we want to use to perform CDC. We will be using PostgreSQL for our project.

👉🏽👉🏽 

In the connection setting you’re expected to fill in the necessary credentials for the PostgreSQL Server.

👉🏽👉🏽👉🏽👉🏽 

Change the Replication to pgoutput then click on Validation to test and validate our connection.

👉🏽👉🏽👉🏽 

👉🏽👉🏽👉🏽👉🏽 

At the end of the connection, you should get debezium running and capturing data real-time from PostgreSQL

👉🏽👉🏽👉🏽 

## Setup Kafka Topic
Now that our debezium is up and running as expected we need to set Kafka topic which will be used in receiving the data from debezium.

**Note:** By default Debezium would create a Kafka topic for use from which to read the data.

### View Kafka Topic
Using the command below in our VSCode terminal we can list all available topics in Kafka broker.

```
docker-compose exec kafka kafka-topics.sh --list --bootstrap-server kafka:9092
```

👉🏽👉🏽👉🏽 

With the command we can locate the topic the data is being sent to in Kafka topic which is deb_conn.fabric.user_data.

### Consumer Kafka Topic

Using the command below to consume data realtime from Kafka topic in our terminal.

```
docker-compose exec kafka kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic deb_conn.fabric.user_data --from-beginning
```

👉🏽👉🏽👉🏽 

The image below shows that we can consume data from Kafka Topic that is being sent by debezium in realtime.

## Create a Consumer Script to ElasticSearch

Before creating consumer script we first need to create an Index in ElasticSearch that will be used in storing the data and querying it. In your Terminal open WSL - Window Subsystem for Linux which will be used in creating the Index with the datatype mappings.

```
curl -X PUT "http://localhost:9200/user_data_index_new" -H "Content-Type: application/json" -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "id": {
        "type": "integer"
      },
      "name": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "gender": {
        "type": "keyword"
      },
      "address": {
        "type": "text"
      },
      "latitude": {
        "type": "double"
      },
      "longitude": {
        "type": "double"
      },
      "timezone": {
        "type": "keyword"
      },
      "email": {
        "type": "keyword"
      },
      "phone": {
        "type": "keyword"
      },
      "cell": {
        "type": "keyword"
      },
      "date_of_birth": {
        "type": "date"
      },
      "registered_date": {
        "type": "date"
      },
      "picture_url": {
        "type": "keyword"
      },
      "insertion_time": {
        "type": "date"
      }
    }
  }
}'
```

👉🏽👉🏽👉🏽 

You will notice a new index has been created in ElasticSearch called user_data_index.

👉🏽👉🏽👉🏽 

You can use the command below to confirm the ElasticSearch Index Created.
```
curl -X GET -x "" "localhost:9200/user_data_index_new?pretty"
```

### Consumer Script
Use the code below to create a consumer script and insert data into ElasticSearch Index created.

👉🏽 **Click:** [Consumer Script ElasticSearch](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/consume_elasticsearch.py)








