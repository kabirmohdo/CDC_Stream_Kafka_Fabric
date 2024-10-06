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
```Python
az account set --subscription "YourSubscriptionId"
```


