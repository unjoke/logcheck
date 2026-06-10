# Log Detection Research Notes

Logcheck adapts ideas from modern log anomaly detection while staying local and deterministic.

## Adapted Ideas

- LogAI: keep a clear local analysis pipeline with parsing, feature extraction, detection, and reviewable outputs.
- LogPAI/logparser/Drain: normalize volatile log tokens into templates before counting repeated behavior.
- LogBERT-style sequence detection: treat suspicious event order as useful context, but implement deterministic sequence rules instead of training a model.

## Project Boundary

This project does not fetch external logs, query domains, scan networks, train remote models, block accounts, exploit systems, or submit reports externally. All detections are derived from local parsed events and local configuration.
