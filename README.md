# Qemu #

## Get system config ##

```
apt-get source qemu
tar -xvf qemu_2.11+dfsg-1ubuntu7.34.debian.tar.xz
mv debian qemu-2.11+dfsg
cd qemu-2.11+dfsg

sudo apt-get build-dep qemu
dpkg-buildpackage -rfakeroot -uc -b
```

## Build & Install ##

```
cd qemu/
mkdir build
cd build/
../src/configure \
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
```

## Installation ##

```
./install/bin/qemu-system-x86_64 -boot d -enable-kvm -m 1204 \
    -vga virtio --cdrom ./ubuntu-20.04.1-live-server-amd64.iso -drive file=./imgs/foobar.qcow2,if=virtio
```

Update grub to add serial output :

File `/etc/default/grub`

add
```
GRUB_CMDLINE_LINUX="console=ttyS0"
GRUB_TERMINAL=console
```

Regenerate grub configuration :
```
grub-mkconfig -o /boot/grub/grub.cfg
```
## Abstraction ##
### QEMU Layout ##
```
----------------------------------------|----------------
|             Guest State               | SETUP LIBVIRT |
|---------------------------------------|---------------|
| DEVICE GUEST VISIBLE   | GUEST OPAQUE |  HOST STATE   |
|------------------------|--------------|---------------|
|                        |//////////////|               | 
|                        |//////////////|               | 
|                        |//////////////|               | 
|                        |//////////////|               | 
---------------------------------------------------------

The guest-visible device state is the state within QEMU which we send by our own protocol.  
	This includes the device state for each device that has been exposed to the guest.

The guest opaque, the host have no idea about for exemple the guest processes

The host state is QEMU state, is not involved during the migration process and must be replicated, it is quite important to get this right before migration is started, because the QEMU setup on the source and destination hosts have to be identical.   

```
## Migration ##

liens :
* https://www.linux-kvm.org/page/Migration
* https://www.programmersought.com/article/12583463192/
* https://qemu.readthedocs.io/en/latest/devel/migration.html
* docs/devel/migration.rst

Migration properties :

* send-configuration
* send-section-footer
* decompress-error-check
* clear-bitmap-shift

* downtime-limit
* checkpoint-delay

* announce-initial
* announce-max
* announce-rounds
* announce-step

Doc in :
* `./qapi/migration.json`

help migrate_set_parameter

info migrate

parameter :
* store-global-state

* max-bandwidth : to set maximum speed for migration. maximum speed in bytes per second. (Since 2.8)

info migrate_capabilities

Migration capabilities :
* xbzrle: Xor Based Zero Run Length Encoding. 
 this feature caches all the pages sent across to the destination in the previous iteration.  
 For each page to be transmitted across, we compare the current page with the page in the cache.  Only the difference in the bytes in such pages are then sent across.  
 This greatly reduces the data that goes over the network in some workloads, and hence speeds up the migration process. (`docs/xbzrle.txt`)
    * xbzrle-cache-size
* rdma-pin-all Pin tout le mémoire de la VM en mémoire physique pour accélérer la migration R utilisant le protocole DMA (`docs/rdma.txt`, `https://wiki.qemu.org/Features/RDMALiveMigration`)
* auto-converge : 
this setting can pause some vCPUs so that guests don’t make too much progress during stage 2 of migration by slowing it down.  That gives an opportunity for the number of dirty pages to reduce to our low watermark conditions to transition to stage 3.  
Pausing guest vCPUs can be done in several ways: re-nicing the guest vCPU threads on the host (each vCPU is just a regular thread on the host), or by restricting the host CPU time the guest as a whole gets via cgroups, or by just not scheduling particular guest vCPUs at all from QEMU code. (`https://wiki.qemu.org/Features/AutoconvergeLiveMigration`)
    * cpu-throttle-initial
    * cpu-throttle-increment
    * cpu-throttle-tailslow
    * max-cpu-throttle
    * throttle-trigger-threshold
* zero-blocks : Encode zeroed blocks with a flag
* compress: Compression à la volée des pages de RAM avec Zlib (`docs/multi-thread-compression.txt`)
    * x-compress-level
    * x-compress-threads
    * x-compress-wait-thread
    * x-decompress-threads

* events : generate events for each migration state change
* postcopy-ram :
    * max-postcopy-bandwidth : Background transfer bandwidth during postcopy.
* release-ram: Libération des pages de RAM migrées lorsque le postcopy est activé
* colo : COarse-Grain LOck Stepping. Les deux VMs restent synchronisées en continu
* block : Utilisé pour migrer le contenu des devices de type block
* return-path :

pause-before-switchover: Pause outgoing migration before serialising device
                           state and before disabling block IO (since 2.11)

* multifd : Utilise plus d'un file descripteur pour la migration
    * multifd-channels : Number of channels used to migrate data in parallel
    * multifd-compression : Which compression method to use
    * multifd-zstd-level
    * multifd-zlib-level

@dirty-bitmaps: If enabled, QEMU will migrate named dirty bitmaps.
                 (since 2.12)

@postcopy-blocktime: Calculate downtime for postcopy live migration
                      (since 3.0)

@late-block-activate: If enabled, the destination will not activate block
                       devices (and thus take locks) immediately at the end of migration.
                       (since 3.0)

@x-ignore-shared: If enabled, QEMU will not migrate shared memory (since 4.0)

@validate-uuid: Send the UUID of the source to allow the destination
                 to ensure it is the same. (since 4.2)

### Avec stockage partagé ###
#### Etape de migration live pre-copy ####

* Etape 1: `ram_save_setup()`
	* Marquer toute la mémoire comme dirty
* Etape 2: `ram_save_iterate()`
	* Envoyer les pages dirty jusqu'a ce que les critères de convergences seront validés 
* Etape 3: `migration_thread()`
	* Stoper la VM source
	* Transferer les pages dirty restantes 
	* Transferer les device state
* Lancer la VM destination

#### Transfert ####
La migration est un flux de byte qui peut être transferer.
* tcp migration: utilise les sockets tcp.
* unix migration: utilise les sockets unix.
* exec migration: utilise les standards stdin/stdout à travers unprocessus.
* fd migration: utilise un descripteur de fichier.


#### Manipulation ####

VMA source :
```
./install/bin/qemu-system-x86_64 -nographic -boot d -enable-kvm -m 1024 -drive file=./imgs/foobar.qcow2,if=virtio -L ./build/pc-bios/
```

VM dest :
```
./install/bin/qemu-system-x86_64 -nographic -boot d -enable-kvm -m 1024 -drive file=./imgs/foobar.qcow2,if=virtio -L ./build/pc-bios/ -incoming tcp:0:4444
```

