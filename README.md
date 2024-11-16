# CDC Data Architecture with OpenSource and Microsoft Fabric

📽️ [Watch Full Video of Project](https://youtu.be/pD1wFoxFszQ)

*Real-time data Capturing*

# Introduction
As billions of data gets generated daily and having a robust system that can manage such an influx of data is of high importance. With OpenSource technology achieving such a process is possible but the question arises how can this be done also on an enterprise level for business users?
# Project Requirement
In company XYZ Limited your AppDev(Software Department) currently has a web application that sends to a PostgreSQL Database via a Connection String. As a senior data engineer for XYZ Limited, you have been tasked to create a CDC approach to connect to Azure PostgreSQL and capture the data in real life as they get inserted into the database and then stored in a NoSQL Database which will be Elasticsearch.

The Analytic Department uses Microsoft Power BI for reporting, and you also want to capture the same data of CDC in Microsoft using the Microsoft Fabric component available. The architecture below explains the entire process and what we aim to achieve.

![Architecture](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/archiecture.png)

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

![Account_Login_CLI](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/2.png)

### Step 2: Create Resource Group
In Azure, similar resources are logically contained under resource groups. It's a method for jointly managing and organizing your Azure resources. Consider it as a directory or folder where you can organize and store resources with similar lifecycles or purposes.

First, let's start by selecting the subscription ID in your Azure Portal, selecting the subscription, and picking the copy of the subscription ID information.

![Subscription_ID](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/3.png)

With the subscription id head to your Azure CLI and put in the following information.
```
az account set --subscription "YourSubscriptionId"
```

Now that we have our subscription select use the command below to create a new resource group.

```
az group create --name YourResourceGroupName --location YourLocation
```

![Create_Resource_Group](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/4.png)

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

![Service_Principal](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/5.png)

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
set SKU=Standard_D4ds_v4
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
![Virtual_Env](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/6.png)

Create a virtual Python environment with the command below, this will create a subfolder in our project directory.
```
python -m venv fabric_env
```

Once the virtual environment is created you need to activate it with this command below.
```
fabric_env\Scripts\activate
```

![activate_env](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/7.png)

## Create Docker-Compose.yml File for Project
We need to set up all the necessary resources for the project by creating a docker file that has a container that houses all our images.

Multiple Docker containers can be defined and configured as a single application using a Docker Compose file, which is a YAML file. It enables you to control and plan the start, stop, and start-up of numerous connected containers.

Create a new file called docker-compose.yml in your project folder and put in the following command.
![docker-compose.yml](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/8.png)

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

![libraries](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/9.png)


### Step 2: Create a Producer Script
With docker up and running we need to create a Producer script that will be picking data from a website, converting it to a dataframe, and inserting it into a PostgreSQL database table called user_data.

👉🏽 **Click:** [Producer Script](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/producer.py)

### Step 3: Test Producer Script
After successfully creating the script let's test it by running it on our VSCode with the line of code below.

![test](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/10.png)

From the image, you would notice data are being inserted into our PostgreSQL Database.

![PostgreSQL_Insert](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/11.png)

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

![debezium](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/12.png)

In the new window select the database we want to use to perform CDC. We will be using PostgreSQL for our project.

![Postgresql](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/13.png)

In the connection setting you’re expected to fill in the necessary credentials for the PostgreSQL Server.

![advanced](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/14.png)

Change the Replication to pgoutput then click on Validation to test and validate our connection.

![pgout](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/15.png)

At the end of the connection, you should get debezium running and capturing data real-time from PostgreSQL

![validate](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/16.png)

## Setup Kafka Topic
Now that our debezium is up and running as expected we need to set Kafka topic which will be used in receiving the data from debezium.

**Note:** By default Debezium would create a Kafka topic for use from which to read the data.

### View Kafka Topic
Using the command below in our VSCode terminal we can list all available topics in Kafka broker.

```
docker-compose exec kafka kafka-topics.sh --list --bootstrap-server kafka:9092
```

![view_topics](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/17.png) 

With the command we can locate the topic the data is being sent to in Kafka topic which is deb_conn.fabric.user_data.

### Consumer Kafka Topic

Using the command below to consume data realtime from Kafka topic in our terminal.

```
docker-compose exec kafka kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic deb_conn.fabric.user_data --from-beginning
```

![verift](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/18.png)

The image avove shows that we can consume data from Kafka Topic that is being sent by debezium in realtime.

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

![wls](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/19.png)

You will notice a new index has been created in ElasticSearch called user_data_index.

![index](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/20.png)

You can use the command below to confirm the ElasticSearch Index Created.
```
curl -X GET -x "" "localhost:9200/user_data_index_new?pretty"
```

### Consumer Script
Use the code below to create a consumer script and insert data into ElasticSearch Index created.

👉🏽 **Click:** [Consumer Script ElasticSearch](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/consume_elasticsearch.py)


![confirm](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/21.png)

From the image above we can confirm data is been consumed in real time.

## Confirm Streaming
To confirm everything is working as expected we are going to compare the data in Azure PostgreSQL database and that of the Index ElasticSearch.

### Confirm PostgreSQL View
We cannot directly query the table as data are being inserted into the table, we need to create a view that we can use in counting the database.

You will notice the number of rows of data inserted into the PostgreSQL table is 119

```
create view fabric.user_data_view as
select * from fabric.user_data
– - Create a view from and existing table
select  count(*) from fabric.user_data_view
```
![count](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/22.png)

### Confirm ElasticSearch Index Count
Using the command GET /user_data_index_new/_count?pretty we can get the total number of rows. http://localhost:5601/

![elastic_count](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/24.png)

### View Data in ElasticSearch
With this command below we can get the value of 10 records in the ElasticSearch index.
```
GET /user_data_index_new/_search?pretty
{

  "query": {

    "match_all": {}

  },        

  "size": 10

}
```

![last_10](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/25.png)

## Create a Kibana Dashboard for ElasticSearch Index 
Elasticsearch data is visualized and analyzed using Kibana, a potent open-source data visualization tool. It offers an intuitive user interface for examining and comprehending patterns, trends, and anomalies in data.

The following steps should be followed in setting up the Kibana Dashboard:

### Step 1: Create an Index Pattern
Kibana Index Patterns are a fundamental concept that allows you to organize and visualize your data stored in Elasticsearch. They serve to define how Kibana should interpret and group your data based on specific criteria.

In your ElasticSearch site expand the pane and click on the Dashboard, this should open another window.

![index_pattern](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/26.png)

In the new window select the Create new dashboard this should take you to the visualization tab.

![new_dashboard](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/27.png)

Using the Wildcard to select the ElasticSearch Index created.

![index_wildcard](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/28.png)

### Step 2: Discovery
The discovery gives you a better way to visualize the data in ElasticSearch index either in a Tables or JSON format.

![discovery](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/29.png)

Expand the records to get more information about the data.

![expand](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/30.png)

### Step 3: Create Visualization
Click on Create Visualization this should take you to the design area.
![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/31.png) 

Create as much visualization if needed.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/32.png) 

