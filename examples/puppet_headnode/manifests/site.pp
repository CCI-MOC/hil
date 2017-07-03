## Packages to be installed ##
package { [
    'isc-dhcp-server',
    'tftpd-hpa',
    'inetutils-inetd',
    'python-flask',
    'syslinux-common',
]:
  ensure  => present,
}

## Mount the Ubuntu ISO and copy files ##
file { "/mnt/iso":
  ensure => directory,
} ->
mount { "/mnt/iso":
  device => "/root/CentOS-6.6-x86_64-minimal.iso",
  fstype  => "iso9660",
  options  => "loop,ro",
  ensure  => mounted,
  atboot  => true,
}

## Files to be updated ##

# set interface configuration
file { '/etc/network/interfaces':
  ensure  => present,
  source  => "/root/hil/examples/puppet_headnode/manifests/static/interfaces",
}

file { '/etc/default/isc-dhcp-server':
  ensure  => present,
  source  => "/root/hil/examples/puppet_headnode/manifests/static/isc-dhcp-server",
  require => Package["isc-dhcp-server"]
}

# dhcp configuration
file { '/etc/dhcp/dhcpd.conf':
  ensure  => present,
  source  => "/root/hil/examples/puppet_headnode/manifests/static/dhcpd.conf",
  require => Package["isc-dhcp-server"],
  notify  => Service["isc-dhcp-server"]
}

# tftp configuration
file { "/etc/default/tftpd-hpa":
  ensure  => present,
  require => Package["tftpd-hpa"],
  source  => "/root/hil/examples/puppet_headnode/manifests/static/tftpd-hpa",
}

file { "/etc/inetd.conf":
  ensure  => present,
  require => Package["inetutils-inetd"],
  source  => "/root/hil/examples/puppet_headnode/manifests/static/inetd.conf",
}

# pxe configuration
file { "/var/lib/tftpboot/pxelinux.cfg":
  ensure => directory,
  require => Package["tftpd-hpa"],
} ->
file { "/var/lib/tftpboot/pxelinux.cfg/default":
  ensure  => present,
  source  => "/root/hil/examples/puppet_headnode/manifests/static/default",
}

$centosDir = "/var/lib/tftpboot/centos"
file { $centosDir :
  ensure => directory,
  require => Package["tftpd-hpa"],
}

file { "/var/lib/tftpboot/centos/pxelinux.cfg":
  ensure  => present,
  source  => "/root/hil/examples/puppet_headnode/manifests/static/pxelinux_cfg",
  require => File[$centosDir],
}

file { "/var/lib/tftpboot/centos/vmlinuz":
  ensure  => present,
  source  => "/mnt/iso/isolinux/vmlinuz",
  require  => [Mount["/mnt/iso"], File[$centosDir]],
}

file { "/var/lib/tftpboot/centos/initrd.img":
  ensure  => present,
  source  => "/mnt/iso/isolinux/initrd.img",
  require  => [Mount["/mnt/iso"], File[$centosDir]],
}

file { "/var/lib/tftpboot/centos/ks.cfg":
  ensure  => present,
  source  => "/root/hil/examples/puppet_headnode/manifests/static/ks.cfg",
  require => File[$centosDir],
}

file { "/usr/local/bin/make-links":
  ensure  => present,
  source  => "/root/hil/examples/puppet_headnode/manifests/static/make-links",
  mode => 755
}

file { "/usr/local/bin/boot_notify.py":
  ensure  => present,
  source  => "/root/hil/examples/puppet_headnode/manifests/static/boot_notify.py",
  mode  => 755,
}

file { "/etc/rc.local":
  ensure  => present,
  source  => "/root/hil/examples/puppet_headnode/manifests/static/rc.local",
  mode  => 755,
}

## put the bootloader in the tftp dir.
define pxecopy() {
  file { "/var/lib/tftpboot/${title}":
    # Really, this doesn't depend on the pxelinux.cfg dir, but it's parent dir.
    # This is a bit nicer than having to specify another resource, however,
    # since the directory will be created anyway.
    require => [Package['syslinux-common'], File['/var/lib/tftpboot/pxelinux.cfg']],
    source => "/usr/lib/syslinux/${title}",
    mode => 644,
  }
}

pxecopy {[
  "pxelinux.0",
  "menu.c32",
  "memdisk",
  "mboot.c32",
  "chain.c32",
]:}

## Services to restart ##
service { 'isc-dhcp-server':
  ensure => running,
  enable => true,
}