Goto console :
```
ctrl+a c
```

Goto serial :
```
ctrl+a x
```

Start migration on A console type :
```
migrate -d tcp:127.0.0.1:4444
```

Migration info
```
info migrate
```

Stop emulation and quit on A
```
stop
exit
```

Dump migration on a file
```
(qemu) migrate "exec:cat > mig"
```

Analyse le fichier :
```
./qemu/src/scripts/analyze-migration.py
```

### Sans stockage partagé ###

Option `-b` dans migrate. TODO

## Tracing ##

doc :
* ./docs/devel/tracing.txt
* ./src/migration/trace-events
* ./src/docs/multi-thread-compression.txt

### Backend simple ###

doc :
* https://medium.com/@mcastelino/tracing-qemu-kvm-interactions-da92a8d78f79

Compilation avec : `--enable-trace-backends=simple`

Activation de tous les evements :
`cat ./build/trace/trace-events-all | grep "(" | grep -v "#" | cut -f 1 -d "(" > all_events`

Activation des evements de migration :

run avec `-trace events=events`
`./install/bin/qemu-system-x86_64 -boot d -enable-kvm -m 1024 -drive file=./imgs/foobar.qcow2,if=virtio -L ./build/pc-bios/ -trace events=events`

`./install/bin/qemu-system-x86_64 -nographic -boot d -enable-kvm -m 1024 -drive file=./imgs/foobar.qcow2,if=virtio -L ./build/pc-bios/ -incoming tcp:0:4444`

Run migration and stop & quit to flush the buffer :
```
stop
quit
```

Analyse the trace :
```
./src/scripts/simpletrace.py ./build/trace/trace-events-all trace-* > trace.txt
```

## GDB ##

```
gdb --args ./install/bin/qemu-system-x86_64 -boot d -enable-kvm -m 1024 -drive file=./imgs/foobar.qcow2,if=virtio -L ./build/pc-bios/ -trace events=events
```

Avoid signal noise :
```
handle SIGUSR1 noprint nostop
break migration_thread
break qemu_fflush
```

Dump migration on a file
```
(qemu) migrate "exec:cat > mig"
```

## Tests ##

doc :
* https://fadeevab.com/how-to-setup-qemu-output-to-console-and-automate-using-shell-script/

```
mkfifo /tmp/guest.in /tmp/guest.out
mkfifo /tmp/guest_monitor.in /tmp/guest_monitor.out

./install/bin/qemu-system-x86_64 -boot d -enable-kvm -m 1024 \
    -drive file=./imgs/foobar.qcow2,if=virtio -L ./build/pc-bios/ -trace events=events -nographic \
    -serial pipe:/tmp/guest -monitor pipe:/tmp/guest_monitor
```
## Gestion de la mémoire ##
```
    AddressSpace               
    +-------------------------+
    |name                     |
    |   (char *)              |          FlatView (An array of FlatRange)
    +-------------------------+          +----------------------+
    |current_map              | -------->|nr                    |
    |   (FlatView *)          |          |nr_allocated          |
    +-------------------------+          |   (unsigned)         |         FlatRange             FlatRange
    |                         |          +----------------------+         
    |                         |          |ranges                | ------> +---------------------+---------------------+
    |                         |          |   (FlatRange *)      |         |offset_in_region     |offset_in_region     |
    |                         |          +----------------------+         |    (hwaddr)         |    (hwaddr)         |
    |                         |                                           +---------------------+---------------------+
    |                         |                                           |addr(AddrRange)      |addr(AddrRange)      |
    |                         |                                           |    +----------------|    +----------------+
    |                         |                                           |    |start (Int128)  |    |start (Int128)  |
    |                         |                                           |    |size  (Int128)  |    |size  (Int128)  |
    |                         |                                           +----+----------------+----+----------------+
    |                         |                                           |mr                   |mr                   |
    |                         |                                           | (MemoryRegion *)    | (MemoryRegion *)    |
    |                         |                                           +---------------------+---------------------+
    |                         |
    |                         |
    |                         |
    |                         |          MemoryRegion(system_memory/system_io)
    +-------------------------+          +------------------------+
    |root                     |          |name                    | root of a MemoryRegion
    |   (MemoryRegion *)      | -------->|  (const char *)        | tree
    +-------------------------+          +------------------------+
                                         |addr                    |
                                         |  (hwaddr)              |
                                         |size                    |
                                         |  (Int128)              |
                                         +------------------------+
                                         |subregions              |
                                         |    QTAILQ_HEAD()       |
                                         +------------------------+
                                                      |
                                                      |
                                  +-------------------+---------------------+
                                  |                                         |
                                  |                                         |
                                  |                                         |

                    struct MemoryRegion                            struct MemoryRegion
                    +------------------------+                     +------------------------+
                    |name                    |                     |name                    |
                    |  (const char *)        |                     |  (const char *)        |
                    +------------------------+                     +------------------------+
                    |addr                    |   GPA               |addr                    |
                    |  (hwaddr)              |                     |  (hwaddr)              |
                    |size                    |                     |size                    |
                    |  (Int128)              |                     |  (Int128)              |
                    +------------------------+                     +------------------------+
                    |ram_block               |                     |ram_block               |
                    |    (RAMBlock *)        |                     |    (RAMBlock *)        |
                    +------------------------+                     +------------------------+
                               |
                               |
                               |
                               |
                               v
                    RAMBlock                     
                    +---------------------------+
                    |next                       |
                    |    QLIST_ENTRY(RAMBlock)  |
                    +---------------------------+
                    |offset                     |
                    |used_length                |
                    |max_length                 |
                    |    (ram_addr_t)           |
                    +---------------------------+
                    |host                       |   HVA
                    |    (uint8_t *)            |
                    +---------------------------+
                    |mr                         |
                    |    (struct MemoryRegion *)|
                    +---------------------------+
```

## Protocole d'échange ##

Distinction entre deux types de périphériques :
* Itératifs : Périphérique avec un grand volume de données. 
* Non-itératifs (la plupart) :  les données sont envoyées après la phase de précopie lorsque les CPUs sont stoppés
 


Le protocole d'échange est utilisé pour envoyer des objets depuis la machine virtuelle source vers la destination au sein d'un flux. Chaque objet peut être envoyé en de multiples parties encapsulée au sein de sections délimitées par des constantes numériques afin de multiplexer l'envoi de parties d'objets.

Constantes qui servent à délimiter les échanges :

