🦩 FlowMingo — AML Intelligence Platform

FlowMingo is an AI-driven Anti-Money Laundering (AML) intelligence platform designed to monitor, detect, and analyze suspicious financial transactions in real time.

It provides a powerful dashboard for financial institutions to identify fraud patterns such as smurfing, layering, and round-tripping, while also enabling complaint filing and transaction investigation.

Key Features

1. Live Transaction Monitoring
- Real-time simulation of financial transactions
- Visual monitoring using animated transaction flows
- Displays transactions per second (TPS)
- Risk score tracking over time

2. Intelligent Alert System
- Automatically flags high-risk transactions
- Categorizes alerts based on severity:
  - 🔴 High Risk
  - 🟡 Medium Risk
  - 🟢 Low Risk
- Displays live alert stream with transaction details

3. Fraud Typology Detection
Detects common money laundering patterns:
- 🐡 Smurfing (multiple small transactions)
- 🔀 Layering (complex transaction chains)
- 🔁 Round-Tripping (circular money flow)
- 📋 Normal transactions (monitored)

4. Analytics Dashboard
- Total transactions processed
- Flagged transactions count
- Fraud rings detected
- Transaction volume tracking
- Typology distribution visualization

5. Complaint Filing System
- Structured form to report suspicious activity
- Captures:
  - Account details
  - Transaction details
  - Typology classification
  - Evidence and notes
- Generates STR/CTR reports (simulated)

6. Transaction Records Management
- Search and filter transactions
- View detailed transaction info
- Export records as CSV
- Pagination for large datasets

7. Risk Scoring Engine
- Each transaction is assigned a risk score (0–100)
- Threshold-based classification:
  - >85 → Flagged
  - 55–85 → Review
  - <55 → Cleared

System Architecture

The platform follows a modular structure:

1. Data Simulation Layer
   - Generates realistic transaction data
   - Mimics banking systems (RTGS, NEFT, UPI)

2. Detection Layer
   - Assigns risk scores based on typology
   - Identifies suspicious patterns

3. Visualization Layer
   - Dashboard with real-time updates
   - Graphs and transaction flows

4. User Interaction Layer
   - Complaint filing interface
   - Transaction inspection tools

Technologies Used

- HTML5
- CSS3 (Custom UI + Animations)
- Vanilla JavaScript
- Canvas API (for live monitoring visuals)

Use Cases

- Banking fraud monitoring
- AML compliance systems
- Financial intelligence units (FIU)
- Academic demonstrations of fraud detection systems

Note

This is an implementation-based prototype designed for demonstration and educational purposes.  
It does not connect to real banking systems.

Future Improvements

- Integration with real transaction APIs
- Machine learning-based anomaly detection
- Graph-based fraud detection (GNN models)
- Role-based authentication system
- Backend database integration

Authors

-Harshith Nair
-Rishi Savla
Developed as part of a cybersecurity/AI research project.
