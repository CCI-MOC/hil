DISK_NAME = base-headnode.img
DISK_TARG = /var/lib/libvirt/images/$(DISK_NAME)

include config.mak

VIRT_USER ?= libvirt-qemu
VIRT_GROUP ?= kvm

RAM = 512

all: $(DISK_NAME)

install: image.xml $(DISK_TARG)
	virt-image \
		--noreboot \
		--replace \
		--vnc \
		--ram $(RAM) \
		image.xml

$(DISK_TARG): $(DISK_NAME)
	install -m600 $< $@ -o $(VIRT_USER) -g $(VIRT_GROUP)

$(DISK_NAME): build-vm.sh
	RAM=$(RAM) ./$<
	mv ubuntu-kvm/*.qcow2 $@
clean:
	rm -rf $(DISK_NAME) ubuntu-kvm
