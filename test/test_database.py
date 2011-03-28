#
# Database unit tests
#
# Author: Henrik Thostrup Jensen <htj@ndgf.org>
# Copyright: Nordic Data Grid Facility (2009, 2010)

import os
import time

from twisted.trial import unittest
from twisted.internet import defer

from . import ursampledata, srsampledata, utils




SGAS_TEST_FILE = os.path.join(os.path.expanduser('~'), '.sgas-test')



class GenericDatabaseTest:

    def fetchJobUsageRecord(self, record_id):
        # fetch an individual usage record from the underlying database given a record id
        # should return none if the record does not exist
        raise NotImplementedError('fetching individual usage record is not implemented in generic test (nor should it be)')


    @defer.inlineCallbacks
    def testSingleInsert(self):

        doc_ids = yield self.db.insertJobUsageRecords(ursampledata.UR1)
        self.failUnlessEqual(len(doc_ids), 1)

        doc = yield self.fetchJobUsageRecord(ursampledata.UR1_ID)

        self.failUnlessEqual(doc.get('record_id', None), ursampledata.UR1_ID)
        self.failUnlessEqual(doc.get('job_name', None),  'test job 1')


    @defer.inlineCallbacks
    def testExistenceBeforeAndAfterInsert(self):

        doc = yield self.fetchJobUsageRecord(ursampledata.UR2_ID)
        self.failUnlessEqual(doc, None)

        doc_ids = yield self.db.insertJobUsageRecords(ursampledata.UR2)
        self.failUnlessEqual(len(doc_ids), 1)

        doc = yield self.fetchJobUsageRecord(ursampledata.UR2_ID)

        self.failUnlessEqual(doc.get('record_id', None), ursampledata.UR2_ID, doc)
        self.failUnlessEqual(doc.get('job_name', None),  'test job 2')


    @defer.inlineCallbacks
    def testCompoundInsert(self):

        doc_ids = yield self.db.insertJobUsageRecords(ursampledata.CUR)

        self.failUnlessEqual(len(doc_ids), 2)

        for ur_id in ursampledata.CUR_IDS:
            doc = yield self.fetchJobUsageRecord(ur_id)
            self.failUnlessEqual(doc.get('record_id', None), ur_id)


class QueryDatabaseTest:

    def triggerAggregateUpdate(self):
        # trigger an update of the aggregated information in the underlying database (if needed)
        raise NotImplementedError('updating aggregated information is not implemented in generic test (nor should it be)')


    @defer.inlineCallbacks
    def testBasicQuery(self):

        yield self.db.insertJobUsageRecords(ursampledata.UR1)
        yield self.db.insertJobUsageRecords(ursampledata.UR2)

        yield self.triggerAggregateUpdate()

        result = yield self.db.query('SELECT distinct(user_identity) FROM uraggregated;')
        self.failUnlessEqual(result, [['/O=Grid/O=NorduGrid/OU=ndgf.org/CN=Test User']])


    @defer.inlineCallbacks
    def testGroupQuery(self):

        yield self.db.insertJobUsageRecords(ursampledata.UR1)
        yield self.db.insertJobUsageRecords(ursampledata.UR2)
        yield self.triggerAggregateUpdate()

        result = yield self.db.query('SELECT user_identity, sum(n_jobs) FROM uraggregated GROUP BY user_identity')
        self.failUnlessEqual(result, [['/O=Grid/O=NorduGrid/OU=ndgf.org/CN=Test User', 2]])


    @defer.inlineCallbacks
    def testFilterQuery(self):

        yield self.db.insertJobUsageRecords(ursampledata.CUR)
        yield self.triggerAggregateUpdate()

        result = yield self.db.query('SELECT user_identity, sum(n_jobs) FROM uraggregated ' +
                                     'WHERE machine_name = \'%s\' GROUP BY user_identity' % ('fyrgrid.grid.aau.dk',))
        self.failUnlessEqual(result, [['/O=Grid/O=NorduGrid/OU=ndgf.org/CN=Test User', 1]])


    @defer.inlineCallbacks
    def testOrderQuery(self):

        yield self.db.insertJobUsageRecords(ursampledata.CUR)
        yield self.triggerAggregateUpdate()

        result = yield self.db.query('SELECT machine_name FROM uraggregated ORDER BY machine_name')
        self.failUnlessEqual(result, [['benedict.grid.aau.dk'], ['fyrgrid.grid.aau.dk']])



class StorageRecordTest:

    @defer.inlineCallbacks
    def testBasicStorageInsert(self):

        doc_ids = yield self.db.insertStorageUsageRecords(srsampledata.SR_0)
        self.failUnlessEqual(len(doc_ids), 1)
        self.failUnlessEqual(doc_ids.keys()[0], srsampledata.SR_0_ID)

        doc = yield self.fetchStorageUsageRecord(srsampledata.SR_0_ID)

        self.failUnlessEqual(doc.get('record_id', None), srsampledata.SR_0_ID)
        self.failUnlessEqual(doc.get('storage_media', None),  'disk')

        # one more

        doc_ids = yield self.db.insertStorageUsageRecords(srsampledata.SR_1)
        self.failUnlessEqual(len(doc_ids), 1)
        self.failUnlessEqual(doc_ids.keys()[0], srsampledata.SR_1_ID)

        doc = yield self.fetchStorageUsageRecord(srsampledata.SR_1_ID)

        self.failUnlessEqual(doc.get('record_id', None), srsampledata.SR_1_ID)
        self.failUnlessEqual(doc.get('group', None),  'Alice')


    @defer.inlineCallbacks
    def testCompoundStorageInsert(self):

        doc_ids = yield self.db.insertStorageUsageRecords(srsampledata.SRS)
        self.failUnlessEqual(len(doc_ids), 3)
        record_ids = doc_ids.keys()
        for rid in record_ids:
            self.failUnlessIn(rid, srsampledata.SRS_IDS)



