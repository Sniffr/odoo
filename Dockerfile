FROM odoo:18.0

USER root

# Install system packages and Python dependencies
RUN apt-get update && \
    # Install net-tools (for netstat) and iproute2 (for ss)
    apt-get install -y net-tools iproute2 && \
    pip3 install --no-cache-dir --break-system-packages icalendar && \
    # Clean up apt lists to keep the image small
    rm -rf /var/lib/apt/lists/*

USER odoo