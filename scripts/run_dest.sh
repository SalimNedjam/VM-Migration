
# RUN
cd ../qemu-5.2.0/

./install/bin/qemu-system-x86_64 -boot d -nographic -enable-kvm -m 5120 -drive file=./imgs/foobar.qcow2,if=virtio -L ./pc-bios -incoming tcp:192.168.1.40:4444

cd ../scripts/