| Constante              | Valeur |
|------------------------|--------|
| QEMU_VM_EOF            | 0x00   | 
| QEMU_VM_SECTION_START  | 0x01   | 
| QEMU_VM_SECTION_PART   | 0x02   | 
| QEMU_VM_SECTION_END    | 0x03   | 
| QEMU_VM_SECTION_FULL   | 0x04   | 
| QEMU_VM_SUBSECTION     | 0x05   |
| QEMU_VM_VMDESCRIPTION  | 0x06   | 
| QEMU_VM_CONFIGURATION  | 0x07   | 
| QEMU_VM_COMMAND        | 0x08   |
| QEMU_VM_SECTION_FOOTER | 0x7e   | 

On distingue les constantes qui permettent d'ouvrir un nouveau stream destiné à l'envoi d'un device (`QEMU_VM_SECTION_START`, `QEMU_VM_SECTION_FULL`) des autres constantes qui font référence à un stream

Exemple de scénario d'échange :
```
---------------------------------------------------------
| QEMU_VM_FILE_MAGIC        | File magic                |
|---------------------------|---------------------------|
| QEMU_VM_FILE_VERSION      | Version (has to be v3)    |
|---------------------------|---------------------------|
| QEMU_VM_CONFIGURATION     | Configuration optionnelle |
|---------------------------|---------------------------|
|                           |                           |
| QEMU_VM_SECTION_START     | Sections containing VM    |
| QEMU_VM_SECTION_FOOTER    | Data (RAM, Device)        |
|                           |                           |
| QEMU_VM_SECTION_PART      |                           |
| QEMU_VM_SECTION_FOOTER    |                           |
| QEMU_VM_SECTION_PART      |                           |
| QEMU_VM_SECTION_FOOTER    |                           |
|                           |                           |
| QEMU_VM_SECTION_END       |                           |
| QEMU_VM_SECTION_FOOTER    |                           |
|                           |                           |
| QEMU_VM_SECTION_FULL      |                           |
| QEMU_VM_SECTION_FOOTER    |                           |
|                           |                           |
|---------------------------|---------------------------|
| QEMU_VM_EOF               | Enf Of Sections           |
|---------------------------|---------------------------|
| QEMU_VM_VMDESCRIPTION     |                           |
|                           | VMSD description :        |
|                           | JSON décrivant le format  |
|                           | différents devices de la  | 
|                           | VM (Nombre de champs,     |
|                           | taille des chanmps...)    |
|                           |                           |
---------------------------------------------------------
```

### QEMU_VM_CONFIGURATION ###

Description : envoie un descriptif de la configuration de la VM

Format :
```
    -------------------------------------------------------------------
    | QEMU_VM_CONFIGURATION  | uint8  |                               |
    | name_len               | uint32 | Longueur du nom de la machine |
    | name                   | char[] | Nom de la machine             |
    -------------------------------------------------------------------
```

Code émetteur :
```
savevm.c:   qemu_savevm_state_header()
savevm.c:       |-> qemu_put_byte(f, QEMU_VM_CONFIGURATION);
vmstate.c:          |-> vmstate_save_state(f, &vmstate_configuration, &savevm_state, 0)
```

Code réception
```
savevm.c:   qemu_loadvm_state(QEMUFile *f)
savevm.c:       |-> qemu_loadvm_state_header()
savevm.c:       |-> qemu_loadvm_state_setup()
savevm.c:       |-> qemu_loadvm_state_main()
savevm.c:           |-> qemu_loadvm_section_start_full
savevm.c:               |-> vmstate_load()
savevm.c:           |-> qemu_loadvm_section_part_end
savevm.c:               |-> vmstate_load()

savevm.c:   vmstate_load()
vmstate.c       |-> vmstate_load_state()
vmstate.c           |-> vmstate_subsection_load()
```

### QEMU_VM_SECTION_START ou QEMU_VM_SECTION_FULL ###

Description : sert à démarrer l'envoie d'une nouvelle instance d'objet.

Format :
```
    -----------------------------------------------------------------------------------------------
    | QEMU_VM_SECTION_START ou QEMU_VM_SECTION_FULL | uint8  | Type de section                    |
    | se->section_id                                | uint32 | identifiant unique de la section   |
    | strlen(se->idstr)                             | uint8  | longeur du nom de la section       |
    | se->idstr                                     | []     | nom du bloc de la section          |
    | se->instance_id                               | uint32 |                                    |
    | se->version_id                                | uint32 |                                    |
    | Data                                          |        | Données arbitraire dont le layout  |
    |                                               |        | dépend du couple idstr,instance_id |
    ------------RAMBLOCK_FOREACH(block)les données envoyées dans la section.
```
* `instance_id` : est utilisé pour identifier l'instance d'objet qui est envoyé

Le champ `section_id` permet d'identifier de manière unique l'instance de l'objet qui est envoyé.

QEMU_VM_SECTION_START est utilisé pour les devices envoyés en itératifs tandis que QEMU_VM_SECTION_FULL est utilisé pour les devices envoyés en non-itératif.

Code d'envoi :
```
migration.c : migration_thread()
savevm.c :          |-> qemu_savevm_state_setup(QEMUFile *f)
                            |-> save_section_header(f, se, QEMU_VM_SECTION_START)
```
```
savevm.c :          |-> qemu_savevm_state_complete_precopy_non_iterable(QEMUFile *f)
                            |-> save_section_header(f, se, QEMU_VM_SECTION_FULL)
```
```
savevm.c :          qemu_save_device_state(QEMUFile *f)
                        |-> save_section_header(f, se, QEMU_VM_SECTION_FULL);
```

Code de réception :
```
qemu_loadvm_state()
    |-> qemu_loadvm_state_main()
```

## QEMU_VM_SECTION_PART ou QEMU_VM_SECTION_END ##

Description : sert à envoyer une partie d'un objet dont les premières parties ont déjà été envoyées via une section QEMU_VM_SECTION_START.

Format :
```
    ---------------------------------------------------------------------------------------------
    | QEMU_VM_SECTION_PART or QEMU_VM_SECTION_END | uint8  |                                    |
    | se->section_id                              | uint32 |                                    |
    | Data                                        |        | Données arbitraire dont le layout  |
    |                                             |        | dépend du couple idstr,instance_id |
    ---------------------------------------------------------------------------------------------
```

Code d'envoi de QEMU_VM_SECTION_PART :
```
migration.c:    migration_thread()
migration.c:        |-> migration_iteration_run()
savevm.c :              |-> qemu_savevm_state_iterate()
savevm.c :                  |-> save_section_header(f, se, QEMU_VM_SECTION_PART);
```

