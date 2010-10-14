"""
Query builder SGAS queryengine.

Used for creating SQL query from a set of query arguments.

Author: Henrik Thostrup Jensen <htj@ndgf.org>
Copyright: Nordic Data Grid Facility (2010)
"""



def buildQuery(query_args):

    print "QA", query_args

    user_identities = query_args.get('user_identity')
    machine_names   = query_args.get('machine_name')
    vo_name         = query_args.get('vo_name')
    start_date      = query_args.get('start_date')
    end_date        = query_args.get('end_date')
    time_resolution = query_args.get('time_resolution')

    assert time_resolution in ['day', 'week', 'month', 'collapse'], 'Invalid time resolution specified'

    date_extract, date_grouping = _getStartEndDatesAndGrouping(query_args)
    print "DE", date_extract
    print "DG", date_grouping

    query_args = [] # RENAME me!

    query = "SELECT machine_name, user_identity, "
    if vo_name:
        query += "vo_name, "
    query += date_extract

    query += "sum(n_jobs), sum(cputime), sum(walltime) "
    query += "FROM uraggregated "
    query += "WHERE execution_time > %s AND execution_time < %s "
    query_args.append(start_date)
    query_args.append(end_date)

    if user_identities:
        query += 'AND user_identity IN %s '
        query_args.append(tuple(user_identities))
    if machine_names:
        query += 'AND machine_name IN %s '
        query_args.append(tuple(machine_names))
    if vo_name:
        query += 'AND vo_name = %s '
        query_args.append(vo_name)

    if query.endswith(','):
        query = query[:-1]

    query += "GROUP BY "
    if user_identities:
        query += 'user_identity,'
    if machine_names:
        query += 'machine_name,'
    if vo_name:
        query += 'vo_name,'

    query += date_grouping

    if query.endswith(','):
        query = query[:-1]

#    query_args += [start_date, end_date, machine_names[0], user_identities[0] ]

    print "Q", query
    print "A", query_args
    return query, query_args



def _getStartEndDatesAndGrouping(query_args):

    time_resolution = query_args.get('time_resolution')

    if time_resolution == 'day':
        dates = 'execution_time, execution_time, '
        group = 'execution_time,'

    elif time_resolution == 'week':
        dates = ''
        group = "date_part('year', current_date) || '-' || date_part('week', current_date),"

    elif time_resolution == 'montly':
        dates = ' .. '
        group = "date_part('year', current_date) || '-' || date_part('month', current_date),"

    elif time_resolution == 'collapse':
        dates = '%s, %s, ' % (query_args.get('start_date'), query_args.get('end_date'))
        group = ''

    return dates, group