## Create Consumer to Azure Data Lake Gen 2
Microsoft Azure offers a highly scalable and reasonably priced data lake storage solution called Azure Data Lake Gen 2. Its numerous features and ability to manage large volumes of data, both structured and unstructured, make it appropriate for a broad range of machine learning and data analytics tasks.

### Step 1: Generate SAS Token
In your Azure Data Lake Gen 2 expand the Security & networking and select the Shared access signature. Pick the data and click generate SAS and Connectiong Strings.

![token](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/33.png) 

### Step 2: Consumer Script to ADLS
Create a consumer script that would be used in picking data from the Kafka topic and sending to Azure Storage Account.

👉🏽 **Click:** [Consumer_Script_ADLS](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/consumer_adls.py)

### Step 3: Confirm Update
Head to your Azure Storage account and confirm the data update. From the image, you will notice a successful upload to the storage account.

![update](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/35.png) 

# Section 3: Setting up the CDC streaming process in Microsoft Fabric
At this point we are going to add an Azure PostgreSQL Database as a CDC source for EventStream in Microsoft Fabric. Link

**The following steps should be followed:**

### Step 1: Create a Fabric workspace in Power BI Service

In your Power BI account create a workspace that can be use in housing the entire Fabric resource.

In the new workspace you are expected to add a new item called EventStream. This Item is like Apache Kafka but for streaming purposes.

![workspace](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/36.png) 

### Step 2: Select and Configure Source

You are expected to add a data source for EventStream, since we connect Azure PostgreSQL we will be using the PostgreSQL database as our source.

![source](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/37.png) 

Select your database, use this database as testing.

![databae](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/38.png) 

In the new windows select the new connection to configure the entire set-up needed.

![connection](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/39.png) 

Add all the necessary credentials for of the Azure PostgreSQL and connect.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/40.png) 

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/41.png) 

### Step 3: View Data
After making all necessary connections you can view your data by selecting the data preview in EventStream.