Code d'envoi de QEMU_VM_SECTION_END :
```
savevm.c : qemu_savevm_state_complete_precopy_iterable
    |-> save_section_header(f, se, QEMU_VM_SECTION_END);
        |-> qemu_put_byte(f, QEMU_VM_SECTION_END);
        |-> qemu_put_be32(f, se->section_id);

savevm.c : qemu_savevm_state_complete_postcopy
    |-> qemu_put_byte(f, QEMU_VM_SECTION_END);
    |-> qemu_put_be32(f, se->section_id);
```

### QEMU_VM_SECTION_FOOTER ###

Description : Utilisé systématiquement après les données envoyées après une balise de type :
* `QEMU_VM_SECTION_START`
* `QEMU_VM_SECTION_PART`
* `QEMU_VM_SECTION_FULL`
* `QEMU_VM_SECTION_END`

Format :
```
    ----------------------------------------------------------------------------------------
    | QEMU_VM_SECTION_FOOTER | uint8  |                                                    |
    | se->section_id         | uint32 | Section id that must match the header's section id |
    ----------------------------------------------------------------------------------------
```

Code d'envoi :

```
savevm.c : save_section_footer
```

Code de réception :

```
savevm.c : check_section_footer
```

### QEMU_VM_SUBSECTION ###

The most common structure change is adding new data, e.g. when adding  a newer form of device, or adding that state that you previously  forgot to migrate.  This is best solved using a subsection.

A subsection is "like" a device vmstate, but with a particularity, it  has a Boolean function that tells if that values are needed to be sent  or not.  If this functions returns false, the subsection is not sent.  Subsections have a unique name, that is looked for on the receiving  side.

```
Format :

    --------------------------------------------------
    | QEMU_VM_SUBSECTION | uint8  |                  |
    | len                | uint8  | Longeur du nom   |
    | name               | []     | nom              |
    | version_id         | uint32 |                  |
    --------------------------------------------------
```

```
    vmstate_save_state_v
        Save Fileds
        vmstate_subsection_save
```

### QEMU_VM_VMDESCRIPTION ###

Description : description des instance d'objets envoyés au format json.

Format :
```
    -----------------------------------------------------------------
    | QEMU_VM_VMDESCRIPTION | uint8  |                              |
    | len                   | uint32 | Longeur du nom               |
    | vmdesc                | []     | Description de la VM en json |
    -----------------------------------------------------------------
```

### QEMU_VM_COMMAND ###

QEMU_VM_COMMAND section type is for sending commands from source to destination.  

These commands are not intended to convey guest state but to control the migration process.

For use in postcopy.

| Constante              | Valeur |
|------------------------|--------|
| MIG_CMD_INVALID				| Must be 0   | 
| MIG_CMD_OPEN_RETURN_PATH		| Tell the dest to open the Return path   | 
| MIG_CMD_PING   				| Request a PONG on the RP   | 
| MIG_CMD_POSTCOPY_ADVISE    	|  Prior to any page transfers, just warn we might want to do PC  | 
| MIG_CMD_POSTCOPY_LISTEN   	| Start listening for incoming pages as it's running.   | 
| MIG_CMD_POSTCOPY_RUN     		| Start execution   |
| MIG_CMD_POSTCOPY_RAM_DISCARD  | A list of pages to discard that were previously sent during precopy but are dirty.   | 
| MIG_CMD_PACKAGED  			| Send a wrapped stream within this stream   | 
| MIG_CMD_ENABLE_COLO        	| Enable COLO   |
| MIG_CMD_POSTCOPY_RESUME 		| resume postcopy on dest   | 
| MIG_CMD_RECV_BITMAP 			| Request for recved bitmap on dst   | 
| MIG_CMD_MAX 					|    | 


``` 


static int loadvm_process_command(QEMUFile *f)
{
    MigrationIncomingState *mis = migration_incoming_get_current();
    uint16_t cmd;
    uint16_t len;
    uint32_t tmp32;

    cmd = qemu_get_be16(f);
    len = qemu_get_be16(f);

    /* Check validity before continue processing of cmds */
    if (qemu_file_get_error(f)) {
        return qemu_file_get_error(f);
    }

    trace_loadvm_process_command(cmd, len);
    if (cmd >= MIG_CMD_MAX || cmd == MIG_CMD_INVALID) {
        error_report("MIG_CMD 0x%x unknown (len 0x%x)", cmd, len);
        return -EINVAL;
    }

    if (mig_cmd_args[cmd].len != -1 && mig_cmd_args[cmd].len != len) {
        error_report("%s received with bad length - expecting %zu, got %d",
                     mig_cmd_args[cmd].name,
                     (size_t)mig_cmd_args[cmd].len, len);
        return -ERANGE;
    }

    switch (cmd) {
    case MIG_CMD_OPEN_RETURN_PATH:
        if (mis->to_src_file) {
            error_report("CMD_OPEN_RETURN_PATH called when RP already open");
            /* Not really a problem, so don't give up */
            return 0;
        }
        mis->to_src_file = qemu_file_get_return_path(f);
        if (!mis->to_src_file) {
            error_report("CMD_OPEN_RETURN_PATH failed");
            return -1;
        }
        break;

    case MIG_CMD_PING:
        tmp32 = qemu_get_be32(f);
        trace_loadvm_process_command_ping(tmp32);
        if (!mis->to_src_file) {
            error_report("CMD_PING (0x%x) received with no return path",
                         tmp32);
            return -1;
        }
        migrate_send_rp_pong(mis, tmp32);
        break;

    case MIG_CMD_PACKAGED:
        return loadvm_handle_cmd_packaged(mis);

    case MIG_CMD_POSTCOPY_ADVISE:
        return loadvm_postcopy_handle_advise(mis, len);

    case MIG_CMD_POSTCOPY_LISTEN:
        return loadvm_postcopy_handle_listen(mis);

    case MIG_CMD_POSTCOPY_RUN:
        return loadvm_postcopy_handle_run(mis);

    case MIG_CMD_POSTCOPY_RAM_DISCARD:
        return loadvm_postcopy_ram_handle_discard(mis, len);

    case MIG_CMD_POSTCOPY_RESUME:
        return loadvm_postcopy_handle_resume(mis);

    case MIG_CMD_RECV_BITMAP:
        return loadvm_handle_recv_bitmap(mis, len);

    case MIG_CMD_ENABLE_COLO:
        return loadvm_process_enable_colo(mis);
    }

    return 0;
}
```
## RAM Instance ##

