# Final-Project-End-to-End-Data-Pipeline-and-Dashboard

# Final Project: End-to-End Data Pipeline on Google Cloud Platform (GCP)

## Objective  
The goal of this final project is to demonstrate your understanding of the full data engineering lifecycle by building an end-to-end data pipeline on **Google Cloud Platform (GCP)**, culminating in a functional dashboard.

## Problem Statement  
You are required to:  
- Choose a **dataset of interest**.  
- Design and implement a **pipeline to ingest and store** the dataset in a **data lake**.  
- Build a **pipeline to move the data** from the data lake to a **data warehouse**.  
- Apply **data transformation** within the warehouse to make it **analysis-ready**.  
- Build a **dashboard (at least one page)** that presents **meaningful insights** using the transformed data.  

## Data Pipeline Type  
You must choose either:  
- **Streaming pipeline** – for ingesting real-time data into the data lake.  
- **Batch pipeline** – for periodic ingestion (e.g., hourly, daily).  

Be clear in your choice and rationale.

## Key Evaluation Criteria  
- **Pipeline reliability**: The code should be **robust and reusable**, not something that breaks after one run.  
- **Security best practices**: Follow best practices for **managing credentials, access control, and secure data handling**.  
- **Flexibility and scalability**: A well-designed pipeline should be **runnable or scalable without major rework**.  
- **Best practices adherence**: Projects following **class concepts** (e.g., **decoupling, modularization, monitoring**) will score higher.  

## Deliverables  
- **Final Presentation**: Due **Friday, April 4th (in class)**.  
- **Final Submission**: Due **Monday, April 7th**.  

## Data Source Flexibility (Recommended)  
Whenever possible, design your pipeline to support **changeable or refreshable data sources**.  
- The data should be **re-ingestible over time** (e.g., via an API that updates regularly, scheduled batch jobs, or streaming).  
- If using **static datasets** (e.g., from Kaggle or public CSVs), structure your pipeline as if it could be **re-run with new or updated data** in the future.  

💡 **Tip**:  
We understand it can be difficult to find publicly available APIs with real-time or regularly updating data. In such cases:  
- You may use **web scraping** (ensure the site permits it).  
- Or **simulate freshness** by **splitting and replaying static datasets over time**.  

Clearly explain any **limitations and your approach** in the `README`.  
**Projects that consider reusability or auto-refresh mechanisms will score higher**.

## Submission Requirements  
To submit your project, please provide:  
1. **A link to your GitHub repository**  
2. **Your Commit ID** (6 alphanumeric characters)  

### Your GitHub repository should contain:  
- **All relevant code**  
- A clear and concise `README` file explaining:  
  - Your approach, pipeline architecture  
  - Instructions to reproduce or deploy your project (if applicable)  
  - A **link to your final dashboard**  
