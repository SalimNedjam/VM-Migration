# COMPILE
cd ../qemu-5.2.0/build

../configure \
 --target-list=x86_64-softmmu \
 --disable-blobs --disable-strip --enable-system --enable-linux-user \
 --enable-modules --enable-module-upgrades --enable-linux-aio \
 --audio-drv-list=pa,alsa,oss --enable-attr --enable-brlapi \
 --enable-virtfs --enable-cap-ng --enable-curl --enable-fdt \
 --enable-gnutls --enable-gtk --enable-vte --enable-libiscsi \
 --enable-curses --enable-smartcard --enable-debug \
 --enable-vnc-sasl --enable-seccomp --enable-libusb \
 --enable-usb-redir --enable-xfsctl --enable-vnc \
 --enable-vnc-jpeg --enable-vnc-png --enable-kvm --enable-vhost-net \
 --enable-trace-backends=simple --extra-cflags="-save-temps=obj" \
 --prefix=$(pwd)/../install/

make -j8 install

cd ../../scripts