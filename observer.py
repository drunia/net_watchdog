#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class Observer:

    def changed(self, observable):
        pass


class Observable:

    def attach(self, observer):
        pass

    def detach(self, observable):
        pass

    def notify_observers(self):
        pass

