# -*- mode: python; tab-width: 4; indent-tabs-mode: nil -*-
from cloudsn.core import config, utils, keyring
from cloudsn import logger
from cloudsn.core.keyring import Credentials
from gi.repository import GObject
from datetime import datetime
import gettext

class Notification:
    def __init__(self, id = None, message = None, sender = None, icon = None):
        self.id = id
        self.sender = sender
        self.message = message
        self.icon = icon

class Account:
    def __init__ (self, properties, provider):
        if 'name' not in properties:
            raise Exception(_("Error loading account configuration: The name property is mandatory, check your configuration"))
        self.properties = properties
        self.properties["provider_name"] = provider.get_name()
        self.provider = provider
        self.total_unread = 0
        self.last_update = None
        self.error_notified = False
        self.credentials = None
        if 'active' not in self.properties:
            self.properties["active"] = True
        if 'show_notifications' not in self.properties:
            self.properties["show_notifications"] = True

    def __getitem__(self, key):
        return self.properties[key]

    def __setitem__(self, key, value):
        self.properties[key] = value

    def __contains__(self, key):
        return key in self.properties

    def __delitem__(self, key):
        del(self.properties[key])

    def get_properties(self):
        return self.properties

    def get_name (self):
        return self.properties["name"]

    def get_provider (self):
        return self.provider

    def can_mark_read(self):
        return False

    def mark_read(self):
        raise Exception("The mark_read method has not been implemented")

    def has_credentials(self):
        """False if the account doesn't need credentials"""
        return True

    def get_credentials(self):
        if not self.credentials:
            raise Exception (_("The credentials have not been loaded for the account %s") % (self.get_name()))

        return self.credentials

    #TODO change to get_credentials_safe
    def get_credentials_save(self):
        if not self.credentials:
            return keyring.Credentials("","")

        return self.credentials

    def set_credentials(self, credentials):
        self.credentials = credentials

    def get_show_notifications(self):
        return utils.get_boolean(self.properties["show_notifications"])

    def set_show_notifications(self, show_notifications):
        self.properties["show_notifications"] = utils.get_boolean(show_notifications)

    def get_active (self):
        return utils.get_boolean(self.properties["active"])

    def set_active(self, active):
        self.properties["active"] = utils.get_boolean(active)

    def get_activate_command(self):
        if "activate_command" in self.properties:
            return self.properties["activate_command"]
        return ""

    def set_activate_command(self, command):
        self.properties["activate_command"] = command

    def get_last_update (self):
        return self.last_update

    def get_total_unread (self):
        return self.total_unread

    def get_new_unread_notifications(self):
        return []

    def activate (self):
        if "activate_command" in self.properties and self.properties["activate_command"] != "":
            logger.debug ("Executing the activate command")
            utils.execute_command (self, self.properties["activate_command"])
        elif "activate_url" in self.properties :
            utils.show_url (self.properties["activate_url"])
        else:
            logger.warn('This account type has not an activate action')

    def get_icon (self):
        if self.error_notified:
            return utils.get_account_error_pixbuf(self)
        else:
            return self.get_provider().get_icon()

    def get_gicon (self):
        if self.error_notified:
            return utils.get_account_error_gicon(self)
        else:
            return self.get_provider().get_gicon()

class AccountCacheMails (Account):

    def __init__(self, properties, provider):
        Account.__init__(self, properties, provider)
        self.notifications = {}
        self.new_unread = []

    def get_total_unread (self):
        if self.notifications:
            return len(self.notifications)
        else:
            return self.total_unread

    def get_new_unread_notifications(self):
        return self.new_unread

class AccountManager (GObject.Object):

    __default = None

    __gtype_name__ = "AccountManager"

    __gsignals__ = { "account-added" : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
                     "account-deleted" : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
                     "account-changed" : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
                     "account-active-changed" : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))}

    def __init__(self):
        if AccountManager.__default:
            raise AccountManager.__default
        GObject.Object.__init__(self)
        from cloudsn.core.provider import ProviderManager
        self.accounts = {}
        self.sc = config.SettingsController.get_instance()
        self.pm = ProviderManager.get_instance()

    @staticmethod
    def get_instance():
        if not AccountManager.__default:
            AccountManager.__default = AccountManager()
        return AccountManager.__default

    def load_accounts(self):
        accs_conf = self.sc.get_accounts_config()
        for conf in accs_conf.values():
            provider = self.pm.get_provider(conf['provider_name'])
            if provider:
                try:
                    acc = provider.load_account (conf)
                    if acc.has_credentials():
                        credentials = Credentials("","")
                        try:
                            credentials = keyring.get_keyring().get_credentials(acc)
                        except Exception, e:
                            logger.exception("Cannot load credentials for account "+conf["name"]+": %s", e)
                        acc.set_credentials (credentials)
                    self.add_account(acc)
                except Exception, e:
                    logger.exception("Cannot load the account "+conf["name"]+": %s", e)

            else:
                logger.error("Error in account %s: The provider %s doesn't exists" % (conf['name'], conf['provider_name']))

    def validate_account(self, account_name):
        if account_name in self.accounts:
            error = _('The account %s already exists' % (account_name))
            raise Exception(error)

    def add_account(self, acc):
        self.validate_account(acc.get_name())
        self.accounts[acc.get_name()] = acc

        self.emit("account-added", acc)

    def set_account_active (self, acc, active):
        if acc.get_active() != active:
            acc.error_notified = False
            acc.set_active(active)
            self.emit("account-active-changed", acc)
            self.save_account(acc)

    def get_account(self, account_name):
        return self.accounts[account_name]

    def get_accounts(self):
        return self.accounts.values()

    def del_account(self, account, complete=True):
        del self.accounts[account.get_name()]
        if complete:
            self.sc.del_account_config(account.get_name())
            if account.has_credentials():
                keyring.get_keyring().remove_credentials(account)
            self.sc.save_accounts()

        self.emit("account-deleted", account)

    def update_account (self, acc):
        if acc.get_active():
            acc.provider.update_account (acc)
            acc.last_update = datetime.now()

    def save_account(self, acc):
        acc.error_notified = False
        self.sc.set_account_config (acc)
        if acc.has_credentials():
            keyring.get_keyring().store_credentials(acc, acc.get_credentials())
        self.sc.save_accounts()
        self.emit("account-changed", acc)

    def save_accounts(self, store_credentials = True):
        if store_credentials and acc.has_credentials():
            keyring.get_keyring().store_credentials(acc, acc.get_credentials())
        self.sc.save_accounts()

def get_account_manager():
    return AccountManager.get_instance()
