UBO Calculator
A web-based tool for calculating Ultimate Beneficial Ownership (UBO) in multi-layered business structures.
Overview
The UBO Calculator helps staff and management identify ultimate beneficial owners across complex corporate structures. It automatically traces ownership through multiple layers of companies and calculates each person's or entity's ultimate ownership percentage in the target business.
Key Features

Visual ownership diagrams - Clear graphical representation of ownership structures with colour-coded entities (blue for companies, orange for people)
Automatic UBO calculation - Traces ownership paths through multiple layers and calculates ultimate ownership percentages
Dual relationship tracking - Records both equity ownership and directorship roles
Layer organisation - Arrange entities in visual layers for clear hierarchy display
Validation checks - Automatic validation that ownership percentages sum correctly
Data export - Download entities, relationships, ultimate ownership data and diagrams as CSV/PNG files
Quick setup tools - Helper function to create multiple equal-share directors in one step

Use Cases
This tool is designed for:

Compliance teams verifying beneficial ownership for regulatory requirements
Due diligence during mergers and acquisitions
Legal teams mapping corporate structures
Management reviewing ownership positions
Anyone needing to understand complex multi-tier ownership structures

Benefits

Reduces human error - Automated calculations eliminate manual arithmetic mistakes
Improves efficiency - Complex ownership structures calculated instantly
Reduces completion time - Tasks that previously took hours now take minutes
Clear understanding - Visual diagrams make complex structures easy to comprehend
Audit trail - Export all data for documentation and compliance purposes

How It Works

Add entities - Create companies and people in your ownership structure
Define relationships - Set up equity ownership percentages and directorship roles
Set target company - Select which business you want to analyse
View results - See ultimate ownership percentages and visual diagram automatically

Example
If Matt Ltd is owned 50% by yourself and 50% by Matt Holdings, and Matt Holdings is owned 25% by Claude and 75% by Mike, the calculator will show:

You: 50% of Matt Ltd
Claude: 12.5% of Matt Ltd (25% × 50%)
Mike: 37.5% of Matt Ltd (75% × 50%)

Getting Started
Running Locally

Install Python dependencies:

bashpip install -r requirements.txt

Run the application:

bashstreamlit run app.py

Open your browser to http://localhost:8501

Deploying to Streamlit Cloud

Push your code to GitHub
Connect your repository to Streamlit Cloud
Deploy with the following files:

app.py - Main application
requirements.txt - Python dependencies
packages.txt - System dependencies



Data Privacy

No persistent storage - All data exists only in your browser session
Session-based - Data resets when you close the browser tab or refresh
No data transmission - Information never leaves your machine except via manual downloads
Public data - Tool is designed for publicly available UBO information only

This tool is safe for work use as it handles public beneficial ownership information that is typically available through Companies House or similar registries.
Technical Details
Built with:

Streamlit - Web application framework
Pandas - Data manipulation and analysis
Graphviz - Diagram generation and visualisation

Requirements

Python 3.7+
See requirements.txt for full dependency list

Limitations

UBO threshold is adjustable (default 25%) but must be set before analysis
Circular ownership structures are not supported
Maximum 10 visual layers for diagram clarity
