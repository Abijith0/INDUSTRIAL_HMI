# 🏭 INDUSTRIAL HMI (Python/PySide6)

![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Framework](https://img.shields.io/badge/Framework-PySide6-41CD52?style=for-the-badge&logo=qt&logoColor=white)

## 📋 Project Overview
A professional PC-based Industrial HMI/SCADA application developed using **Python (PySide6)** for leak testing and production machines. This system replaces traditional hardware HMIs (Siemens/Allen-Bradley) with a modern, scalable, and cost-effective software solution.

Designed with real factory requirements in mind: **Live Monitoring**, **SPC Analysis**, **Alarm Logging**, and **Automated PDF Reporting**.

---

## 📸 Project Screenshots

### 1. Main Dashboard (Auto Mode)
![Main Dashboard](SCREEN_AUTO.png)

### 2. Live SPC Charts
![SPC Charts](SCREEN_CHART.png)

### 3. SQL Production Datalog
![Datalog](SCREEN_DATALOG.png)

---

## ⚙️ Industrial Use Case
This HMI was engineered for an **Industrial Leak Testing Machine** used in automotive component manufacturing. It functions as a complete operator interface and production monitoring system.

**Key Benefits:**
* **Cost Reduction:** Replaces expensive proprietary panel HMIs.
* **Data Ownership:** Logs detailed cycle data to SQLite (no license fees).
* **Traceability:** Records Serial Numbers, Test Results, and Timestamps for every cycle.
* **Reporting:** Generates automatic Shift Reports (PDF/Excel) for management.

---

## 🧠 Core Features

### 🖥 Modern Dashboard
* Clean single-page industrial UI.
* Large touch-friendly controls.
* Real-time machine status & PLC communication indicator.

### 📊 Production Monitoring
* **OK / NG** job counting.
* **Yield Percentage** calculation (Live OEE tracking).
* Multi-cavity leak test value visualization.

### 📈 SPC & Trend Charts
* Real-time pressure trend graphs using `QtCharts`.
* Historical performance monitoring for Quality Control.

### 🗃 Data Logging System
* **SQLite Database:** Stores date/time stamped records.
* **Alarm Management:** Logs safety bypass alerts and machine faults.

### 📄 Automated Reporting
* **PDF Export:** Generates professional shift reports.
* **Excel/CSV Export:** Raw data export for external analysis.

---

## 🧱 System Architecture

```mermaid
graph TD
    PLC["PLC / Controller"] -->|"Modbus TCP / OPC UA"| HMI["Python HMI (PySide6)"]
    HMI -->|"Log Data"| DB[("SQLite Database")]
    HMI -->|"Visualize"| UI["Operator Dashboard"]
    HMI -->|"Generate"| RPT["PDF & Excel Reports"]








---

## ▶ How to Run

### Requirements
* Python 3.10+
* Windows OS (Recommended)

### Installation
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Abijith0/INDUSTRIAL_HMI.git](https://github.com/Abijith0/INDUSTRIAL_HMI.git)
    cd INDUSTRIAL_HMI
    ```

2.  **Install dependencies:**
    ```bash
    pip install PySide6
    ```

3.  **Run the application:**
    ```bash
    python MAIN.PY
    ```
    *(Note: The application includes a **Simulation Mode**, so it will generate dummy data even without a PLC connected.)*

---

## 📄 Sample Reports
- [Download Sample PDF Report](ProductionReport_18-02-2026.pdf)
- [Download Sample Excel Sheet](ProductionReport_18-02-2026.xlsx)

---

## 👨‍💻 Developer
**Abijith Harishkumar**
*Automation Engineer | IIoT & Python Developer*

Focused on bridging the gap between **OT (Operational Technology)** and **IT** by combining PLC systems with modern software architecture.
