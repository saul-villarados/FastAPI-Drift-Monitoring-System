# Data Drift Monitoring System

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-green)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A FastAPI-based application for monitoring data drift in real-time. It receives data via API, compares it with a reference dataset, and sends alerts to Slack if drift is detected.

## Features

- Real-time data drift detection
- Slack alerts
- MongoDB storage
- Simple drift detection algorithm (Z-score for numerical features, new categories for categorical features)

## Setup

### Prerequisites

- Python 3.11+
- MongoDB
- Slack workspace with an incoming webhook

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/drift-monitoring.git
   cd drift-monitoring