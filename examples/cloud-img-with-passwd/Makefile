# $(distro).mk defines IMG_IN and MIRROR.
include $(distro).mk

all: build
$(IMG_IN):
	wget $(MIRROR)/$(IMG_IN)
check: $(IMG_IN) SHA256SUMS.$(distro)
	sha256sum -c SHA256SUMS.$(distro)
$(IMG_IN).raw: $(IMG_IN)
	qemu-img convert -O raw $< $@
build: $(IMG_IN).raw
	mkdir mnt
	mount -o loop,offset=$$((512 * 2048)) $< mnt
	mount -t sysfs none mnt/sys
	mount -t proc none mnt/proc
	chroot mnt /usr/bin/passwd
	umount mnt/sys
	umount mnt/proc
	umount mnt
