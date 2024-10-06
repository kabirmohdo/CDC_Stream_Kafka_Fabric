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







