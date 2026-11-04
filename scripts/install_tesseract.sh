#!/bin/bash
# Databricks cluster init script: installs Tesseract OCR with Vietnamese.
# Cluster → Edit → Advanced options → Init scripts → add this file (workspace or volume path).
# Use a "Single user" (dedicated) cluster; shared clusters may block init scripts.
set -e
apt-get update -y
apt-get install -y tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng
tesseract --list-langs