La mémoire est décrite sous forme d'un ensemble de zone chaque zone ayant :
* Un nom
* Une taille
* Un tableau de données

La transmission de la liste des zones est fait par l'envoi d'un message
flagué RAM_SAVE_FLAG_MEM_SIZE suivi d'un tableau de description de chaque
zone (nom et taille)

La transmission des données est fait par l'envoi d'un message de type
* RAM_SAVE_FLAG_PAGE pour écrire une page de données
* RAM_SAVE_FLAG_ZERO pour écrire une page de zero
* RAM_SAVE_FLAG_COMPRESS_PAGE pour écrire une page de données compressée
* RAM_SAVE_FLAG_XBZRLE pour écrire une page de données compressée en utilisant XBZRLE

Le message contient
1. soit :
* Le nom de la zone mémoire réceptrice des données
* Le flag RAM_SAVE_FLAG_CONTINUE pour indiquer que la page transférée
doit être écrite dans la même zone mémoire que les pages transférées
précédemment.
2. L'offset auquel les données doivent être écrites

```
static SaveVMHandlers savevm_ram_handlers = {
    .save_setup = ram_save_setup,
    .save_live_iterate = ram_save_iterate,
    .save_live_complete_postcopy = ram_save_complete,
    .save_live_complete_precopy = ram_save_complete,
    .has_postcopy = ram_has_postcopy,
    .save_live_pending = ram_save_pending,
    .load_state = ram_load,
    .save_cleanup = ram_save_cleanup,
    .load_setup = ram_load_setup,
    .load_cleanup = ram_load_cleanup,
    .resume_prepare = ram_resume_prepare,
};
```

### Liste des zones ###

Envoie la configuration (nom, et taille) des zones de mémoire physique de la VM.

Envoi du flag :
```
    ----------------------------------------------------------------------
    | header | ram_bytes_total_common OR RAM_SAVE_FLAG_MEM_SIZE | uint64 |
    ----------------------------------------------------------------------
```

Envoi de la description de la mémoire physique zone de mémoire par zone de mémoire :

```
    -------------------------------------------------------------------------------
    | block  | strlen(block->idstr)   | uint8  | longeur de l'identifiant         |
    |        | block->idstr           |        | identifiant du bloc              |
    |        | block->used_length     | uint64 | taille du block                  |
if (migrate_postcopy_ram && block->page_size != qemu_host_page_size) {
    |        | block->page_size       | uint64 |                                  |
}
if(migrate_ignore_shared()) {
    |        | block->mr->addr        | uint64 | Adresse physique du bloc mémoire |
}
    -------------------------------------------------------------------------------
    | block  |                        |       |                                   |
    | ....   |                        |       |                                   |
    -------------------------------------------------------------------------------
```

Envoi du flag de fin :
```
    -------------------------------------------------------------------------------
    | end    | RAM_SAVE_FLAG_EOS      | uint64 |                                  |
    -------------------------------------------------------------------------------
```

Exemple :
```
name=0000:00:02.0/vga.vram
length=16777216

name=/rom@etc/acpi/tables
length=131072

name=pc.bios
length=262144

name=0000:00:03.0/e1000.rom
length=262144

name=pc.rom
length=131072

name=0000:00:02.0/vga.rom
length=65536

name=/rom@etc/table-loader
length=4096

name=/rom@etc/acpi/rsdp
length=4096

name=0000:00:02.0/vga.vram
length=16777216
```

Sender :
`ram_save_setup()`

Receiver :
```
ram_load()
    if (postcopy_running) {
        ret = ram_load_postcopy(f);
    } else {
        ret = ram_load_precopy(f);
    }
```

### Transmission des données ###

#### RAM_SAVE_FLAG_PAGE | RAM_SAVE_FLAG_CONTINUE ####

Envoi d'une zone de mémoire :

```
    ------------------------------------------------------------------------------------------------
    | header | RAM_SAVE_FLAG_PAGE OR RAM_SAVE_FLAG_CONTINUE | uint64    |                          |
    ------------------------------------------------------------------------------------------------
if (flags & RAM_SAVE_FLAG_CONTINUE) {
} else {
    ------------------------------------------------------------------------------------------------
    | block  | strlen(block->idstr)                         | uint8     | longeur de l'identifiant |
    |        | block->idstr                                 |           | identifiant du bloc      |
    |        | data                                         | PAGE_SIZE | Une page de données      |
    ------------------------------------------------------------------------------------------------
}
```

Sender :
```
save_normal_page()

    ram_counters.transferred += save_page_header(rs, rs->f, block,
                                                 offset | RAM_SAVE_FLAG_PAGE);

    save_page_header
        if (block == rs->last_sent_block) {
            offset |= RAM_SAVE_FLAG_CONTINUE;
        }
        qemu_put_be64(f, offset);

        if (!(offset & RAM_SAVE_FLAG_CONTINUE)) {
            len = strlen(block->idstr);
            qemu_put_byte(f, len);
            qemu_put_buffer(f, (uint8_t *)block->idstr, len);
            size += 1 + len;
            rs->last_sent_block = block;
        }

    qemu_put_buffer(rs->f, buf, TARGET_PAGE_SIZE);
```

Receiver :
```
ram_load()
    if (postcopy_running) {
        ret = ram_load_postcopy(f);
    } else {
        ret = ram_load_precopy(f);
    }
```

#### RAM_SAVE_FLAG_ZERO | RAM_SAVE_FLAG_CONTINUE ####

Envoi d'une zone de mémoire à 0 :

```
    -----------------------------------------------------------------------------------------------------
    | header | RAM_SAVE_FLAG_ZERO OR RAM_SAVE_FLAG_CONTINUE | uint64 |                                  |
    -----------------------------------------------------------------------------------------------------
if (flags & RAM_SAVE_FLAG_CONTINUE) {
} else {
    -----------------------------------------------------------------------------------------------------
    | block  | strlen(block->idstr)                         | uint8  | longeur de l'identifiant         |
    |        | block->idstr                                 |        | identifiant du bloc              |
    -----------------------------------------------------------------------------------------------------
}
    ------------------------------------------------------------------------------------------------------
    |        | 0                                            | uint8  | char utilisé pour remplir la page |
    ------------------------------------------------------------------------------------------------------
```

