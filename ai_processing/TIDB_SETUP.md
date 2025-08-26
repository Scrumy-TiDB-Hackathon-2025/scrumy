
# TiDB Setup Guide for Hackathon Demo

## Quick TiDB Cloud Setup
1. Visit: https://tidbcloud.com/
2. Create a free account
3. Create a new cluster (Serverless tier is free)
4. Get connection details from cluster dashboard

## Environment Setup
export DATABASE_TYPE=tidb
export TIDB_HOST=gateway01.us-west-2.prod.aws.tidbcloud.com
export TIDB_PORT=4000
export TIDB_USER=your_username
export TIDB_PASSWORD=your_password
export TIDB_DATABASE=scrumy_ai

## Test Connection
python demo_database_switching.py

## For Demo Day
- Use TiDB for live demonstration
- SQLite for backup/development
- Show switching between both databases
