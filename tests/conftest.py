__author__ = 'designerror'

from hamcrest.core.base_matcher import BaseMatcher
from hamcrest.core.helpers.hasmethod import hasmethod

class Valid(BaseMatcher):
    def _matches(self, item):
        return False if not hasmethod(item, 'valid') else item.valid()

class NotValid(BaseMatcher):
    def _matches(self, item):
        return False if not hasmethod(item, 'valid') else not item.valid()

class Success(BaseMatcher):
    def _matches(self, item):
        return item

class NotSuccess(BaseMatcher):
    def _matches(self, item):
        return not item

def valid():
    return Valid()

def not_valid():
    return NotValid()

def success():
    return Success()

def not_success():
    return NotSuccess()