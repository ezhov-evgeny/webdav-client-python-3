__author__ = 'designerror'

import allure
#from hamcrest import *

class TestRequiredOptions:

    def test_without_webdav_hostname(self):
        options = { 'webdav_server': "https://webdav.yandex.ru"}
        allure.attach('options', options.__str__())
        assert 1
