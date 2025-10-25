FROM odoo:18.0

USER root

# Install Python dependencies for custom addons
RUN pip3 install --no-cache-dir --break-system-packages icalendar

USER odoo
