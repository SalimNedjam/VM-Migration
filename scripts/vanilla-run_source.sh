
# RUN
cd ../vanilla-qemu/

./install/bin/qemu-system-x86_64 -nographic -boot d -enable-kvm -m 1204  -drive file=/home/dev/git/vm-migration-fingerprint/qemu-5.2.0/imgs/foobar.qcow2,if=virtio -L ./pc-bios

cd ../scripts