![view](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/42.png) 

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/43.png) 

### Step 4: Create EventHouse
This will be used in creating a KQL Database for storing the stream data and building real-time report using KQL language.

![eventhouse](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/44.png) 


### Issues with CDC in Fabric EventStream ⚠️
This feature is amazing for CDC in the enterprise approach, the only issue I found was the PostgreSQL Database does not support multiple slots.

The previous slot used for the Debezium connector affected the connection and setting for Fabric CDC for PostgreSQL. I had to provision a new server to solve this issue.

## Option 2: Send Data to Custom App EventStream from Producer
Due to the Slot issue with Debezium, let's send data directly from the API to Fabric EventStream by creating a custom App producer.

### Step 1: Set Custom App
In the same workspace create a new EventStream and provide a unique name for processing.

![custom_app](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/45.png) 

Then select Use Custom endpoint for your producer.

![endpoint](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/46.png) 

You are expected to provide your endpoint with a name then click on add.

![endpoint](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/47.png)  

### Step 2: Create a Producer App

Firstly we need to get some security settings before sending data to our app. Copy the EventHub name and connection string-primary key and play it in a secure location. We are using the environment variable in our Python code.

![peoducer_app](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/48.png) 

Below is the code used in sending data from the API to EventStream in Fabric.

👉🏽 **Click:** [EventHub Script Fabric](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/producer_eventhub.py)

### Step 3: Test Streaming Data

Let's test and confirm streaming data to Fabric EventStream. From the image below we can confirm data are being streamed in real-time to Fabric EventStream from our producer application.

![test](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/49.png) 

### Step 4: Set [KQL Visualization](https://learn.microsoft.com/en-us/kusto/query/tutorials/learn-common-operators?view=microsoft-fabric)
We need to perform some queries and set visualization using the KQL Database in Fabric.

Start by clicking the dropdown on the last tab and select EventHouse which is used in storing the KQL database.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/50.png) 

We are using a direct query so fill in the following information.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/51.png) 

Publish to save all changes, this should take a couple of minutes depending on your internet speed.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/52.png) 

Perform the necessary configuration for Eventhouse.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/53.png) 

View the KQL Database by clicking on the Open Item

![KQL](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/54.png) 

### Step 5: Build Near-Real time Report
Expand the table you are streaming data into and let visualize better.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/55.png) 

Query your data using KQL and get the desired output then select the Power BI tab at the right corner of your report.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/56.png) 

Build your near realtime report with the streaming data.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/57.png) 

# Section 4: Create a Fabric Pipeline

The Microsoft Fabric Pipeline is the same as the Azure Data Factory and Synapse Pipeline with much similarity. Some knowledge in any of the previous can easily be transferred to this use case.

We plan to move the entire data from Azure Data Lake Gen 2 to Fabric Lakehouse Files folder by using a Pipeline.

**The following set should be followed to achieve this:**

### Step 1: Set Source Connection
In the same workspace create a Pipeline and add the copy activity which will be used in our configuration process.

To connect to the Azure Data Lake Gen 2 which is our source you can get the DFS endpoint using the Azure Storage Explorer.

![credentials](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/58.png) 

With the endpoint gotten fill in the following connection configuration below and use the SAS token generated earlier when sending data to Azure Data Lake from Kafka Topic.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/59.png) 

After setting up all necessary connection save your work and run Pipeline.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/60.png) 

### Step 2: Test and Confirm Data Movement
Run the pipeline to confirm if data loaded as expected.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/61.png) 

Head to the Fabric Lakehouse and confirm data load.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/62.png) 

# Section 5: Create a RAG Model using Azure OpenAI 

## Transforming and Loading JSON Files.
The `JSON` data being streamed into OneLake needs to be transformed into a tabular format for easier reading, visualization, and LLM interaction which will be configured later.
When you open up an empty Notebook, on the left pane of the window, we find all the files we are looking for in the Lakehouse
In the window of the new notebook, you will see a left pane with the following items Resources, Lakehouses, and Warehouses. 

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/63.png) 

We are using a Lakehouse for this scenario so select Lakehouse. If no Lakehouses pop up, you can click on the Add Lakehouse icon and select an existing Lakehouse or create a new one. In our case, the Lakehouse already exists and when we open it up, we find the user_folder directory which contains all the `JSON` files being streamed into the Lakehouse.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/64.png) 

Now, let’s switch attention to the Notebook and its content. This notebook will define all the libraries and functions used to perform all the transformations necessary for cleaning the data and writing it to a Delta Table.

