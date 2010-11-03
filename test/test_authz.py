#
# Authorization tests
#
# Author: Henrik Thostrup Jensen <htj@ndgf.org>
# Copyright: Nordic Data Grid Facility (2010)

from twisted.trial import unittest

from sgas.authz import engine, rights

# includes all basic authz types and some basic combinations
# there will probably be more later
TEST_AUTHZ_DATA = """
"host1"     insert
"host2"     insert:all
"host3"     insert:machine_name=host2
"host4.ex.org" insert:machine_name=host2
# comment
"user1"     view
"user2"     view:view=viewname
"user3"     view:group=vg1
"user4"     view:group=vg1, view:group=vg2
"user5"     view:group=vg1;vg2
"user6"     view:all

"bot1"      query:all
"bot2"      query:machine_name=host1
"bot3"      query:user_identity=user1
"bot4"      query:user_identity=user1, query:user_identity=user3
"bot5"      query:machine_name=host2+user_identity=user2
"bot6"      query:machine_name=host2+user_identity=user2;user4
"bot7"      query:vo_name=vo1
"""


class AuthzTest(unittest.TestCase):


    def setUp(self):
        self.authz = engine.AuthorizationEngine(insert_check_depth=2)
        self.authz.parseAuthzData(TEST_AUTHZ_DATA)


    def tearDown(self):
        pass


    def testInsertAuthz(self):
        # "host1"     insert
        # "host2"     insert:all
        # "host3"     insert:machine_name=host2
        # "host4.ex.org" insert:machine_name=host2

        self.failUnlessTrue(  self.authz.hasRelevantRight('host1', rights.ACTION_INSERT) )
        self.failUnlessTrue(  self.authz.hasRelevantRight('host2', rights.ACTION_INSERT) )
        self.failUnlessTrue(  self.authz.hasRelevantRight('host3', rights.ACTION_INSERT) )
        self.failUnlessFalse( self.authz.hasRelevantRight('user1', rights.ACTION_INSERT) )
        self.failUnlessFalse( self.authz.hasRelevantRight('bot1',  rights.ACTION_INSERT) )


        self.failUnlessFalse( self.authz.isAllowed('host_unknown', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host_unknown')] ))

        self.failUnlessTrue(  self.authz.isAllowed('host1', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host1')] ))
        self.failUnlessFalse( self.authz.isAllowed('host1', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host2')] ) )

        self.failUnlessTrue(  self.authz.isAllowed('host2', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host2')] ) )
        self.failUnlessTrue(  self.authz.isAllowed('host2', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host1')] ) )
        self.failUnlessTrue(  self.authz.isAllowed('host2', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host3')] ) )
        # can a host insert a usage record with a certain user - yes it can
        # doesn't make a that much of sense, but it can
        self.failUnlessTrue(  self.authz.isAllowed('host2', rights.ACTION_INSERT, [( rights.CTX_USER_IDENTITY, 'user1')] ) )

        self.failUnlessTrue(  self.authz.isAllowed('host3', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host3')]) )
        self.failUnlessTrue(  self.authz.isAllowed('host3', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host2')] ) )
        self.failUnlessFalse( self.authz.isAllowed('host3', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host1')] ) )

        self.failUnlessTrue(  self.authz.isAllowed('host4.ex.org', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host2.ex.org')] ) )
        self.failUnlessTrue(  self.authz.isAllowed('host4.ex.org', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host4.ex.org')] ) )
        self.failUnlessTrue(  self.authz.isAllowed('host4.ex.org', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host2')] ) )
        self.failUnlessFalse( self.authz.isAllowed('host4.ex.org', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host1')] ) )

        self.failUnlessFalse( self.authz.isAllowed('user1', rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host3')]) )
        self.failUnlessFalse( self.authz.isAllowed('bot1',  rights.ACTION_INSERT, [( rights.CTX_MACHINE_NAME, 'host1')]) )


    def testViewAuthz(self):
        # "user1"     view
        # "user2"     view:view=viewname
        # "user3"     view:group=vg1
        # "user4"     view:group=vg1, view:group=vg2
        # "user5"     view:group=vg1;vg2
        # "user6"     view:all

        self.failUnlessTrue(  self.authz.hasRelevantRight('user1', rights.ACTION_VIEW) )
        self.failUnlessTrue(  self.authz.hasRelevantRight('user2', rights.ACTION_VIEW) )
        self.failUnlessTrue(  self.authz.hasRelevantRight('user3', rights.ACTION_VIEW) )
        self.failUnlessTrue(  self.authz.hasRelevantRight('user4', rights.ACTION_VIEW) )
        self.failUnlessTrue(  self.authz.hasRelevantRight('user5', rights.ACTION_VIEW) )
        self.failUnlessTrue(  self.authz.hasRelevantRight('user6', rights.ACTION_VIEW) )

        self.failUnlessFalse( self.authz.hasRelevantRight('host1', rights.ACTION_VIEW) )
        self.failUnlessFalse( self.authz.hasRelevantRight('host3', rights.ACTION_VIEW) )
        self.failUnlessFalse( self.authz.hasRelevantRight('bot1',  rights.ACTION_VIEW) )
        self.failUnlessFalse( self.authz.hasRelevantRight('bot4',  rights.ACTION_VIEW) )


        self.failUnlessTrue  ( self.authz.isAllowed('user1', rights.ACTION_VIEW, [(rights.CTX_VIEW, 'viewname' )] ) )
        self.failUnlessTrue  ( self.authz.isAllowed('user1', rights.ACTION_VIEW, [(rights.CTX_VIEWGROUP, 'vg1' )] ) )

        self.failUnlessTrue  ( self.authz.isAllowed('user2', rights.ACTION_VIEW, [(rights.CTX_VIEW, 'viewname' )] ) )
        self.failUnlessFalse ( self.authz.isAllowed('user2', rights.ACTION_VIEW, [(rights.CTX_VIEW, 'otherview')] ) )

        self.failUnlessTrue  ( self.authz.isAllowed('user3', rights.ACTION_VIEW, [(rights.CTX_VIEWGROUP, 'vg1')] ) )
        self.failUnlessFalse ( self.authz.isAllowed('user3', rights.ACTION_VIEW, [(rights.CTX_VIEWGROUP, 'vg2')] ) )
        self.failUnlessFalse ( self.authz.isAllowed('user3', rights.ACTION_VIEW, [(rights.CTX_VIEW, 'viewname')] ) )
        self.failUnlessFalse ( self.authz.isAllowed('user3', rights.ACTION_VIEW, [(rights.CTX_VIEW, 'otherview')] ) )
        self.failUnlessTrue  ( self.authz.isAllowed('user3', rights.ACTION_VIEW, [(rights.CTX_VIEW, 'otherview'), (rights.CTX_VIEWGROUP, 'vg1')]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('user3', rights.ACTION_VIEW, [(rights.CTX_VIEWGROUP, 'vg1'), (rights.CTX_VIEWGROUP, 'vg2')]  ) )

        self.failUnlessFalse ( self.authz.isAllowed('user4', rights.ACTION_VIEW, [( rights.CTX_VIEWGROUP, 'vg3')]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('user4', rights.ACTION_VIEW, [( rights.CTX_VIEW, 'viewname')]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('user4', rights.ACTION_VIEW, [( rights.CTX_VIEWGROUP, 'vg1')]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('user4', rights.ACTION_VIEW, [( rights.CTX_VIEW, 'otherview'), (rights.CTX_VIEWGROUP, 'vg2')]  ) )

        self.failUnlessFalse ( self.authz.isAllowed('user5', rights.ACTION_VIEW, [( rights.CTX_VIEWGROUP, 'vg3')]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('user5', rights.ACTION_VIEW, [( rights.CTX_VIEW, 'viewname')]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('user5', rights.ACTION_VIEW, [( rights.CTX_VIEWGROUP, 'vg1')]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('user5', rights.ACTION_VIEW, [( rights.CTX_VIEW, 'otherview'), (rights.CTX_VIEWGROUP, 'vg2')]  ) )

        self.failUnlessTrue  ( self.authz.isAllowed('user6', rights.ACTION_VIEW, [( rights.CTX_VIEWGROUP, 'vg3')]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('user6', rights.ACTION_VIEW, [( rights.CTX_VIEW, 'viewname')]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('user6', rights.ACTION_VIEW, [( rights.CTX_VIEWGROUP, 'vg1')]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('user5', rights.ACTION_VIEW, [( rights.CTX_VIEW, 'otherview'), (rights.CTX_VIEWGROUP, 'vg2')]  ) )


    def testQueryAuthz(self):
        # "bot1"      query:all
        # "bot2"      query:machine_name=host1
        # "bot3"      query:user_identity=user1
        # "bot4"      query:user_identity=user1, query:user_identity=user3
        # "bot5"      query:machine_name=host2+user_identity=user2
        # "bot6"      query:machine_name=host2+user_identity=user2;user4
        # "bot7"      query:vo_name=vo1

        self.failUnlessTrue(  self.authz.hasRelevantRight('bot1', rights.ACTION_QUERY) )
        self.failUnlessTrue(  self.authz.hasRelevantRight('bot2', rights.ACTION_QUERY) )
        self.failUnlessTrue(  self.authz.hasRelevantRight('bot3', rights.ACTION_QUERY) )
        self.failUnlessTrue(  self.authz.hasRelevantRight('bot4', rights.ACTION_QUERY) )
        self.failUnlessTrue(  self.authz.hasRelevantRight('bot5', rights.ACTION_QUERY) )
        self.failUnlessTrue(  self.authz.hasRelevantRight('bot6', rights.ACTION_QUERY) )
        self.failUnlessTrue(  self.authz.hasRelevantRight('bot7', rights.ACTION_QUERY) )

        self.failUnlessFalse( self.authz.hasRelevantRight('host2', rights.ACTION_QUERY) )
        self.failUnlessFalse( self.authz.hasRelevantRight('host4', rights.ACTION_QUERY) )
        self.failUnlessFalse( self.authz.hasRelevantRight('user1', rights.ACTION_QUERY) )
        self.failUnlessFalse( self.authz.hasRelevantRight('user5', rights.ACTION_QUERY) )


        self.failUnlessTrue  ( self.authz.isAllowed('bot1', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host1' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot1', rights.ACTION_QUERY, [( rights.CTX_USER_IDENTITY, 'user1' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot1', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host1', rights.CTX_USER_IDENTITY, 'user2' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot1', rights.ACTION_QUERY, [( rights.CTX_VO_NAME, 'vo1' )]  ) )

        self.failUnlessTrue  ( self.authz.isAllowed('bot2', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host1' )]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('bot2', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2' )]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('bot2', rights.ACTION_QUERY, [( rights.CTX_USER_IDENTITY, 'user1' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot2', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host1'), (rights.CTX_USER_IDENTITY, 'user1' )]  ) )

        self.failUnlessFalse ( self.authz.isAllowed('bot3', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host1' )]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('bot3', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot3', rights.ACTION_QUERY, [( rights.CTX_USER_IDENTITY, 'user1' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot3', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host1'), (rights.CTX_USER_IDENTITY, 'user1' )]  ) )

        self.failUnlessFalse ( self.authz.isAllowed('bot4', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host1' )]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('bot4', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot4', rights.ACTION_QUERY, [( rights.CTX_USER_IDENTITY, 'user1' )]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('bot4', rights.ACTION_QUERY, [( rights.CTX_USER_IDENTITY, 'user2' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot4', rights.ACTION_QUERY, [( rights.CTX_USER_IDENTITY, 'user3' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot4', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host1'), (rights.CTX_USER_IDENTITY, 'user1' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot4', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2'), (rights.CTX_USER_IDENTITY, 'user3' )]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('bot4', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2'), (rights.CTX_USER_IDENTITY, 'user2' )]  ) )

        self.failUnlessFalse ( self.authz.isAllowed('bot5', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2' )]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('bot5', rights.ACTION_QUERY, [( rights.CTX_USER_IDENTITY, 'user2' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot5', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2'), (rights.CTX_USER_IDENTITY, 'user2' )]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('bot5', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2'), (rights.CTX_USER_IDENTITY, 'user1' )]  ) )

        self.failUnlessFalse ( self.authz.isAllowed('bot6', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host1' )]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('bot6', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2' )]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('bot6', rights.ACTION_QUERY, [( rights.CTX_USER_IDENTITY, 'user2' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot6', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2'), (rights.CTX_USER_IDENTITY, 'user2' )]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('bot6', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2'), (rights.CTX_USER_IDENTITY, 'user3' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot6', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2'), (rights.CTX_USER_IDENTITY, 'user4' )]  ) )

        self.failUnlessFalse ( self.authz.isAllowed('bot7', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2' )]  ) )
        self.failUnlessFalse ( self.authz.isAllowed('bot7', rights.ACTION_QUERY, [( rights.CTX_USER_IDENTITY, 'user1' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot7', rights.ACTION_QUERY, [( rights.CTX_VO_NAME, 'vo1' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot7', rights.ACTION_QUERY, [( rights.CTX_MACHINE_NAME, 'host2'), (rights.CTX_VO_NAME, 'vo1' )]  ) )
        self.failUnlessTrue  ( self.authz.isAllowed('bot7', rights.ACTION_QUERY, [( rights.CTX_USER_IDENTITY, 'user1'), (rights.CTX_VO_NAME, 'vo1' )]  ) )

