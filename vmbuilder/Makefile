DISK_NAME = base-headnode.img
DISK_TARG = /var/lib/libvirt/images/$(DISK_NAME)

VIRT_USER = libvirt-qemu
VIRT_GROUP = kvm

all: $(DISK_NAME)

install: image.xml $(DISK_TARG)
	virt-image \
		--noreboot \
		--replace \
		--vnc \
		--ram 512 \
		image.xml

$(DISK_TARG): $(DISK_NAME)
	install -m600 $< $@ -o $(VIRT_USER) -g $(VIRT_GROUP)

$(DISK_NAME): build-vm.sh
	./$<
	mv ubuntu-kvm/*.qcow2 $@
clean:
	rm -rf $(DISK_NAME) ubuntu-kvm
