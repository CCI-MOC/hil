
**puppet SSL described:**
http://www.masterzen.fr/2010/11/14/puppet-ssl-explained/



**from 10_setup_master.sh:**
sudo service puppetmaster start;\

**resulting error:**
Starting puppetmaster:                                     [FAILED]
Info: Creating a new SSL certificate request for ca
Info: Certificate Request fingerprint (SHA256): 0B:03:CB:48:55:C0:4C:F6:B0:20:65:86:31:CC:9F:97:0D:3D:E3:C0:84:FC:2A:8F:6A:63:CD:38:83:41:8C:ED
Notice: Signed certificate request for ca
Debug: Using cached certificate for ca
Info: Creating a new certificate revocation list
Info: Creating a new SSL key for puppet
Error: Could not run: Could not write puppet: undefined method `writesub' for #<Puppet::Settings:0x7fd6537ef870>
Error: Could not request certificate: Connection refused - connect(2)




**Individual nodes trying to get certificates signed by master (puppet node) / CA (certificate authority):**
Error: Could not request certificate: The certificate retrieved from the master does not match the agent's private key.
Certificate fingerprint: D0:9E:C4:D6:74:D3:86:A7:C4:43:59:AE:8C:5E:30:5F:88:F2:69:6E:96:0F:BB:E6:B0:DD:DF:25:02:23:2B:25
To fix this, remove the certificate from both the master and the agent and then start a puppet run, which will automatically regenerate a certficate.
On the master:
  puppet cert clean network
On the agent:
  rm -f /var/lib/puppet/ssl/certs/network.pem
  puppet agent -t


**Testing the above solution provides an identical error (including fingerprint)**


* Both cases give "undefined method ‘writesub’” error.
* Puppet has permissions in ssl directory ( /var/lib/puppet/ssl )
* Not all requests end up in /var/lib/puppet/ssl/ca/requests on Puppet (usually 2 node cert requests) 
