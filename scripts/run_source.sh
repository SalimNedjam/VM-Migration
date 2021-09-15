
# RUN
cd ../qemu-5.2.0/

./install/bin/qemu-system-x86_64 -nographic -boot d -enable-kvm -m 5120  -drive file=./imgs/foobar.qcow2,if=virtio -L ./pc-bios

cd ../scripts