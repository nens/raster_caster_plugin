FROM qgis/qgis:4.2

# COPY requirements-dev.txt /root
# RUN pip3 install -r /root/requirements-dev.txt
RUN qgis_setup.sh
RUN pip3 install "shapely>=2.1.1" --break-system-packages
# Create runtime directory required by WSLg / VS Code Wayland forwarding
RUN mkdir -p /tmp/runtime-root && chmod 700 /tmp/runtime-root
# Copied the original PYTHONPATH and added the profile's python dir to imitate qgis' behaviour.
ENV PYTHONPATH=/code:/usr/share/qgis/python/:/usr/share/qgis/python/plugins:/usr/lib/python3/dist-packages/qgis:/usr/share/qgis/python/qgis:/root/.local/share/QGIS/QGIS3/profiles/default/python
# Note: we'll mount the current dir into this WORKDIR
WORKDIR /code