Sender :
```
save_zero_page_to_file

    if (is_zero_range(p, TARGET_PAGE_SIZE)) {
        len += save_page_header(rs, file, block, offset | RAM_SAVE_FLAG_ZERO);

    save_page_header
        if (block == rs->last_sent_block) {
            offset |= RAM_SAVE_FLAG_CONTINUE;
        }
        qemu_put_be64(f, offset);

        if (!(offset & RAM_SAVE_FLAG_CONTINUE)) {
            len = strlen(block->idstr);
            qemu_put_byte(f, len);
            qemu_put_buffer(f, (uint8_t *)block->idstr, len);
            size += 1 + len;
            rs->last_sent_block = block;
        }

        qemu_put_byte(file, 0);
        len += 1;
    }
    return len;
```

Receiver :
```
ram_load()unsigned long int
        ret = ram_load_precopy(f);
    }
```

## Code analysis ##

### Sender ###

Une structure de donnée de type `SaveStateEntry` est allouée pour chaque objet qui doit être migré. Elle est insérée dans une liste contenue dans une globale `savevm_state` de type `SaveState`. La migration est effectuée en parcourant chaque entrée de la liste pour effectuer la migration. Les opérations de migrations de chaque objet peuvent être encodés de deux manière différente :
* Par une structure de type `SaveVMHandlers` contenue dans le champs `ops` du `SaveState` qui contient un ensemble de pointeur de fonctions utilisés au cours du processus de migration
* Par une structure de type `VMStateDescription` contenue dans le champs `vmsd` qui permet d'encoder de manière générique n'importe quelle structure de données en C.

Modélise chaque objet du système qui veut s'enregistrer pour être migré :
```
typedef struct SaveStateEntry {
    union { struct SaveStateEntry *tqe_next; QTailQLink tqe_circ; } entry;
    char idstr[256];
    uint32_t instance_id;
    int alias_id;
    int version_id;

    int load_version_id;
    int section_id;

    int load_section_id;
    const SaveVMHandlers *ops;
    const VMStateDescription *vmsd;
    void *opaque;
    CompatEntry *compat;
    int is_ram;
} SaveStateEntry;
```

Contient la liste des objets à migrer :
```
typedef struct SaveState {
    // Cntient la liste des handlers a enregistrer
    union { struct SaveStateEntry *tqh_first; QTailQLink tqh_circ; } handlers;  // Liste des structures en attentes de migration
    SaveStateEntry *handler_pri_head[MIG_PRI_MAX + 1];
    int global_section_id;
    uint32_t len;
    const char *name;
    uint32_t target_page_bits;
    uint32_t caps_count;
    MigrationCapability *capabilities;
    QemuUUID uuid;
} SaveState;

static struct SaveState savevm_state;
```

Schéma de la liste des objets à migrer :
```
    SaveState(savevm_state)
    +--------------------------------------+
    |global_section_id                     |
    |     (int)                            |
    |name                                  |
    |     (char*)                          |
    |len                                   |
    |target_page_bits                      |
    |caps_count                            |
    |     (uint32_t)                       |
    +--------------------------------------+
    |capabilities                          |
    |     (MigrationCapability*)           |
    +--------------------------------------+
    |handlers                              |
    |     (list of SaveStateEntry)         |
    +--------------------------------------+
            	|
                |
                |                                                                                   
                |                                                                                  
          SaveStateEntry                          SaveStateEntry                       SaveStateEntry                 
    +-----------------------------+      +-----------------------------+      +------------------------------------+
    |idstr                        |      |idstr                        |      |idstr                               |
    |     = "block"               |      |     = "ram"                 |      |     = "dirty-bitmap"               |
    |ops                          |      |ops                          |      |ops                                 |
    |     = savevm_block_handlers |      |     = savevm_ram_handlers   |      |     = savevm_dirty_bitmap_handlers |
    |opaque                       |----->|opaque                       |----->|opaque                              |
    |     = block_mig_state       |      |     = ram_state             |      |     = dirty_bitmap_mig_state       |
    |vmsd                         |      |vmsd                         |      |vmsd                                |
    |     = NULL                  |      |     = NULL                  |      |     = NULL                         |
    +-----------------------------+      +-----------------------------+      +------------------------------------+
```

Code utilisé par les périphériques émulés pour s'enregistrer auprès de la liste d'objet à migrer. Le handler `register_savevm_live` est utilisé par le code legacy :
```
savevm.c:   register_savevm_live(const char *idstr, uint32_t instance_id, int version_id,
                                 const SaveVMHandlers  *ops, void *opaque))
savevm.c:       |-> se = g_new0(SaveStateEntry, 1);
savevm.c:       |-> se->version_id = version_id;
savevm.c:       |-> se->section_id = savevm_state.global_section_id++;
savevm.c:       |-> [...]
savevm.c:       |-> savevm_state_handler_insert(se);
savevm.c:           |-> QTAILQ_INSERT_TAIL(&savevm_state.handlers, nse, entry);

savevm.c:   vmstate_register_with_alias_id(VMStateIf *obj, uint32_t instance_id,
                                   const VMStateDescription *vmsd, void *opaque, int alias_id,
                                   int required_for_version, Error **errp)
savevm.c:       |-> se = g_new0(SaveStateEntry, 1);
savevm.c:       |-> se->version_id = vmsd->version_id;
savevm.c:       |-> [...]
savevm.c:       |-> savevm_state_handler_insert(se);
savevm.c:           |-> QTAILQ_INSERT_TAIL(&savevm_state.handlers, nse, entry);
```

Stack de code de migration depuis la ligne de commande jusqu'au thread principal :
```
hmp-cmds.c: hmp_migrate()
migration.c:    |-> qmp_migrate()
migration.c:        |-> migrate_prepare()
migration.c:            |-> migrate_init()
migration.c:        |-> socket_start_outgoing_migration()
socket.c:               |-> socket_start_outgoing_migration_internal()
socket.c:                   |-> socket_outgoing_migration()
channel.c:                      |-> migration_channel_connect()
migration.c:                        |-> migrate_fd_connect()
migration.c:                            |-> qemu_thread_create(migration_thread)
migration.c:                                |-> migration_thread()
migration.c:                                        Do the migration stuff
```

#### Opération d'envoi : `SaveVMHandlers` ####

