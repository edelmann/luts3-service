"""
Parser for converting usage records into statements for inserting data into
PostgreSQL.

Author: Henrik Thostrup Jensen
Copyright: Nordic Data Grid Facility (2010)
"""



ARG_LIST = [
    'record_id',
    'create_time',
    'global_job_id',
    'local_job_id',
    'local_user_id',
    'global_user_name',
    'vo_type',
    'vo_issuer',
    'vo_name',
    'vo_attributes',
    'machine_name',
    'job_name',
    'charge',
    'status',
    'queue',
    'host',
    'node_count',
    'processors',
    'project_name',
    'submit_host',
    'start_time',
    'end_time',
    'submit_time',
    'cpu_duration',
    'wall_duration',
    'user_time',
    'kernel_time',
    'major_page_faults',
    'runtime_environments',
    'exit_code',
    'downloads',
    'uploads',
    'insert_hostname',
    'insert_identity',
    'insert_time'
]



def createInsertArguments(usagerecord_docs, insert_identity=None, insert_hostname=None):

    stringify = lambda f : str(f) if f is not None else None

    args = []

    for ur_doc in usagerecord_docs:

        # convert vo attributes into arrays (adaption is done by psycopg2)
        if 'vo_attrs' in ur_doc:
            vo_attrs = [ [ e.get('group'), e.get('role') ] for e in ur_doc['vo_attrs'] ]
            #ur_doc['vo_attributes'] = [ [ str(f) if f else None for f in e ] for e in vo_attrs ]
            ur_doc['vo_attributes'] = [ [ stringify(f) for f in e ] for e in vo_attrs ]

        if 'downloads' in ur_doc:
            dls = []
            for dl in ur_doc['downloads']:
                dla = dl.get('url'), dl.get('size'), dl.get('start_time'), dl.get('end_time'), dl.get('bypass_cache'), dl.get('from_cache')
                dls.append(dla)
            ur_doc['downloads'] = [ [ stringify(f) for f in e  ] for e in dls ]

        if 'uploads' in ur_doc:
            uls = []
            for ul in ur_doc['uploads']:
                ula = ul.get('url'), dl.get('size'), dl.get('start_time'), dl.get('end_time')
                uls.append(ula)
            ur_doc['uploads'] = [ [ stringify(f) for f in e  ] for e in uls ]

        arg = [ ur_doc.get(a, None) for a in ARG_LIST ]
        args.append(arg)

    return args