class PostgreSQLTestCase(GenericDatabaseTest, QueryDatabaseTest, StorageRecordTest, unittest.TestCase):

    @defer.inlineCallbacks
    def fetchJobUsageRecord(self, record_id):

        from sgas.database.postgresql import urconverter

        stm = "SELECT * from usagerecords where record_id = %s"
        res = yield self.postgres_dbpool.runQuery(stm, (record_id,))

        if res == []:
            defer.returnValue(None)
        elif len(res) == 1:
            ur_doc = dict( zip(urconverter.ARG_LIST, res[0]) )
            defer.returnValue(ur_doc)
        else:
            self.fail('Multiple results returned for a single job usage record')


    @defer.inlineCallbacks
    def fetchStorageUsageRecord(self, record_id):

        from sgas.database.postgresql import srconverter

        stm = "SELECT * from storagerecords where record_id = %s"
        res = yield self.postgres_dbpool.runQuery(stm, (record_id,))

        if res == []:
            defer.returnValue(None)
        elif len(res) == 1:
            sr_doc = dict( zip(srconverter.ARG_LIST, res[0]) )
            defer.returnValue(sr_doc)
        else:
            self.fail('Multiple results returned for a single storage usage record')


    @defer.inlineCallbacks
    def triggerAggregateUpdate(self):
        # should update the uraggregate table here
        yield self.real_db.updater.performUpdate()


    def setUp(self):

        from twisted.enterprise import adbapi
        from sgas.ext.python import json
        from sgas.database import inserter
        from sgas.database.postgresql import database

        config = json.load(file(SGAS_TEST_FILE))
        db_url = config['postgresql.url']

        args = [ e or None for e in db_url.split(':') ]
        host, port, db, user, password, _ = args
        if port is None: port = 5432

        self.postgres_dbpool = adbapi.ConnectionPool('psycopg2', host=host, port=port, database=db, user=user, password=password)

        self.real_db = database.PostgreSQLDatabase(db_url)

        class WrapperDB:
            def __init__(self, db):
                self.db = db
                self.authorizer = utils.FakeAuthorizer()
            def insertJobUsageRecords(self, ur_data):
                return inserter.insertJobUsageRecords(ur_data, self.db, self.authorizer)
            def insertStorageUsageRecords(self, sr_data):
                return inserter.insertStorageUsageRecords(sr_data, self.db, self.authorizer)
            def query(self, *args):
                return self.db.query(*args)

        self.db = WrapperDB(self.real_db)

        return self.real_db.startService()


    @defer.inlineCallbacks
    def tearDown(self):
        yield self.real_db.stopService()
        # delete all ur rows in the database
        delete_stms = \
        "TRUNCATE uraggregated_data;"       + \
        "TRUNCATE uraggregated_update;"     + \
        "TRUNCATE usagedata      CASCADE;"  + \
        "TRUNCATE globalusername CASCADE;"  + \
        "TRUNCATE insertidentity CASCADE;"  + \
        "TRUNCATE machinename    CASCADE;"  + \
        "TRUNCATE voinformation  CASCADE;"
        yield self.postgres_dbpool.runOperation(delete_stms)
        yield self.postgres_dbpool.close()


    @defer.inlineCallbacks
    def testUpdateAfterSingleInsert(self):

        yield self.db.insertJobUsageRecords(ursampledata.UR1)

        rows = yield self.postgres_dbpool.runQuery('SELECT * from uraggregated_update')
        mid_rows = yield self.postgres_dbpool.runQuery("SELECT id from machinename WHERE machine_name = %s", (ursampledata.UR1_MACHINE_NAME,))

        self.failUnlessEqual(len(rows), 1)

        # do the date dance!
        gmt = time.gmtime()
        date = '%s-%s-%s' % (gmt.tm_mday, gmt.tm_mon, gmt.tm_year)
        mxd = rows[0][0]
        row_date = '%s-%s-%s' % (mxd.day, mxd.month, mxd.year)

        machine_name_id = mid_rows[0][0]
        self.failUnlessEqual( [ (row_date, rows[0][1]) ], [ (date, machine_name_id) ])


    @defer.inlineCallbacks
    def testUpdateAfterTrigger(self):

        yield self.db.insertJobUsageRecords(ursampledata.CUR)
        yield self.triggerAggregateUpdate()

        rows = yield self.postgres_dbpool.runQuery('SELECT * from uraggregated_update')
        self.failUnlessEqual(len(rows), 0)


    @defer.inlineCallbacks
    def testExitCodeCorrection(self):

        yield self.db.insertJobUsageRecords(ursampledata.UR_BAD_EXIT_CODE)

        rows = yield self.postgres_dbpool.runQuery('SELECT * from usagerecords')
        self.failUnlessEqual(len(rows), 1)
        self.failUnlessEqual(rows[0][31], 166) # corrected from 68774 in the ur




