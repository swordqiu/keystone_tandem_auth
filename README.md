keystone_tandem_auth
====================


An Openstack keystone identity plugin that authenticates against two backends in tandem.

List of files:

  keystone/config.py
  keystone/identity/backends/tandem/__init__.py
  keystone/identity/backends/tandem/core.py

The source code was tested on Folsom stable.


How to use it:

1. Merge the codes with keystone folsom stable, make sure the files are placed in the correct directory hierarchy.

   Please notes that config.py adds the following two lines at the end of the file to add two options for tandem identity backend. You may modify your own config.py to add these two lines.

   register_str('primary', group='tandem', default=None)
   register_str('secondary', group='tandem', default=None)


2. Config /etc/keystone/keystone.conf and add the following lines.


  [identity]
  driver = keystone.identity.backends.tandem.Identity

  [tandem]
  primary = keystone.identity.backends.sql.Identity
  secondary = keystone.identity.backends.ldap.Identity

  [sql]
  ... SQL backend options ...

  [ldap]
  ... LDAP backend options ...


The above configuration will authenticate users against sql backend as primary and ldap backend as secondary. Please first make sure the two backends are configured and work properly.