## Code Walkthrough
### Import relevant Libraries

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/65.png) 

### Define Sequence Map and Sequence Mapper

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/66.png) 

The sequence map is used to indicate which step in the transformation is taking place in real-time. The sequence mapper is a python decorator that will be used along with all the functions we use for performing the transformations and will apply the sequence map on each function accordingly.

### Transformation Functions
All the functions used for the transformations are listed below:
1.	read_data:
This function reads JSON data from the specified ABFSS filepath into a Spark DataFrame.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/67.png) 

2.	extract_payload:
Extracts the payload from a Spark DataFrame by dropping unnecessary columns     and converting it to a list of dictionaries. This function removes the "schema" column from the DataFrame and converts the resulting DataFrame to a list of dictionaries, where each dictionary represents a record.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/68.png) 

3.	parse_payload:
Parses a list of payload dictionaries to extract main information. This function iterates over the provided list of payloads, attempting to extract the "after" portion of the payload. If a KeyError occurs (i.e., the expected structure is not present), the function will skip that payload.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/69.png) 

4.	create_schema:
Creates and returns a Spark DataFrame schema. This function defines the structure of the DataFrame by specifying the column names and their corresponding data types. The schema includes fields for personal information such as name, gender, address, and various timestamps.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/70.png) 

5.	create_dataframe_from_parsed_payload:
Creates a Spark DataFrame from a parsed payload using a specified schema. This function takes a list of parsed payloads and a callable schema maker function to create a DataFrame. The schema maker should return a StructType defining the structure of the DataFrame.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/71.png) 

6.	capitalize_columns:
Capitalizes the names of all columns in a Spark DataFrame. This function iterates over the columns of the input DataFrame and modifies their names to be capitalized.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/72.png) 

7.	parse_timestamps:
Parses a timestamp column in a Spark DataFrame. This function updates the specified column in the DataFrame by converting its values from a Unix timestamp format. If the `date_only` parameter is set to True, the column will be cast to a date type.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/73.png) 

8.	split_timezone:
Splits the timezone column into separate location and offset columns. This function extracts the timezone location and offset from a formatted timezone string in the DataFrame. The original timezone column is removed after extraction.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/74.png) 

9.	timezone_hours_from_gmt
Converts a GMT offset string to total hours and adds it as a new column. This  function defines a helper function to calculate the total hours from a GMT offset string (formatted as "+hh:mm" or "-hh:mm") and applies it to the specified offset column. The result is added as a new column in the DataFrame.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/75.png)  

10.	extract_age:
Calculates the age based on a date column and adds it as a new column. This function converts the specified date column to a date type, calculates the age in years based on the current date, and adds a new column named "Age" to the DataFrame.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/76.png) 

11.	final_cleanup:
Performs final cleanup on the DataFrame by selecting specified columns and adding an ingestion date. This function selects the columns specified in the `cols` list and adds a new column named "Ingestion_Date" with the current timestamp.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/77.png) 

12.	write_to_delta:
Writes the provided DataFrame to a specified Delta table. This function saves the input DataFrame to a Delta table with the specified name, using the "overwrite" mode to replace any existing data in the table.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/78.png) 

Final Result
Putting it all together, we have:

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/79.png) 

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/80.png) 

After running the commands, we should have the following printed out to console:

We can read the final result stored in the `transform_df` variable

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/81.png) 

We can also confirm that this data has indeed been written to a Delta Table by refreshing the tables folder on the left pane under our Lakehouse. The `user_data`should appear as seen below:

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/82.png) 

## Creating the Delta Table Assitant

In this section, we aim to create an AI capable of answering questions based on the information provided in the table created in the previous section. To achieve this, we follow these steps:
1.	Create Working Environment and install packages
2.	Create config files
3.	Reasoning behind the code
4.	Code walkthrough
5.	Brief demonstration

## Create Working Environment and install packages
To begin creating the AI Table Assistant on Microsoft Fabric, we need to first create a new environment as the default environment comes preinstalled with an older version of OpenAI and we need to also install other packages to aid the development.
First go to your workspace and click on “New” on the top left corner of your screen.
Click on “More Options” and then in the next window, scroll down till you are at the Data Science section and click on Notebook.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/83.png)  

This brings you to a new notebook. In the new notebook, select the dropdown arrow in the “Environment” tab at the top of the screen. 
Click on “New environment”. Give the new environment a name.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/84.png)  

In the new environment window, type in the names of the packages required.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/85.png) 

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/86.png) 