Modélise les opérations à effectuer pour migrer un objet : 
```
typedef void SaveStateHandler(QEMUFile *f, void *opaque);

typedef struct SaveVMHandlers {
    /* This runs inside the iothread lock.  */
    SaveStateHandler *save_state;

    void (*save_cleanup)(void *opaque);
    int (*save_live_complete_postcopy)(QEMUFile *f, void *opaque);
    int (*save_live_complete_precopy)(QEMUFile *f, void *opaque);

    /* This runs both outside and inside the iothread lock.  */
    bool (*is_active)(void *opaque);
    bool (*has_postcopy)(void *opaque);

    /* is_active_iterate
     * If it is not NULL then qemu_savevm_state_iterate will skip iteration if
     * it returns false. For example, it is needed for only-postcopy-states,
     * which needs to be handled by qemu_savevm_state_setup and
     * qemu_savevm_state_pending, but do not need iterations until not in
     * postcopy stage.
     */
    bool (*is_active_iterate)(void *opaque);

    /* This runs outside the iothread lock in the migration case, and
     * within the lock in the savevm case.  The callback had better only
     * use data that is local to the migration thread or protected
     * by other locks.
     */
    int (*save_live_iterate)(QEMUFile *f, void *opaque);

    /* This runs outside the iothread lock!  */
    int (*save_setup)(QEMUFile *f, void *opaque);
    void (*save_live_pending)(QEMUFile *f, void *opaque,
                              uint64_t threshold_size,
                              uint64_t *res_precopy_only,
                              uint64_t *res_compatible,
                              uint64_t *res_postcopy_only);
    /* Note for save_live_pending:
     * - res_precopy_only is for data which must be migrated in precopy phase
     *     or in stopped state, in other words - before target vm start
     * - res_compatible is for data which may be migrated in any phase
     * - res_postcopy_only is for data which must be migrated in postcopy phase
     *     or in stopped state, in other words - after source vm stop
     *
     * Sum of res_postcopy_only, res_compatible and res_postcopy_only is the
     * whole amount of pending data.
     */

    LoadStateHandler *load_state;
    int (*load_setup)(QEMUFile *f, void *opaque);
    int (*load_cleanup)(void *opaque);
    /* Called when postcopy migration wants to resume from failure */
    int (*resume_prepare)(MigrationState *s, void *opaque);
} SaveVMHandlers;
```

Pile d'appel du thread de migration :
```
migration_thread()

    qemu_savevm_state_header(f);
        => QEMU_VM_FILE_MAGIC
        => QEMU_VM_FILE_VERSION
        if configured
            => QEMU_VM_CONFIGURATION

    qemu_savevm_state_setup(f);
    
        QTAILQ_FOREACH(se, &savevm_state.handlers, entry) {
            if (!se->ops || !se->ops->save_setup)
                continue 
            
            if (se->ops->is_active && !se->ops->is_active(se->opaque))
                continue

            => QEMU_VM_SECTION_START
            ret = se->ops->save_setup(f, se->opaque);
            => QEMU_VM_SECTION_FOOTER
        }

    while (migration_is_active(s)) {
        migration_iteration_run()
            qemu_savevm_state_iterate(f, false)
                QTAILQ_FOREACH(se, &savevm_state.handlers, entry) {

                    if (!se->ops || !se->ops->save_live_iterate)
                        continue

                    if (se->ops->is_active && !se->ops->is_active(se->opaque))
                        continue

                    if (se->ops->is_active_iterate && !se->ops->is_active_iterate(se->opaque))
                        continue

                    if (postcopy && !(se->ops->has_postcopy && se->ops->has_postcopy(se->opaque))) 
                        continue

                    => QEMU_VM_SECTION_PART
                    ret = se->ops->save_live_iterate(f, se->opaque);
                    => QEMU_VM_SECTION_FOOTER

    migration_completion(s);
        qemu_savevm_state_complete_precopy
            qemu_savevm_state_complete_precopy_iterable
                QTAILQ_FOREACH(se, &savevm_state.handlers, entry) {

                    if (!se->ops || !se->ops->save_live_complete_precopy)
                        continue;

                    if (in_postcopy && se->ops->has_postcopy && se->ops->has_postcopy(se->opaque))
                        continue;

                    if (se->ops->is_active && !se->ops->is_active(se->opaque))
                        continue

                    => QEMU_VM_SECTION_END
                    ret = se->ops->save_live_complete_precopy(f, se->opaque);
                    => QEMU_VM_SECTION_FOOTER
            
            qemu_savevm_state_complete_precopy_non_iterable

                if ((!se->ops || !se->ops->save_state) && !se->vmsd)
                    continue;

                if (se->vmsd && !(vmsd->needed && !vmsd->needed(opaque)))
                    continue;

                => QEMU_VM_SECTION_FULL
                vmstate_save()
                    if (!se->vmsd) {
                        vmstate_save_old_style()
                            se->ops->save_state(f, se->opaque);
                    } else {
                        vmstate_save_state()
                            vmstate_save_state_v()
                                vmstate_subsection_save()
                                FOR EACH SUBSECTION
                                    QEMU_VM_SUBSECTION
                                    vmstate_save_state
                    }
                    
                => QEMU_VM_SECTION_FOOTER

        qemu_savevm_state_complete_postcopy
            QTAILQ_FOREACH(se, &savevm_state.handlers, entry) {

                if (!se->ops || !se->ops->save_live_complete_postcopy)
                    continue;
    
                if (se->ops->is_active) && !se->ops->is_active(se->opaque))
                    continue;

                => QEMU_VM_SECTION_END
                ret = se->ops->save_live_complete_postcopy(f, se->opaque);
                => QEMU_VM_SECTION_FOOTER
                }

            => QEMU_VM_EOF
```

`QEMUFile *f` : Modélise un flux utilisé pour dumper les données.
The files, sockets or fd's that carry the migration stream are abstracted by
the  ``QEMUFile`` type (see `migration/qemu-file.h`).  In most cases this
is connected to a subtype of ``QIOChannel`` (see `io/`).

#### Encodage générique : `VMStateDescription` ####

Les structures de données de type `struct VMStateDescription` et `struct VMStateField`sont utilisées pour encoder de manière générique un ensemble de données à envoyer. Le principe utilisé consiste à encoder dans chaque `structre VMStateField` des informations (offset, taille...) permettant de lire et d'envoyer un champ contenu dans une structure de type arbitraire.

```
struct VMStateDescription {
    const char *name;
    int version_id;
    int (*pre_load)(void *opaque);
    int (*post_load)(void *opaque, int version_id);
    int (*pre_save)(void *opaque);
    VMStateField *fields;
};

struct VMStateField {
    const char *name;
    const char *err_hint;
    size_t offset;
    size_t size;
    size_t start;
    int num;
    size_t num_offset;
    size_t size_offset;
    const VMStateInfo *info;
    enum VMStateFlags flags;
    const VMStateDescription *vmsd;
    int version_id;
    int struct_version_id;
    bool (*field_exists)(void *opaque, int version_id);
};
```

Exemple avec `QEMU_VM_CONFIGURATION`.

