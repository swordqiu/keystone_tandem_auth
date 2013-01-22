# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack LLC
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from keystone import config

from keystone import exception
from keystone import identity

from keystone.common import logging

from keystone.openstack.common import importutils

CONF = config.CONF

LOG = logging.getLogger(__name__)

class Identity(identity.Driver):

    def __init__(self):
        assert(CONF.tandem.primary is not None)
        self.primary   = importutils.import_object(CONF.tandem.primary)
        self.secondary = None
        if CONF.tandem.secondary is not None and \
                len(CONF.tandem.secondary) > 0:
            self.secondary = importutils.import_object(CONF.tandem.secondary)

    def is_primary_user(self, user_id):
        try:
            u = self.primary.get_user(user_id)
            return True
        except exception.UserNotFound:
            return False

    def is_primary_tenant(self, tenant_id):
        try:
            t = self.primary.get_tenant(tenant_id)
            return True
        except exception.TenantNotFound:
            return False

    def is_primary_role(self, role_id):
        try:
            t = self.primary.get_role(role_id)
            return True
        except exception.RoleNotFound:
            return False

    def authenticate(self, user_id=None, tenant_id=None, password=None):
        """Authenticate a given user, tenant and password.

        :returns: (user_ref, tenant_ref, metadata_ref)
        :raises: AssertionError

        """
        is_pr = self.is_primary_user(user_id)
        if tenant_id is not None:
            is_pt = self.is_primary_tenant(tenant_id)
        else:
            is_pt = None
        if is_pr and (is_pt is None or is_pt):
            return self.primary.authenticate(user_id=user_id,
                                        tenant_id=tenant_id,
                                        password=password)
        elif self.secondary and not is_pr and (is_pt is None or not is_pt):
            return self.secondary.authenticate(user_id=user_id,
                                        tenant_id=tenant_id,
                                        password=password)
        else:
            raise AssertionError('Invalid user / tenant')

    def get_tenant(self, tenant_id):
        try:
            return self.primary.get_tenant(tenant_id)
        except exception.TenantNotFound:
            try:
                if self.secondary:
                    return self.secondary.get_tenant(tenant_id)
            except exception.TenantNotFound:
                pass
            return self.get_tenant_by_name(tenant_id)

    def get_tenant_by_name(self, tenant_name):
        try:
            return self.primary.get_tenant_by_name(tenant_name)
        except exception.TenantNotFound as e:
            if self.secondary:
                return self.secondary.get_tenant_by_name(tenant_name)
            else:
                raise e

    def get_user(self, user_id):
        try:
            return self.primary.get_user(user_id)
        except exception.UserNotFound:
            try:
                if self.secondary:
                    return self.secondary.get_user(user_id)
            except exception.UserNotFound:
                pass
            return self.get_user_by_name(user_id)

    def get_user_by_name(self, user_name):
        try:
            return self.primary.get_user_by_name(user_name)
        except exception.UserNotFound as e:
            if self.secondary:
                return self.secondary.get_user_by_name(user_name)
            else:
                raise e

    def get_role(self, role_id):
        try:
            return self.primary.get_role(role_id)
        except exception.RoleNotFound:
            try:
                if self.secondary:
                    return self.secondary.get_role(role_id)
            except exception.RoleNotFound:
                pass
            return self.get_role_by_name(role_id)

    def get_role_by_name(self, name):
        roles = self.list_roles()
        for r in roles:
            if r['name'] == name:
                return r
        raise exception.RoleNotFound(role_id=name)

    def list_users(self):
        users = self.primary.list_users()
        #users.extend(self.secondary.list_users())
        return users

    def list_roles(self):
        roles = self.primary.list_roles()
        #roles.extend(self.secondary.list_roles())
        return [r if isinstance(r, dict) else r.to_dict() for r in roles]

    def get_tenants(self):
        tenants = self.primary.get_tenants()
        #tenants.extend(self.secondary.get_tenants())
        return tenants

    def add_user_to_tenant(self, tenant_id, user_id):
        is_pu = self.is_primary_user(user_id)
        is_pt = self.is_primary_tenant(tenant_id)
        if is_pu and is_pt:
            self.primary.add_user_to_tenant(tenant_id, user_id)
        elif self.secondary and not is_pu and not is_pt:
            self.secondary.add_user_to_tenant(tenant_id, user_id)
        else:
            raise exception.Forbidden()

    def remove_user_from_tenant(self, tenant_id, user_id):
        is_pu = self.is_primary_user(user_id)
        is_pt = self.is_primary_tenant(tenant_id)
        if is_pu and is_pt:
            self.primary.remove_user_from_tenant(tenant_id, user_id)
        elif self.secondary and not is_pu and not is_pt:
            self.secondary.remove_user_from_tenant(tenant_id, user_id)
        else:
            raise exception.Forbidden()

    def get_tenant_users(self, tenant_id):
        if self.is_primary_tenant(tenant_id):
            return self.primary.get_tenant_users(tenant_id)
        elif self.secondary:
            return self.secondary.get_tenant_users(tenant_id)
        else:
            raise exception.TenantNotFound(tenant_id=tenant_id)

    def get_tenants_for_user(self, user_id):
        if self.is_primary_user(user_id):
            return self.primary.get_tenants_for_user(user_id)
        elif self.secondary:
            return self.secondary.get_tenants_for_user(user_id)
        else:
            raise exception.UserNotFound(user_id=user_id)

    def get_roles_for_user_and_tenant(self, user_id, tenant_id):
        is_pu = self.is_primary_user(user_id)
        is_pt = self.is_primary_tenant(tenant_id)
        if is_pu and is_pt:
            return self.primary.get_roles_for_user_and_tenant(user_id, tenant_id)
        elif self.secondary and not is_pu and not is_pt:
            return self.secondary.get_roles_for_user_and_tenant(user_id,
                                                                    tenant_id)
        else:
            return []

    def add_role_to_user_and_tenant(self, user_id, tenant_id, role_id):
        is_pu = self.is_primary_user(user_id)
        is_pt = self.is_primary_tenant(tenant_id)
        is_pr = self.is_primary_role(role_id)
        if is_pu and is_pt and is_pr:
            self.primary.add_role_to_user_and_tenant(user_id, tenant_id,
                                                        role_id)
        elif self.secondary and not is_put and not is_pt and not is_pr:
            self.secondary.add_role_to_user_and_tenant(user_id, tenant_id,
                                                        role_id)
        else:
            raise exception.Forbidden()

    def remove_role_from_user_and_tenant(self, user_id, tenant_id, role_id):
        is_pu = self.is_primary_user(user_id)
        is_pt = self.is_primary_tenant(tenant_id)
        is_pr = self.is_primary_role(role_id)
        if is_pu and is_pt and is_pr:
            self.primary.remove_role_from_user_and_tenant(user_id, tenant_id,
                                                                    role_id)
        elif self.secondary and not is_pu and not is_pt and not is_pr:
            self.secondary.remove_role_from_user_and_tenant(user_id, tenant_id,                                                                    role_id)
        else:
            raise exception.Forbidden()

    def create_user(self, user_id, user):
        try:
            self.get_user_by_name(user['name'])
            raise exception.Conflict('User name %s exists' % user['name'])
        except exception.UserNotFound:
            nu = self.primary.create_user(user_id, user)
            nu.pop('password', None)
            return nu

    def update_user(self, user_id, user):
        if 'name' in user:
            try:
                nu = self.get_user_by_name(user['name'])
                if nu['id'] != user_id:
                    raise exception.Conflict('Name %s has been used' %
                                                    user['name'])
            except exception.UserNotFound:
                pass
        is_pu = self.is_primary_user(user_id)
        if is_pu:
            self.primary.update_user(user_id, user)
        elif self.secondary:
            self.secondary.update_user(user_id, user)
        else:
            raise exception.UserNotFound(user_id=user_id)

    def delete_user(self, user_id):
        is_pu = self.is_primary_user(user_id)
        if is_pu:
            self.primary.delete_user(user_id)
        elif self.secondary:
            self.secondary.delete_user(user_id)
        else:
            raise exception.UserNotFound(user_id=user_id)

    def create_tenant(self, tenant_id, tenant):
        try:
            self.get_tenant_by_name(tenant['name'])
            raise exception.Conflict('Tenant name %s exists' % tenant['name'])
        except exception.TenantNotFound:
            return self.primary.create_tenant(tenant_id, tenant)

    def update_tenant(self, tenant_id, tenant):
        if 'name' in tenant:
            try:
                nt = self.get_tenant_by_name(tenant['name'])
                if nt['id'] != tenant_id:
                    raise exception.Conflict('Name %s has been used' %
                                                            tenant['name'])
            except exception.TenantNotFound:
                pass
        is_pt = self.is_primary_tenant(tenant_id)
        if is_pt:
            self.primary.update_tenant(tenant_id, tenant)
        elif self.secondary:
            self.secondary.update_tenant(tenant_id, tenant)
        else:
            raise exception.TenantNotFound(tenant_id=tenant_id)

    def delete_tenant(self, tenant_id):
        is_pt = self.is_primary_tenant(tenant_id)
        if self.is_primary_tenant(tenant_id):
            self.primary.delete_tenant(tenant_id)
        elif self.secondary:
            self.secondary.delete_tenant(tenant_id)
        else:
            raise exception.TenantNotFound(tenant_id=tenant_id)

    def get_metadata(self, user_id, tenant_id):
        is_pu = self.is_primary_user(user_id)
        is_pt = self.is_primary_tenant(tenant_id)
        if is_pu and is_pt:
            return self.primary.get_metadata(user_id, tenant_id)
        elif self.secondary:
            return self.secondary.get_metadata(user_id, tenant_id)
        else:
            return exception.Forbidden()

    def create_metadata(self, user_id, tenant_id, metadata):
        is_pu = self.is_primary_user(user_id)
        is_pt = self.is_primary_tenant(tenant_id)
        if is_pu and is_pt:
            self.primary.create_metadata(user_id, tenant_id, metadata)
        elif self.secondary and not is_pu and not is_pt:
            self.secondary.create_metadata(user_id, tenant_id, metadata)
        else:
            raise exception.Forbidden()

    def update_metadata(self, user_id, tenant_id, metadata):
        is_pu = self.is_primary_user(user_id)
        is_pt = self.is_primary_tenant(tenant_id)
        if is_pu and is_pt:
            self.primary.update_metadata(user_id, tenant_id, metadata)
        elif self.secondary and not is_pu and not is_pt:
            self.secondary.update_metadata(user_id, tenant_id, metadata)
        else:
            raise exception.Forbidden()

    def delete_metadata(self, user_id, tenant_id):
        is_pu = self.is_primary_user(user_id)
        is_pt = self.is_primary_tenant(tenant_id)
        if is_pu and is_pt:
            self.primary.delete_metadata(user_id, tenant_id)
        elif self.secondary and not is_pt and not is_pt:
            self.secondary.delete_metadata(user_id, tenant_id)
        else:
            raise exception.Forbidden()

    def create_role(self, role_id, role):
        try:
            self.get_role_by_name(role['name'])
            raise exception.Conflict('Role name %s exists' % role['name'])
        except exception.RoleNotFound:
            return self.primary.create_role(role_id, role)

    def update_role(self, role_id, role):
        if 'name' in role:
            try:
                nr = self.get_role_by_name(role['name'])
                if nr['id'] != role_id:
                    raise exception.Conflict('Name %s has been used' %
                                                            role['name'])
            except exception.RoleNotFound:
                pass
        is_pr = self.is_primary_role(role_id)
        if is_pr:
            self.primary.update_role(role_id, role)
        elif self.secondary:
            self.secondary.update_role(role_id, role)
        else:
            raise exception.RoleNotFound(role_id=role_id)

    def delete_role(self, role_id):
        is_pr = self.is_primary_role(role_id)
        if is_pr:
            self.primary.delete_role(role_id)
        elif self.secondary:
            self.secondary.delete_role(role_id)
        else:
            exception.RoleNotFound(role_id=role_id)
