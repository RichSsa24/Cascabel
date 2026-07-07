FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    auditd \
    python3 \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY agent.py /agent.py
RUN chmod +x /agent.py

# Start auditd and the agent
CMD service auditd start && python3 /agent.py
