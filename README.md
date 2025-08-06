# Data Drift Monitoring System

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-green)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A FastAPI-based application for monitoring data drift in real-time. It receives data via API, compares it with a reference dataset, and sends alerts to Slack if drift is detected.

<img width="1920" height="843" alt="mongo_drift" src="https://github.com/user-attachments/assets/2ca14a68-cfb1-43e3-95fb-429d752bc291" />
## Features

- Real-time data drift detection
- Slack alerts
- MongoDB storage
- Simple drift detection algorithm (Z-score for numerical features, new categories for categorical features)

![WhatsApp Image 2025-08-06 at 5 14 54 PM](https://github.com/user-attachments/assets/d75ffadb-a52b-4be8-a095-00793ac4ae61)



## Setup


### Prerequisites

- Python 3.11+
- MongoDB
- Slack workspace with an incoming webhook

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/saul-villarados/FastAPI-Drift-Monitoring-System.git
   cd FastAPI-Drift-Monitoring-System
