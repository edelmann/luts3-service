#
# Database unit tests
#
# Author: Henrik Thostrup Jensen <htj@ndgf.org>
# Copyright: Nordic Data Grid Facility (2009)

import os
import json
import urllib

from twisted.trial import unittest
from twisted.internet import defer, reactor
from twisted.web import error as weberror

from sgas.server import setup, hostcheck

from . import rclient, ursampledata


SGAS_TEST_FILE = os.path.join(os.path.expanduser('~'), '.sgas-test')



class FakeAuthorizer:

    def isAllowed(self, subject, action, context=None):
        return True



class ResourceTest:

    port = 6180

    @defer.inlineCallbacks
    def setUp(self):
        # self.db should be created by subclass
        site = setup.createSite(self.db, FakeAuthorizer(), [])
        self.iport = reactor.listenTCP(self.port, site)
        self.service_url = 'http://localhost:%i/sgas' % self.port
        yield defer.succeed(None)


    @defer.inlineCallbacks
    def tearDown(self):
        yield self.iport.stopListening()


    @defer.inlineCallbacks
    def testInsert(self):
        insert_url = self.service_url + '/ur'

        d, f = rclient.httpRequest(insert_url, method='POST', payload=ursampledata.UR1)
        r = yield d
        self.failUnlessEqual(f.status, '200')

        # check that we got proper result with internal db representation
        ids = json.loads(r)
        self.failUnlessEqual(len(ids), 1)
        self.failUnlessIn(ursampledata.UR1_ID, ids)


    @defer.inlineCallbacks
    def testQuery(self):

        # insert some data, so there is something to query
        insert_url = self.service_url + '/ur'
        d, f = rclient.httpRequest(insert_url, method='POST', payload=ursampledata.UR1)
        yield d
        d, f = rclient.httpRequest(insert_url, method='POST', payload=ursampledata.UR2)
        yield d
        d, f = rclient.httpRequest(insert_url, method='POST', payload=ursampledata.CUR)
        yield d

        yield self.triggerAggregateUpdate()

        # query string
        query_url = self.service_url + '/query'

        userdn = '/O=Grid/O=NorduGrid/OU=ndgf.org/CN=Test User'
        encoded_userdn = urllib.quote(userdn)

        query_params = '?user_identity=%s&user_identityfirst%%20last&machine_name=benedict.grid.aau.dk&start_date=2009-01-01' % encoded_userdn
        tr_collapse  = '&time_resolution=collapse'
        tr_month     = '&time_resolution=month'
        tr_day       = '&time_resolution=day'

        # query
        # the structural testing of the records could be (a lot) better
        d, f = rclient.httpRequest(query_url + query_params + tr_collapse, method='GET')
        r = yield d
        self.failUnlessEqual(f.status, '200')

        records = json.loads(r)
        self.failUnlessEqual(len(records), 1)

        d, f = rclient.httpRequest(query_url + query_params + tr_month, method='GET')
        r = yield d
        self.failUnlessEqual(f.status, '200')
        records = json.loads(r)
        self.failUnlessEqual(len(records), 3)

        d, f = rclient.httpRequest(query_url + query_params + tr_day, method='GET')
        r = yield d
        self.failUnlessEqual(f.status, '200')
        records = json.loads(r)
        self.failUnlessEqual(len(records), 3)


    @defer.inlineCallbacks
    def testUnavailableDatabase(self):

        # first stop the "real" service
        yield self.iport.stopListening()

        # setup a new service with the "bad" database
        site = setup.createSite(self.bad_db, FakeAuthorizer(), [])
        self.iport = reactor.listenTCP(self.port, site)

        # the actual test

        insert_url = self.service_url + '/ur'
        d, f = rclient.httpRequest(insert_url, method='POST', payload=ursampledata.UR1)
        try:
            r = yield d
            self.fail('Request should have failed with 503')
        except weberror.Error, e:
            self.failUnlessEqual(e.status, '503')

        # fetching individual usage records is currently not supported
        #ur_url = self.service_url + '/ur/recordid/abcdef123456'
        #d, f = rclient.httpRequest(ur_url, method='GET')
        #try:
        #    r = yield d
        #    self.fail('Request should have failed with 503')
        #except weberror.Error, e:
        #    self.failUnlessEqual(e.status, '503')

        ## need to setup a view first
        #view_url = self.service_url + '/view/testview'
        #d, f = rclient.httpRequest(view_url, method='GET')
        #try:
        #    r = yield d
        #    self.fail('Request should have failed with 503')
        #except weberror.Error, e:
        #    self.failUnlessEqual(e.status, '503')



class CouchDBResourceTest(ResourceTest, unittest.TestCase):


    @defer.inlineCallbacks
    def setUp(self):
        from sgas.database.couchdb import database, couchdbclient

        config = json.load(file(SGAS_TEST_FILE))
        url = str(config['couchdb.url'])

        base_url, self.couch_database_name = url.rsplit('/', 1)

        self.couchdb = couchdbclient.CouchDB(base_url)
        _ = yield self.couchdb.createDatabase(self.couch_database_name)

        self.db = database.CouchDBDatabase(url, hostcheck.InsertionChecker(0))
        # for unavailable test
        self.bad_db = database.CouchDBDatabase('http://localhost:9999/nosuchdb', hostcheck.InsertionChecker(0))

        yield ResourceTest.setUp(self)


    @defer.inlineCallbacks
    def triggerAggregateUpdate(self):
        yield defer.succeed(None)
        defer.returnValue(None)


    @defer.inlineCallbacks
    def tearDown(self):
        yield ResourceTest.tearDown(self)
        yield self.couchdb.deleteDatabase(self.couch_database_name)

    def testQuery(self):
        pass
    testQuery.skip = 'Query functionality not supported in CouchDB backend.'



class PostgreSQLResourceTest(ResourceTest, unittest.TestCase):


    @defer.inlineCallbacks
    def setUp(self):
        from twisted.enterprise import adbapi
        from sgas.database.postgresql import database

        config = json.load(file(SGAS_TEST_FILE))
        db_url = config['postgresql.url']

        args = [ e or None for e in db_url.split(':') ]
        host, port, db, user, password, _ = args
        if port is None: port = 5432

        self.postgres_dbpool = adbapi.ConnectionPool('psycopg2', host=host, port=port, database=db, user=user, password=password)

        self.db = database.PostgreSQLDatabase(db_url, hostcheck.InsertionChecker(0))
        yield self.db.startService()
        # for unavalable test
        self.bad_db = database.PostgreSQLDatabase("localhost:9999:nosuchdb:BADUSER:BADPWD:", hostcheck.InsertionChecker(0))

        yield ResourceTest.setUp(self)



    @defer.inlineCallbacks
    def tearDown(self):
        yield ResourceTest.tearDown(self)
        yield self.db.stopService()
        # delete all ur rows in the database
        delete_stms = \
        "TRUNCATE usagedata;"               + \
        "TRUNCATE globalusername CASCADE;"  + \
        "TRUNCATE insertidentity CASCADE;"  + \
        "TRUNCATE machinename    CASCADE;"  + \
        "TRUNCATE voinformation  CASCADE;"
        yield self.postgres_dbpool.runOperation(delete_stms)
        yield self.postgres_dbpool.close()


    @defer.inlineCallbacks
    def triggerAggregateUpdate(self):
        yield self.db.updater.performUpdate()

