# -*- mode: python; tab-width: 4; indent-tabs-mode: nil -*-
#!/usr/bin/python
from gi.repository import Gtk, MessagingMenu
from cloudsn.core import config, utils, account
from cloudsn.ui import window
from cloudsn.core.indicator import Indicator
from cloudsn.const import *
from cloudsn import logger

class IndicatorApplet (Indicator):

    def __init__(self):
        self.am = account.AccountManager.get_instance()

    def get_name(self):
        return _("Indicator Applet")

    def set_active(self, active):
        logger.debug("set_active called")
        if active:
            self.mmapp = MessagingMenu.App(desktop_id="cloudsn.desktop")
            self.mmapp.register()
            logger.debug("MessagingMenuAPP created")
        else:
            #TODO Disable the indicators
            logger.debug("deactivate Not implemented")


    def create_indicator(self, acc):
        """
        create a source and add binds it to the account.
        There is one source section for each account.
        and each account also holds a reference to the source.
        """
        source_name = acc.get_name()
        count = acc.get_total_unread()
        source_id = acc.get_name()
        self.mmapp.append_source_with_count(source_id, None, source_name, count)
        self.mmapp.connect("activate-source", self.on_indicator_display_cb)
        #now indicator is not an object as in indicatorapplet, we can keep
        #the id of it instead
        acc.indicator = source_id
        logger.debug("add new source to account "+acc.get_name())
        acc.is_error_icon = False
        logger.debug("new source created")

    def _has_source(self, acc):
        #as sources can also manually cleared by user
        if acc.indicator is None:
            return False
        else:
            if self.mmapp.has_source(acc.indicator):
                return True
            else:
                acc.indicator = None
                return False


    def update_account(self, acc):
        logger.debug("update_account called")
        logger.debug("get_total_unread " + str(acc.get_total_unread()))
        logger.debug("get_new_unread_notifications " + str(acc.get_new_unread_notifications()))
        if acc.is_error_icon:
            acc.is_error_icon = False
        else:
            if self._has_source(acc):
                logger.debug("acc.indicator is not None")
                #user didn't click on the source
                if acc.get_total_unread() < 1:
                    logger.debug("acc get_total_unread is 0")
                    #but user has checked the email
                    self.mmapp.remove_attention(acc.indicator)
                    self.mmapp.remove_source(acc.indicator)
                    acc.indicator = None
                else:
                    if len(acc.get_new_unread_notifications()) > 0:
                        #whether user checks or not, the number changed
                        self.mmapp.draw_attention(acc.indicator)
                        self.mmapp.set_source_count(acc.indicator, acc.get_total_unread())
            else:
                logger.debug("acc.indicator is None")
                #user clicked on the source, which causes that the source is removed
                #recreate the indicator/source
                if len(acc.get_new_unread_notifications()) > 0:
                    self.create_indicator(acc)
                    self.mmapp.draw_attention(acc.indicator)
                    self.mmapp.set_source_count(acc.indicator, acc.get_total_unread())




    def update_error(self, acc):
        if not acc.is_error_icon:
            #TODO acc.indicator.set_property_icon("icon", acc.get_icon())
            acc.is_error_icon = True
        if self._has_source(acc):
            # if there is already a source, we update the count
            #Otherwise we do nothing
            self.mmapp.set_source_count(acc.indicator, 0)

    def remove_indicator(self, acc):
        logger.debug("remove_indicator called")
        if self._has_source(acc):
            self.mmapp.remove_source(acc.indicator)
            acc.indicator = None

    def on_indicator_display_cb(self, mmapp, source_id):
        """
        call back when user clicked on sources
        """
        logger.debug("on_indicator_display_cb called")
        for acc in self.am.get_accounts():
            if acc.get_active() and acc.indicator == source_id:
                acc.activate()
                #we also clear the source in account
                acc.indicator = None
