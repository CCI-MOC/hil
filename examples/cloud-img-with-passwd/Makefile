# Copyright 2014-2015 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

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
