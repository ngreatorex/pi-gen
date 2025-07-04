#!/bin/bash -e

if [ "${ENABLE_CLOUD_INIT}" != "1" ]; then
	log "Skipping cloud-init stage"
	exit 0
fi

# Install tweaks from rpi-cloud-init-mods
mkdir -p "${ROOTFS_DIR}/etc/cloud/cloud.cfg.d"
install -v -m 644 files/etc/cloud/cloud.cfg.d/99_raspberry-pi.cfg "${ROOTFS_DIR}/etc/cloud/cloud.cfg.d/99_raspberry-pi.cfg"
mkdir -p "${ROOTFS_DIR}/usr/lib/systemd/system/cloud-init-main.service.d"
install -v -m 644 files/usr/lib/systemd/system/cloud-init-main.service.d/41-rpi-firmware-mount.conf "${ROOTFS_DIR}/usr/lib/systemd/system/cloud-init-main.service.d/41-rpi-firmware-mount.conf"
install -v -m 644 files/usr/lib/systemd/system/cloud-init-main.service.d/40-rpi-journal.conf "${ROOTFS_DIR}/usr/lib/systemd/system/cloud-init-main.service.d/40-rpi-journal.conf"

# some preseeding without any runtime effect if not modified
# install meta-data file for NoCloud data-source to work
install -v -m 755 files/boot/firmware/meta-data "${ROOTFS_DIR}/boot/firmware/meta-data"
install -v -m 755 files/boot/firmware/user-data "${ROOTFS_DIR}/boot/firmware/user-data"
install -v -m 755 files/boot/firmware/network-config "${ROOTFS_DIR}/boot/firmware/network-config" 
