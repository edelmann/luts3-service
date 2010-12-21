-- create view of the usage records in the database
-- the purpose of the view is to make data easily accessable so users do not
-- have to do the joins between the tables them selves.

CREATE VIEW usagerecords AS
SELECT
    record_id,
    create_time,
    globalusername.global_user_name,
    voinformation.vo_type,
    voinformation.vo_issuer,
    voinformation.vo_name,
    voinformation.vo_attributes,
    machinename.machine_name,
    global_job_id,
    local_job_id,
    local_user_id,
    job_name,
    charge,
    jobstatus.status,
    jobqueue.queue,
    host,
    node_count,
    processors,
    project_name,
    submit_host,
    start_time,
    end_time,
    submit_time,
    cpu_duration,
    wall_duration,
    user_time,
    kernel_time,
    major_page_faults,
    ARRAY(SELECT runtimeenvironment.runtime_environment
          FROM runtimeenvironment, runtimeenvironment_usagedata
          WHERE usagedata.id = runtimeenvironment_usagedata.usagedata_id AND
                runtimeenvironment_usagedata.runtimeenvironments_id = runtimeenvironment.id)
    AS runtime_environments,
    exit_code,
    inserthost.insert_host,
    insertidentity.insert_identity,
    insert_time
FROM
    usagedata
LEFT OUTER JOIN globalusername  ON (usagedata.global_user_name_id = globalusername.id)
LEFT OUTER JOIN voinformation   ON (usagedata.vo_information_id   = voinformation.id)
LEFT OUTER JOIN machinename     ON (usagedata.machine_name_id     = machinename.id)
LEFT OUTER JOIN jobqueue        ON (usagedata.queue_id            = jobqueue.id)
LEFT OUTER JOIN jobstatus       ON (usagedata.status_id           = jobstatus.id)
LEFT OUTER JOIN inserthost      ON (usagedata.insert_host_id      = inserthost.id)
LEFT OUTER JOIN insertidentity  ON (usagedata.insert_identity_id  = insertidentity.id)
;


CREATE VIEW transfers AS
SELECT
    machinename.machine_name                AS machine_name,
    voinformation.vo_name                   AS vo_name,
    voinformation.vo_attributes[1][1]       AS vo_group,
    voinformation.vo_attributes[1][2]       AS vo_role,
    globalusername.global_user_name         AS global_user_name,
    jobtransferurl.url                      AS url,
    jobtransferdata.transfer_type           AS transfer_type,
    jobtransferdata.size                    AS size,
    jobtransferdata.start_time              AS start_time,
    jobtransferdata.end_time                AS end_time,
    jobtransferdata.bypass_cache            AS bypass_cache,
    jobtransferdata.retrieved_from_cache    AS retrieved_from_cache
FROM
    jobtransferdata
LEFT OUTER JOIN jobtransferurl  ON (jobtransferdata.job_transfer_url_id = jobtransferurl.id)
LEFT OUTER JOIN usagedata       ON (jobtransferdata.usage_data_id       = usagedata.id)
LEFT OUTER JOIN machinename     ON (usagedata.machine_name_id           = machinename.id)
LEFT OUTER JOIN voinformation   ON (usagedata.vo_information_id         = voinformation.id)
LEFT OUTER JOIN globalusername  ON (usagedata.global_user_name_id       = globalusername.id)
;


CREATE VIEW uraggregated AS
SELECT
    execution_time                                                                  AS execution_time,
    insert_time                                                                     AS insert_time,
    machinename.machine_name                                                        AS machine_name,
    jobqueue.queue                                                                  AS queue,
    CASE WHEN global_user_name_id IS NOT NULL THEN globalusername.global_user_name
        ELSE machine_name || ':' || local_user_id
    END                                                                             AS user_identity,
    CASE WHEN vo_information_id IS NOT NULL THEN
        CASE WHEN voinformation.vo_issuer LIKE 'file:///%' THEN NULL
             WHEN voinformation.vo_issuer LIKE 'http://%'  THEN NULL
             WHEN voinformation.vo_issuer LIKE 'https://%' THEN NULL
             ELSE voinformation.vo_issuer
        END
        ELSE NULL
    END                                                                             AS s_vo_issuer,
    CASE WHEN vo_information_id IS NOT NULL THEN
        CASE WHEN voinformation.vo_name LIKE '/%' THEN NULL
             ELSE voinformation.vo_name
        END
        ELSE machine_name || ':' || project_name
    END                                                                             AS vo_name,
    voinformation.vo_attributes[1][1]                                               AS vo_group,
    voinformation.vo_attributes[1][2]                                               AS vo_role,
    CASE WHEN runtime_environments_id IS NOT NULL
        THEN ARRAY(SELECT runtime_environment FROM runtimeenvironment WHERE id IN (SELECT unnest(runtime_environments_id)))
        ELSE NULL
    END                                                                             AS runtime_environments,
    jobstatus.status                                                                AS status,
    n_jobs                                                                          AS n_jobs,
    cputime                                                                         AS cputime,
    walltime                                                                        AS walltime,
    generate_time                                                                   AS generate_time
FROM
    uraggregated_data
LEFT OUTER JOIN machinename         ON (uraggregated_data.machine_name_id     = machinename.id)
LEFT OUTER JOIN jobqueue            ON (uraggregated_data.queue_id            = jobqueue.id)
LEFT OUTER JOIN globalusername      ON (uraggregated_data.global_user_name_id = globalusername.id)
LEFT OUTER JOIN voinformation       ON (uraggregated_data.vo_information_id   = voinformation.id)
LEFT OUTER JOIN jobstatus           ON (uraggregated_data.status_id           = jobstatus.id)
;

