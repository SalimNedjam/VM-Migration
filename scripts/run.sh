
# RUN
cd ../qemu-5.2.0/
./install/bin/qemu-system-x86_64 -boot d -enable-kvm -m 1204 -vga virtio -drive file=./imgs/foobar.qcow2,if=virtio -L ./pc-bios
cd ../scripts