Structure contenant les informations à envoyer :
```
typedef struct SaveState {
    QTAILQ_HEAD(, SaveStateEntry) handlers;
    SaveStateEntry *handler_pri_head[MIG_PRI_MAX + 1];
    int global_section_id;
    uint32_t Ne transmettez pas directement le contenu de chaque page, mais transmettez la différence de chaque page 
Initialisation de la structure `VMStateDescription`. Le champ `fields` est utilisé pour décrire les champs `len` et `name` de la structure `SaveState` qui seront encodés :
```
```

static const VMStateDescription vmstate_configuration = {
    .name = "configuration",
    .version_id = 1,
    .pre_load = configuration_pre_load,
    .post_load = configuration_post_load,
    .pre_save = configuration_pre_save,
    .fields = (VMStateField[]) {
        VMSTATE_UINT32(len, SaveState),
        VMSTATE_VBUFFER_ALLOC_UINT32(name, SaveState, 0, NULL, len),
        VMSTATE_END_OF_LIST()
    },
    .subsections = (const VMStateDescription *[]) {
        &vmstate_target_page_bits,
        &vmstate_capabilites,
        &vmstate_uuid,
        NULL
    }
};
```

Schéma :
Representation
```
    +--------------------------------------+
    |vmsd                                  |
    |    (VMStateDescription *)            |
    |     +--------------------------------+
    |     |name                            |
    |     |    (char *)                    |
    |     +--------------------------------+
    |     |version_id                      |
    |     |minimum_version_id              |
    |     |minimum_version_id_old          |
    |     |    (int)                       |
    |     +--------------------------------+
    |     |unmigratable                    |
    |     |    (int)                       |
    |     +--------------------------------+
    |     |priority                        |
    |     |    (MigrationPriority)         |
    |     +--------------------------------+
    |     |load_state_old                  |
    |     |pre_load                        |
    |     |post_load                       |
    |     |pre_save                        |
    |     |post_save                       |
    |     |needed                          |
    |     |    bool (*)()                  |
    |     +--------------------------------+
    |     |fields                          |
    |     |    (VMStateField *)            |
    |     |    +---------------------------+
    |     |    |flags                      | 
    |     |    |    (VMStateFlags)         |
    |     |    |                           |
    |     |    |name                       |
    |     |    |offset                     |
    |     |    |start                      |
    |     |    |                           |
    |     |    |size                       |
    |     |    |size_offset                |
    |     |    |                           |
    |     |    |num                        |
    |     |    |num_offset                 |
    |     |    |                           |
    |     |    |version_id                 |
    |     |    |struct_version_id          |
    |     |    |field_exists               |
    |     |    |                           |
    |     |    |vmsd                       |
    |     |    |    (VMStateDescription*)  |
    |     |    |                           |
    |     |    |info                       |
    |     |    |    (VMStateInfo *)        |
    |     |    |    +----------------------+
    |     |    |    |name                  |
    |     |    |    |get                   |
    |     |    |    |put                   |
    |     +----+----+----------------------+
    |     |subsections                     |
    |     |    (VMStateDescription **)     |
    +-----+--------------------------------+
```


```
    SaveStateEntry
    +--------------------------------------+
    |opaque                                |
    |    (void *)                      ----|--->+-+----+----+----+----+----+----+----+----+----+------------------+
    |                                      |    | |elem|elem|elem|elem|elem|elem|elem|elem|elem|                  |
    |                                      |    +-+----+----+----+----+----+----+----+----+----+------------------+
    |                                      |      ^                                                  ^
    |                                      |      |                                                  |                                                                               
    |                                      |      |                                                  |                                                                               
    |                                      |      |        field                                     |        field                                                                  
    +--------------------------------------+      +----------------+                                 +----------------+                                                              
    |vmsd                                  |                       |                                                  |
    |    (VMStateDescription *)        ----|--->+--------------------------------+                 +--------------------------------+
    +--------------------------------------+    |fields            |             |                 |fields            |             |
    |subsections                           |    |(VMStateField *)  |             |                 |(VMStateField *)  |             |
    |    (VMStateDescription **)           |    |    +---------------------------+                 |    +---------------------------+
    +--------------------------------------+    |    |name         |             |                 |    |name         |             |
                                                |    |offset   ----+             |                 |    |offset   ----+             |
                                                |    |start                      |                 |    |start                      |
                                                |    |                           |                 |    |                           |
                                                |    |size                       |  => size        |    |size                       |  => size
                                                |    |size_offset                |                 |    |size_offset                |
                                                |    |                           |                 |    |                           |
                                                |    |num                        |  => n_elems     |    |num                        |  => n_elems
                                                |    |num_offset                 |                 |    |num_offset                 |
                                                |    |                           |                 |    |                           |
                                                |    |version_id                 |                 |    |version_id                 |
                                                |    |struct_version_id          |                 |    |struct_version_id          |
                                                |    |field_exists               |                 |    |field_exists               |
                                                |    |                           |                 |    |                           |
                                                |    |vmsd                       |                 |    |vmsd                       |
                                                |    |    (VMStateDescription*)  |                 |    |    (VMStateDescription*)  |
                                                |    |                           |                 |    |                           |
                                                |    |info                       |                 |    |info                       |
                                                |    |    (VMStateInfo *)        |                 |    |    (VMStateInfo *)        |
                                                |    |    +----------------------+                 |    |    +----------------------+
                                                |    |    |name                  |                 |    |    |name                  |
                                                |    |    |get                   |                 |    |    |get                   |
                                                |    |    |put                   |                 |    |    |put                   |
                                                +----+----+----------------------+                 +----+----+----------------------+
```
* Quelques points:
	* vmsd contient un tableau de champs, chaque élément est une structure VMStateField
	* chaque champ contient de plusieurs éléments, dont le  nombre est déterminé par num / num_offset et sa taille est déterminée par size / size_offset
	* L'index de départ des éléments est déterminé par l'offset dans l'espace pointé par le pointeur opaque.

Code source :
```
savevm.c:   qemu_savevm_state_header()
savevm.c:       |-> qemu_put_byte(f, QEMU_VM_CONFIGURATION);
vmstate.c:          |-> vmstate_save_state(f, &vmstate_configuration, &savevm_state, 0)
vmstate.c:              |-> vmstate_save_state_v
vmstate.c:                  if (vmsd->pre_save) {
                                ret = vmsd->pre_save(&savevm_state);    // Initialise les champs 
                                                                        // de la structure SaveState
                            }
savevm.c:                       configuration_pre_save()
savevm.c:                           |-> state->name = current_name;

vmstate.c:                  while (field->name) {                       // Iter sur les fields à envoyer
vmstate.c:                  }
```
