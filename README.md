# Intelligent Secure NAS

## Overview

Intelligent Secure NAS is a distributed, production-style Network Attached Storage (NAS) platform designed with security, observability, monitoring, and centralized infrastructure management.

The platform integrates secure file storage, real-time monitoring, security event logging, brute-force detection, and infrastructure observability using modern DevOps and cybersecurity technologies.

This project was built as a practical cybersecurity and infrastructure engineering lab environment.

---

# Architecture

## Distributed 3-Node Infrastructure

| Node | Hostname | Primary Role |
|------|-----------|---------------|
| U1 | nas-core | Nextcloud + MariaDB + Redis + Nginx |
| U2 | nas-intel | FastAPI + PostgreSQL + Event Processing |
| U3 | nas-sec | Security Engine + Grafana + Prometheus |

---

# Key Features

✅ Secure distributed NAS architecture

✅ HTTPS-enabled file storage and sharing

✅ Real-time monitoring and observability

✅ Security event detection and alerting

✅ Brute-force attack detection using fail2ban

✅ Centralized dashboard monitoring

✅ Dockerized infrastructure deployment

✅ Grafana dashboards for analytics and monitoring

✅ Prometheus metrics collection

✅ Structured logging pipeline

---

# Technology Stack

## Core Infrastructure
- Nextcloud
- Docker
- Docker Compose
- Nginx
- MariaDB
- Redis

## Backend & Event Processing
- FastAPI
- PostgreSQL
- Python

## Security & Monitoring
- Grafana
- Prometheus
- fail2ban
- Node Exporter
- rsyslog

---

# System Workflow

1. Users upload files through Nextcloud
2. Security logs are generated and monitored
3. Events are forwarded through the logging pipeline
4. Security Engine monitors suspicious activity
5. Prometheus collects infrastructure metrics.
6. Grafana visualizes monitoring and security data

---

# Security Features

- Brute-force detection
- Automated IP blocking
- Security event monitoring
- Structured JSON logging
- HTTPS deployment
- Log forwarding pipeline
- Security alert generation

---

# Monitoring & Observability

The platform integrates:

- Grafana dashboards
- Prometheus metrics collection
- Node Exporter monitoring
- Security alert visualization
- Resource utilization tracking
- User activity analytics

---

# Repository Structure

```txt
secure-nas/
│
├── nas-core/
├── nas-intel/
├── nas-sec/
└── .gitignore
