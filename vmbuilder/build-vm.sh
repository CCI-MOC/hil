#!/bin/bash

# We can't have comments after a "\" character, which is annoying for
# long commands like below. This is a dirty hack to let us put comments
# inline. Note that you have to be careful with what characters you use;
# words like "don't" cause problems with shell interpolation, since
# these aren't actual comments.
NB() {
	:
}

vmbuilder kvm ubuntu \
	--suite precise   `NB Use ubuntu 12.04.`                             \
	--flavour virtual `NB Use the virtual appliance kernel.`             \
	--arch i386       `NB No need for long mode on a machine this size.` \
	--mem $RAM        `NB This should be plenty of memory.`              \
	`NB --part expects a filename, but it seems silly to make a separate`\
	`NB file for this. the '<(command)' bash extension allows us to get` \
	`NB around this.` \
	--part <(printf '
root 8000
swap 1000
/var 1000
' ) `NB We provide a 10G disk, with 1G /var, 1G swap, and the rest is /.` \
	--hostname moc-headnode	\
	\
	`NB These are defaults - the user should change them on first login.` \
	--user mocuser \
	--name mocuser \
	--pass r00tme `NB Hint hint.` \
	\
	`NB Extra packages: ` \
	--addpkg acpid `NB This lets the vm respond to acpi shutdown. ` \
	-o `NB overwrite old image`
