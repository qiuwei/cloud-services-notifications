# -*- mode: python; tab-width: 4; indent-tabs-mode: nil -*-
from cloudsn.core.account import Account

class Provider:

    def __init__ (self, name):
        self.name = name
        self.icon = None
        self.gicon = None

    def load_account(self, props):
        return Account(props, self)

    def update_account (self, account_data):
        pass
    def has_indicator(self):
        return True
    def has_notifications (self):
        return True
    def get_import_error(self):
        return None
    def get_name (self):
        return self.name
    def get_icon (self):
        return self.icon
    def get_gicon(self):
        return self.gicon
    def get_account_data_widget (self, account=None):
        """
            If account == None is a new account if not then editing
            Returns a widget and it will be inserted into the new account dialog
        """
        return None
    def set_account_data_from_widget(self, account_name, widget, account=None):
        """
            Must return the modified accont or a new one if account==None
            raise an exception if there is an error validating the data
        """
        raise NotImplementedError("The provider must implement this method!!")

class ProviderManager:

    __default = None

    providers = []

    def __init__(self):
        if ProviderManager.__default:
            raise ProviderManager.__default

    @staticmethod
    def get_instance():
        if not ProviderManager.__default:
            ProviderManager.__default = ProviderManager()
            #Default providers
            from cloudsn.providers.gmailprovider import GMailProvider
            from cloudsn.providers.greaderprovider import GReaderProvider
            from cloudsn.providers.pop3provider import Pop3Provider
            from cloudsn.providers.imapprovider import ImapProvider
            from cloudsn.providers.twitterprovider import TwitterProvider
            from cloudsn.providers.identicaprovider import IdenticaProvider
            from cloudsn.providers.feedsprovider import FeedsProvider
            ProviderManager.__default.add_provider (GMailProvider.get_instance())
            ProviderManager.__default.add_provider (GReaderProvider.get_instance())
            ProviderManager.__default.add_provider (Pop3Provider.get_instance())
            ProviderManager.__default.add_provider (ImapProvider.get_instance())
            ProviderManager.__default.add_provider (TwitterProvider.get_instance())
            ProviderManager.__default.add_provider (IdenticaProvider.get_instance())
            ProviderManager.__default.add_provider (FeedsProvider.get_instance())
        return ProviderManager.__default

    def add_provider (self, provider):
        self.providers.append (provider)
    def get_providers (self):
        return self.providers
    def get_provider(self, name):
        for prov in self.providers:
            if prov.get_name() == name:
                return prov
        return None
