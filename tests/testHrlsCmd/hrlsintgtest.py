import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest
import ast
import json
import os
import os.path
import string
import subprocess
import requests

sys.path.append("../../cmd")

TEST_RESOURCES_PATH = '../tests/resources/'    # Trailing '/' is required
CRED_FILENAME = 'hrls_credentials'
CRED_PATH = TEST_RESOURCES_PATH+CRED_FILENAME

if 'CRED_PATH' in os.environ:
    CRED_PATH = os.environ['CRED_PATH']


@unittest.skipUnless(os.path.isfile(CRED_PATH) and os.access(CRED_PATH, os.R_OK),
                     'requires HRLS credentials file at %s' % CRED_PATH)

def execute_curl(url, username, password, search_list=None, search_verify=None ):
    '''run curl command, get output back in an list'''

    auth = (username, password)

    if search_list is not None:
        url=url+"?"+'&'.join(search_list)
        #print url

    r = requests.get(url, auth=auth, verify=search_verify)
    return r


class HrlsIntegrationTests(unittest.TestCase):

    def setUp(self):
        """Setup testB2SafeCmd environment before the tests have run"""
        jsonfilecontent = json.loads(open(CRED_PATH, 'r').read())
        self.handle_server_url = jsonfilecontent.pop('handle_server_url')
        self.prefix = jsonfilecontent.pop('prefix')
        self.username = jsonfilecontent.pop('reverselookup_username')
        self.password = jsonfilecontent.pop('reverselookup_password')
        self.https_verify = jsonfilecontent.pop('HTTPS_verify', 'True') == 'True'
        if not self.https_verify:
            requests.packages.urllib3.disable_warnings() 
 

    def tearDown(self):
        """ Cleanup testB2SafeCmd environment after the tests have run
        """
        no_op=None

    def test_ping(self):
        """Test that ping works."""
        ping_result = execute_curl(self.handle_server_url+'/hrls/ping', self.username, self.password, None, self.https_verify)
        self.assertEqual(
            ping_result.status_code, 200,
            'ping hrls returns unexpected status')
        self.assertEqual(
            ping_result.content, 'OK\n',
            'ping hrls returns unexpected response')

    def test_search_handle_by_non_existing_key_value_1(self):
        """Test that search by ['URL=my_unknown_handle_url'] returns no matching handle."""
        search_array=['URL=my_unknown_handle_url']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by non existing url key returns unexpected status')
        self.assertEqual(
            search_result.content, '[]',
            'search handle by non existing url key returns unexpected response')

    def test_search_handle_by_non_existing_key_value_2(self):
        """Test that search by ['URL=my_unknown_handle_url','HS_ADMIN=*'] returns no matching handle."""
        search_array=['URL=my_unknown_handle_url','HS_ADMIN=*']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by non existing url key returns unexpected status')
        self.assertEqual(
            search_result.content, '[]',
            'search handle by non existing url key returns unexpected response')

    def test_search_handle_by_non_existing_key_value_3(self):
        """Test that search by ['HS_ADMIN=*','URL=my_unknown_handle_url'] returns no matching handle."""
        search_array=['HS_ADMIN=*','URL=my_unknown_handle_url']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by non existing url key returns unexpected status')
        self.assertEqual(
            search_result.content, '[]',
            'search handle by non existing url key returns unexpected response')

    def test_search_handle_by_prohibited_key_value_1(self):
        """Test that search by ['HS_SECKEY=*'] returns specific message."""
        search_array=['HS_SECKEY=*']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 500,
            'search hrls by prohibited key returns unexpected status')
        self.assertEqual(
            search_result.content, 'Searching via HS_SECKEY entries is not allowed!',
            'search handle by prohibited key returns unexpected response')

    def test_search_handle_by_prohibited_key_value_2(self):
        """Test that search by ['HS_SECKEY=*','URL=*'] returns specific message."""
        search_array=['HS_SECKEY=*','URL=*']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 500,
            'search hrls by prohibited key returns unexpected status')
        self.assertEqual(
            search_result.content, 'Searching via HS_SECKEY entries is not allowed!',
            'search handle by prohibited key returns unexpected response')

    def test_search_handle_by_prohibited_key_value_3(self):
        """Test that search by ['URL=*','HS_SECKEY=*'] returns specific message."""
        search_array=['URL=*','HS_SECKEY=*']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 500,
            'search hrls by prohibited key returns unexpected status')
        self.assertEqual(
            search_result.content, 'Searching via HS_SECKEY entries is not allowed!',
            'search handle by prohibited key returns unexpected response')

    def test_search_handle_by_existing_key_value_1(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/000001'] returns specific handle."""
        search_array=['URL=http://www.test_hrls_check.com/000001']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        self.assertEqual(
            search_result.content, '["'+self.prefix+'/HRLS_CHECK_HANDLE_000001"]',
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_2(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/000001','HS_ADMIN=*'] returns specific handle."""
        search_array=['URL=http://www.test_hrls_check.com/000001','HS_ADMIN=*']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        self.assertEqual(
            search_result.content, '["'+self.prefix+'/HRLS_CHECK_HANDLE_000001"]',
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_3(self):
        """Test that search by ['HS_ADMIN=*','URL=http://www.test_hrls_check.com/000001'] returns specific handle."""
        search_array=['HS_ADMIN=*','URL=http://www.test_hrls_check.com/000001']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        self.assertEqual(
            search_result.content, '["'+self.prefix+'/HRLS_CHECK_HANDLE_000001"]',
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_limit_1(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/*'] returns 1000 handles."""
        limit = 1000
        search_array=['URL=http://www.test_hrls_check.com/*']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        json_check_list = []
        for x in xrange(1, limit+1):
            counter = "%06d" % x
            json_check_list.append(self.prefix+'/HRLS_CHECK_HANDLE_'+counter)
        set1 = set(search_result_list)
        set2 = set(json_check_list)
        self.assertEqual(
            set1, set2,
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_limit_2(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/*','limit=10000'] returns 10000 handles."""
        limit = 10000
        search_array=['URL=http://www.test_hrls_check.com/*','limit=10000']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        json_check_list = []
        for x in xrange(1, limit+1):
            counter = "%06d" % x
            json_check_list.append(self.prefix+'/HRLS_CHECK_HANDLE_'+counter)
        set1 = set(search_result_list)
        set2 = set(json_check_list)
        self.assertEqual(
            set1, set2,
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_limit_3(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/*','limit=100000'] returns 100000 handles."""
        limit = 100000
        search_array=['URL=http://www.test_hrls_check.com/*','limit=100000']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        json_check_list = []
        for x in xrange(1, limit+1):
            counter = "%06d" % x
            json_check_list.append(self.prefix+'/HRLS_CHECK_HANDLE_'+counter)
        set1 = set(search_result_list)
        set2 = set(json_check_list)
        self.assertEqual(
            set1, set2,
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_limit_4(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/*','limit=200000'] returns 100000 handles."""
        limit = 100000
        search_array=['URL=http://www.test_hrls_check.com/*','limit=200000']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        json_check_list = []
        for x in xrange(1, limit+1):
            counter = "%06d" % x
            json_check_list.append(self.prefix+'/HRLS_CHECK_HANDLE_'+counter)
        set1 = set(search_result_list)
        set2 = set(json_check_list)
        self.assertEqual(
            set1, set2,
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_page_1(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/*','page=0'] returns first 1000 handles."""
        limit = 1000
        page = 0
        search_array=['URL=http://www.test_hrls_check.com/*','page=0']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        json_check_list = []
        for x in xrange((page*limit)+1, (page*limit)+limit+1):
            counter = "%06d" % x
            json_check_list.append(self.prefix+'/HRLS_CHECK_HANDLE_'+counter)
        set1 = set(search_result_list)
        set2 = set(json_check_list)
        self.assertEqual(
            set1, set2,
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_page_2(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/*','page=1'] returns second 1000 handles."""
        limit = 1000
        page = 1
        search_array=['URL=http://www.test_hrls_check.com/*','page=1']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        json_check_list = []
        for x in xrange((page*limit)+1, (page*limit)+limit+1):
            counter = "%06d" % x
            json_check_list.append(self.prefix+'/HRLS_CHECK_HANDLE_'+counter)
        set1 = set(search_result_list)
        set2 = set(json_check_list)
        self.assertEqual(
            set1, set2,
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_page_3(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/*','page=2'] returns third 1000 handles."""
        limit = 1000
        page = 2
        search_array=['URL=http://www.test_hrls_check.com/*','page=2']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        json_check_list = []
        for x in xrange((page*limit)+1, (page*limit)+limit+1):
            counter = "%06d" % x
            json_check_list.append(self.prefix+'/HRLS_CHECK_HANDLE_'+counter)
        set1 = set(search_result_list)
        set2 = set(json_check_list)
        self.assertEqual(
            set1, set2,
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_page_and_limit_1(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/*','page=0','limit=10'] returns first 10 handles."""
        limit = 10
        page = 0
        search_array=['URL=http://www.test_hrls_check.com/*','page=0','limit=10']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        json_check_list = []
        for x in xrange((page*limit)+1, (page*limit)+limit+1):
            counter = "%06d" % x
            json_check_list.append(self.prefix+'/HRLS_CHECK_HANDLE_'+counter)
        set1 = set(search_result_list)
        set2 = set(json_check_list)
        self.assertEqual(
            set1, set2,
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_page_and_limit_2(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/*','page=1','limit=10'] returns second 10 handles."""
        limit = 10
        page = 1
        search_array=['URL=http://www.test_hrls_check.com/*','page=1','limit=10']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        json_check_list = []
        for x in xrange((page*limit)+1, (page*limit)+limit+1):
            counter = "%06d" % x
            json_check_list.append(self.prefix+'/HRLS_CHECK_HANDLE_'+counter)
        set1 = set(search_result_list)
        set2 = set(json_check_list)
        self.assertEqual(
            set1, set2,
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_page_and_limit_3(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/*','limit=10','page=0'] returns first 10 handles."""
        limit = 10
        page = 0
        search_array=['URL=http://www.test_hrls_check.com/*','limit=10','page=0']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        json_check_list = []
        for x in xrange((page*limit)+1, (page*limit)+limit+1):
            counter = "%06d" % x
            json_check_list.append(self.prefix+'/HRLS_CHECK_HANDLE_'+counter)
        set1 = set(search_result_list)
        set2 = set(json_check_list)
        self.assertEqual(
            set1, set2,
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_page_and_limit_4(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/*','limit=10','page=1'] returns second 10 handles."""
        limit = 10
        page = 1
        search_array=['URL=http://www.test_hrls_check.com/*','limit=10','page=1']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        json_check_list = []
        for x in xrange((page*limit)+1, (page*limit)+limit+1):
            counter = "%06d" % x
            json_check_list.append(self.prefix+'/HRLS_CHECK_HANDLE_'+counter)
        set1 = set(search_result_list)
        set2 = set(json_check_list)
        self.assertEqual(
            set1, set2,
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_retrieverecords_1(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/000001','retrieverecords=true'] returns all records for that handle."""
        search_array=['URL=http://www.test_hrls_check.com/000001','retrieverecords=true']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][0]['type'], 'URL',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][0]['value'], 'http://www.test_hrls_check.com/000001',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][1]['type'], 'EMAIL',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][1]['value'], 'test_hrls_000001@test_hrls_check.com',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][2]['type'], 'TEXT',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][2]['value'], 'This handle is used to check if the hrls is functioning',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][3]['type'], 'HS_ADMIN',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            len(search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001']), 4,
            'search handle by existing key value returns unexpected response')


    def test_search_handle_by_existing_key_value_retrieverecords_2(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/00000*','retrieverecords=true','limit=9'] returns all records for those handles."""
        search_array=['URL=http://www.test_hrls_check.com/00000*','retrieverecords=true','limit=9']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        for i in xrange(1, 10):
            counter = "%06d" % i
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][0]['type'], 'URL',
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][0]['value'], 'http://www.test_hrls_check.com/'+str(counter),
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][1]['type'], 'EMAIL',
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][1]['value'], 'test_hrls_'+str(counter)+'@test_hrls_check.com',
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][2]['type'], 'TEXT',
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][2]['value'], 'This handle is used to check if the hrls is functioning',
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][3]['type'], 'HS_ADMIN',
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                len(search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)]), 4,
                'search handle by existing key value returns unexpected response')
    
    def test_search_handle_by_existing_key_value_retrieverecords_3(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/*','retrieverecords=true','limit=100000'] returns all records for those handles."""
        search_array=['URL=http://www.test_hrls_check.com/*','retrieverecords=true','limit=100000']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status: %s' % search_result.status_code)
        search_result_list = json.loads(search_result.content)
        for i in xrange( 99999, 100001):
            counter = "%06d" % i
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][0]['type'], 'URL',
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][0]['value'], 'http://www.test_hrls_check.com/'+str(counter),
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][1]['type'], 'EMAIL',
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][1]['value'], 'test_hrls_'+str(counter)+'@test_hrls_check.com',
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][2]['type'], 'TEXT',
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][2]['value'], 'This handle is used to check if the hrls is functioning',
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)][3]['type'], 'HS_ADMIN',
                'search handle by existing key value returns unexpected response')
            self.assertEqual(
                len(search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_'+str(counter)]), 4,
                'search handle by existing key value returns unexpected response')

    def test_search_handle_by_existing_key_value_retrieverecords_except_hs_seckey_1(self):
        """Test that search by ['URL=http://www.test_hrls_check.com/000001','retrieverecords=true'] returns all records for that handle except HS_SECKEY."""
        search_array=['URL=http://www.test_hrls_check.com/000001','retrieverecords=true']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        self.assertNotIn(
            'HS_SECKEY', search_result.content,
            'search handle by existing key value gives back HS_SECKEY response')

    def test_search_handle_by_prefix_existing_key_value_1(self):
        """Test that search by ['prefix','URL=http://www.test_hrls_check.com/*'] returns 1000 handles."""
        limit = 1000
        search_array=['URL=http://www.test_hrls_check.com/*']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles/'+self.prefix, self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing prefix,key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        json_check_list = []
        for x in xrange(1, limit+1):
            counter = "%06d" % x
            json_check_list.append(self.prefix+'/HRLS_CHECK_HANDLE_'+counter)
        set1 = set(search_result_list)
        set2 = set(json_check_list)
        self.assertEqual(
            set1, set2,
            'search handle by prefix,existing key value returns unexpected response')

    def test_search_handle_by_prefix_existing_key_value_2(self):
        """Test that search by ['prefix;xyz','URL=http://www.test_hrls_check.com/*'] returns 1000 handles."""
        limit = 1000
        search_array=['URL=http://www.test_hrls_check.com/*']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles/'+self.prefix+';xyz', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing prefix;xyz,key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        json_check_list = []
        for x in xrange(1, limit+1):
            counter = "%06d" % x
            json_check_list.append(self.prefix+'/HRLS_CHECK_HANDLE_'+counter)
        set1 = set(search_result_list)
        set2 = set(json_check_list)
        self.assertEqual(
            set1, set2,
            'search handle by prefix;xyz,existing key value returns unexpected response')

    def test_search_handle_by_prefix_existing_key_value_3(self):
        """Test that search by ['prefixi','URL=http://www.test_hrls_check.com/*'] returns no handles."""
        limit = 1000
        search_array=['URL=http://www.test_hrls_check.com/*']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles/'+self.prefix+'i', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing prefixi,key value returns unexpected status')
        self.assertEqual(
            search_result.content, '[]',
            'search handle by prefixi,existing key value returns unexpected response')

    def test_search_handle_by_prefix_existing_key_value_4(self):
        """Test that search by ['prefix i','URL=http://www.test_hrls_check.com/*'] returns error."""
        limit = 1000
        search_array=['URL=http://www.test_hrls_check.com/*']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles/'+self.prefix+' i', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 404,
            'search hrls by existing prefix i,key value returns unexpected status')
        
    def test_search_handle_by_prefix_existing_key_value_5(self):
        """Test that search by ['prefix','URL=http://www.test_hrls_check.com/000001','retrieverecords=true'] returns all records for that handle."""
        search_array=['URL=http://www.test_hrls_check.com/000001','retrieverecords=true']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles/'+self.prefix, self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing key value returns unexpected status')
        search_result_list = json.loads(search_result.content)
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][0]['type'], 'URL',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][0]['value'], 'http://www.test_hrls_check.com/000001',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][1]['type'], 'EMAIL',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][1]['value'], 'test_hrls_000001@test_hrls_check.com',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][2]['type'], 'TEXT',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][2]['value'], 'This handle is used to check if the hrls is functioning',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001'][3]['type'], 'HS_ADMIN',
            'search handle by existing key value returns unexpected response')
        self.assertEqual(
            len(search_result_list[str(self.prefix)+'/HRLS_CHECK_HANDLE_000001']), 4,
            'search handle by existing key value returns unexpected response')

    def test_search_handle_by_prefix_existing_key_value_6(self):
        """Test that search by ['prefixi','URL=http://www.test_hrls_check.com/*','retrieverecords=true'] returns no handles."""
        limit = 1000
        search_array=['URL=http://www.test_hrls_check.com/*','retrieverecords=true']
        search_result = execute_curl(self.handle_server_url+'/hrls/handles/'+self.prefix+'i', self.username, self.password, search_array, self.https_verify)
        self.assertEqual(
            search_result.status_code, 200,
            'search hrls by existing prefixi,key value returns unexpected status')
        self.assertEqual(
            search_result.content, '{}',
            'search handle by prefixi,existing key value returns unexpected response')

if __name__ == "__main__":
    unittest.main()
