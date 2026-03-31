Flowmingo - Where money flows, we watch...

FlowMingo is a real-time financial intelligence platform that transforms banking transactions into
a live, dynamic graph, which will enable instant detection of fraud as it happens.
Built using Graph AI + Streaming Systems, FlowMingo identifies complex money laundering
patterns like:
Round-tripping
Smurfing
Layering
Banks lose billions annually to layered money-laundering schemes, yet most fraud systems analyze
transactions individually, missing the network-level patterns that reveal criminal rings.
Flowmingo builds a live transaction graph, streams every payment via Apache Kafka, and runs a
Graph Neural Network (GNN) to detect smurfing, round-tripping, and dormant account activation
in real time, surfacing risk before funds leave the bank.
One-click "Evidence Package" generator compiles the full transaction chain, KYC data, and a
narrative into a FIU-ready STR/CTR report in under 10 seconds, turning a 4-hour compliance task
into a single button press.

What makes Flowmingo unique?

1.⁠ Live Graph-Based Transaction Monitoring:
Every transaction is a directed edge in a Neo4j graph. Money movement patterns become 
visible as network topology; no flat SQL query can see what a graph sees.
2.⁠ GNN-Powered Fraud Typology Detection:
PyTorch Geometric GNN trained on known AML typologies: round-tripping, smurfing
(sub-₹50K structuring), and layering. Louvain Community detection finds fraud rings
automatically.
3.⁠ ⁠One-Click FIU Evidence Package:
When an alert fires, one<img width="866" height="724" alt="Screenshot 2026-03-30 at 11 27 19 PM" src="https://github.com/user-attachments/assets/bb238a4b-1264-4c5e-bea4-efe6ca3df97d" />
 click compiles the full fund trail, timestamps, KYC data, and an LLM-
written narrative into a formatted STR/CTR; PMLA-compliant and ready to file in 10
seconds.
4.⁠ ⁠ Animated Cytoscape.js Dashboard:
React frontend renders live fund flow as an animated graph. Investigators see which accounts are involved, 
the hop sequence, and the risk score, all updating in real time via Kafka streams.