Click on save and then publish.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/87.png) 

### Create config Files
In the window of the new notebook, you will see a left pane with the following items Resources, Lakehouses, and Warehouses. 

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/88.png) 

We are using a Lakehouse for this scenario so select Lakehouse. If no Lakehouses pop up, you can click on the Add Lakehouse icon and select an existing Lakehouse or create a new one.
Click on the ellipsis to the right of the “Files” icon and create a new subfolder and name it “config_files”. This subfolder will host the credentials required for this section.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/89.png) 

Next, open up a notepad or any text editing software and input your Azure OpenAI credentials

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/90.png) 

Save the file with any name you want with the extension, .env
Go back to Fabric and click on the ellipsis next to config_files, the subfolder just created, and select upload files. 
Search for the .env file and select it.
Once uploaded, we can proceed to start coding.


## Reasoning behind the code
The logic behind the code is given below:
Information about the table such as its column names, data types, and what values each column contains is given to the AI as part of the context of its prompt. The AI is also fed instructions about how to answer the questions asked. The AI will return the relevant SQL query to query the table in order to answer the questions. This query response is then parsed and cleaned before being passed into a Pyspark read command. Once the output table is generated, it is converted to a Python dictionary and fed into the AI once more to generate a summary of the data returned.

## Code Walkthrough:
Start the session by clicking on the connect icon:

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/91.png) 

Import the relevant libraries

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/92.png) 

Load the credentials from the .env file created earlier

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/93.png) 

If this cell returns True, then, the load_dotenv method has loaded up the credentials in the .env file
Instantiate the ENDPOINT, API_KEY, API_VERSION, MODEL_NAME from the .env file

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/94.png) 

Load the spark dataframe

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/95.png) 

We get the following table:

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/96.png) 

Next, we define a prompt template where all the prompts used by the LLM will be stored. This template is created using an enum class
The template consists of 4 simple prompts. They are:
a.	tableSchema: This just contains basic information about the Hive table such as the column name, data type, and column description.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/97.png) 

b.	select Table: This tells the LLM what type of information is in the table, the table schema, the user’s question (i.e. the prompt) and other instructions on how the result I expect from the LLM should look like.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/98.png)  

c.	summarizeTable: This prompts the LLM to give a summary of the information in the table in light of the initial prompt given.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/99.png) 

d.	badPromptError: This is a default message returned when the prompt asked has nothing to do with the table.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/100.png) 

Next, we move on to the cell that contains all the LLM interactions.
a.	`get_openai_client`:
This function simply helps to create the Azure OpenAI client 

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/101.png) 

b.	`‘instruction_type_select`:
This function helps to select which prompt template to use. It will be used in other functions in deciding how the LLM should be prompted. The available instructions are “select” which maps to the selectTable prompt in the PromptTemplae Enum class and “summarize” which maps to the summarizeTable prompt in the same Enum class.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/102.png) 

c.	`generate_instruction`:
This function is used to generate the instruction actually sent to the LLM. We have defined a prompt template. It takes in the prompt (i.e. the user query) and then couples it with the text from the PromptTemplate Enum class to form a complete instruction set for the LLM. If the LLM is providing the SQL query for answering the user’s question, then, instruction type is “select” as described earlier. When the resulting table has been generated, it is converted to a dictionary and is passed into this same generate_instruction function as `prompt_result` in which case, the instruction_type switches to “summarize” and instructions to summarize the resuting table is sent to the LLM.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/103.png) 

d.	`get_gpt_response`:
This function takes in the generated instruction set - a combination of the user’s query and the correct prompt template -  and sends it to the LLM

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/104.png) 

e.	`parse_gpt_response`:
This function cleans the response received from the LLM.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/105.png) 

f.	`generate_gpt_dataframe`:
This function is used to return the resulting dataframe from SQL query received and cleaned from the LLM.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/106.png) 

g.	`convert_gpt_dataframe_to_dict`:
This function is simply responsible for converting the resulting dataframe if it exists to a dictionary which is in turn passed down to the LLM for summarization.

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/107.png) 

## Brief Demonstration:
Combining all these elements together, we have:
![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/108.png) 

Results:

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/109.png) 

![visual](https://github.com/kiddojazz/CDC_Stream_Kafka_Fabric/blob/master/images/110.png) 

# Conclusion
In this project, we covered multiple scenarios on how to perform a CDC using Open Source Technology with Kafka and Debezium and Enterprise solution using Microsoft Fabric technology. We also integrated the solution by creating a near-to-real-time data dashboard solution.





























