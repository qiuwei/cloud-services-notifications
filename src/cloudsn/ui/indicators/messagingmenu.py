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
		logger.debug("add indicator to account "+acc.get_name())
		acc.is_error_icon = False
		logger.debug("Indicator created")


	def update_account(self, acc):
		#We had a previous error but now the update works.
		if acc.is_error_icon:
			#acc.indicator.set_property_icon("icon", acc.get_icon())
			acc.is_error_icon = False
		else:
			if len(acc.get_new_unread_notifications()) > 0:
				self.mmapp.draw_attention(acc.indicator)

		if acc.get_total_unread() < 1:
			self.mmapp.remove_attention(acc.indicator)

		if self.mmapp.has_source(acc.indicator):
			self.mmapp.set_source_count(acc.indicator, acc.get_total_unread())

	def update_error(self, acc):
		if not acc.is_error_icon:
			#TODO acc.indicator.set_property_icon("icon", acc.get_icon())
			acc.is_error_icon = True
		self.mmapp.set_source_count(acc.indicator, 0)

	def remove_indicator(self, acc):
		self.mmapp.remove_source(acc.indicator)
		acc.indicator = None

	def on_indicator_display_cb(self, mmapp, source_id):
		"""
		call back when user clicked on sources
		"""
		for acc in self.am.get_accounts():
			if acc.get_active() and acc.indicator == source_id:
				acc.activate()