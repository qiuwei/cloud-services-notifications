# -*- mode: python; tab-width: 4; indent-tabs-mode: nil -*-
from cloudsn.core.keyring import Keyring, KeyringException, Credentials
from cloudsn import logger
import gettext

class PlainKeyring(Keyring):

    def get_id(self):
        return "plain"

    def get_name(self):
        return _("Plain text")

    def remove_credentials(self, acc):
        del(acc["username"])
        del(acc["password"])

    def store_credentials(self, acc, credentials):
        logger.debug("Storing plain credentials for account: %s" % (acc.get_name()))
        acc["username"] = credentials.username
        acc["password"] = credentials.password

    def get_credentials(self, acc):
        self.__check_valid(acc)
        return Credentials(acc["username"], acc["password"])

    def __check_valid(self, acc):
        if "username" not in acc.get_properties() or \
            "password" not in acc.get_properties():
            raise KeyringException(_("The username or password are not configured for the account: %s") % (acc.get_name()))
