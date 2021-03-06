-- logic for upgrading the SGAS PostgreSQL schema from version 3.6.1 to 3.6.2
-- SGAS should be stopped when performing this upgrade

-- Add missing index
CREATE INDEX jobtransferdata_usage_data_id_idx ON jobtransferdata (usage_data_id);

-- Drop View (needed by alter table)
DROP VIEW usagerecords;

-- Alter table
ALTER TABLE usagedata ALTER processors TYPE integer;

-- Create view
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
    localuser.local_user,
    job_name,
    charge,
    jobstatus.status,
    jobqueue.queue,
    host.host,
    node_count,
    processors,
    projectname.project_name,
    submithost.submit_host,
    start_time,
    end_time,
    submit_time,
    cpu_duration,
    wall_duration,
    cpu_duration  * (SELECT scale_factor FROM hostscalefactors WHERE machine_name = machinename.machine_name) AS cpu_duration_scaled,
    wall_duration * (SELECT scale_factor FROM hostscalefactors WHERE machine_name = machinename.machine_name) AS wall_duration_scaled,
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
LEFT OUTER JOIN localuser       ON (usagedata.local_user_id       = localuser.id)
LEFT OUTER JOIN machinename     ON (usagedata.machine_name_id     = machinename.id)
LEFT OUTER JOIN jobqueue        ON (usagedata.queue_id            = jobqueue.id)
LEFT OUTER JOIN host            ON (usagedata.host_id             = host.id)
LEFT OUTER JOIN jobstatus       ON (usagedata.status_id           = jobstatus.id)
LEFT OUTER JOIN projectname     ON (usagedata.project_name_id     = projectname.id)
LEFT OUTER JOIN submithost      ON (usagedata.submit_host_id      = submithost.id)
LEFT OUTER JOIN inserthost      ON (usagedata.insert_host_id      = inserthost.id)
LEFT OUTER JOIN insertidentity  ON (usagedata.insert_identity_id  = insertidentity.id)
;

-- Update functions
CREATE OR REPLACE FUNCTION urcreate (
    in_record_id               varchar,
    in_create_time             timestamp,
    in_global_job_id           varchar,
    in_local_job_id            varchar,
    in_local_user              varchar,
    in_global_user_name        varchar,
    in_vo_type                 varchar,
    in_vo_issuer               varchar,
    in_vo_name                 varchar,
    in_vo_attributes           varchar[][],
    in_machine_name            varchar,
    in_job_name                varchar,
    in_charge                  integer,
    in_status                  varchar,
    in_queue                   varchar,
    in_host                    varchar,
    in_node_count              integer,
    in_processors              integer,
    in_project_name            varchar,
    in_submit_host             varchar,
    in_start_time              timestamp,
    in_end_time                timestamp,
    in_submit_time             timestamp,
    in_cpu_duration            integer,
    in_wall_duration           integer,
    in_user_time               integer,
    in_kernel_time             integer,
    in_major_page_faults       integer,
    in_runtime_environments    varchar[],
    in_exit_code               integer,
    in_downloads               varchar[],
    in_uploads                 varchar[],
    in_insert_host             varchar,
    in_insert_identity         varchar,
    in_insert_time             timestamp
)
RETURNS varchar[] AS $recordid_rowid$

DECLARE
    local_user_fid          integer;
    globalusername_id       integer;
    voinformation_id        integer;
    machinename_id          integer;
    status_fid              integer;
    queue_fid               integer;
    host_fid                integer;
    project_name_fid        integer;
    submit_host_fid         integer;
    inserthost_id           integer;
    insertidentity_id       integer;
    runtime_environment_id  integer;
    jobtransferurl_id       integer;

    ur_id                   integer;
    ur_global_job_id        varchar;
    ur_machine_name_id      integer;
    ur_insert_time          date;

    result                  varchar[];
BEGIN
    -- first check that we do not have the record already
    SELECT usagedata.id, global_job_id, machine_name_id, insert_time::date
           INTO ur_id, ur_global_job_id, ur_machine_name_id, ur_insert_time
           FROM usagedata
           WHERE record_id = in_record_id;
    IF FOUND THEN
        -- this will decide if a record should replace another:
        -- if the global_job_id of the new record is similar to the global_job_id record
        -- it is considered identical. Furthermore if the global_job_id and the record_id
        -- of the incoming record are identical, the record is considered to have minimal
        -- information, and will not replace the existing record
        --
        -- this means that if the incoming record has global_job_id different from the existing
        -- record (they have the same record_id) and its global_job_id is different from the
        -- record_id, the new record will replace the existing record (the ELSE block)
        IF in_global_job_id = ur_global_job_id OR in_global_job_id = in_record_id THEN
            result[0] = in_record_id;
            result[1] = ur_id;
            RETURN result;
        ELSE
            -- delete record, mark update, and continue as normal
            -- technically we should delete job transfers and runtime environments first
            -- however records coming from the LRMS does not contain these, so if an error
            -- occurs here it usally due to an ARC/Grid bug.
            DELETE FROM usagedata WHERE record_id = in_record_id;
            PERFORM * FROM uraggregated_update WHERE insert_time = ur_insert_time::date AND machine_name_id = ur_machine_name_id;
            IF NOT FOUND THEN
                INSERT INTO uraggregated_update (insert_time, machine_name_id) VALUES (ur_insert_time, ur_machine_name_id);
            END IF;
        END IF;
    END IF;

    -- local user name
    IF in_local_user IS NULL THEN
        local_user_fid = NULL;
    ELSE
        SELECT INTO local_user_fid id FROM localuser WHERE local_user = in_local_user;
        IF NOT FOUND THEN
            INSERT INTO localuser (local_user) VALUES (in_local_user) RETURNING id INTO local_user_fid;
        END IF;
    END IF;

    -- global user name
    IF in_global_user_name IS NULL THEN
        globalusername_id = NULL;
    ELSE
        SELECT INTO globalusername_id id
               FROM globalusername
               WHERE global_user_name = in_global_user_name;
        IF NOT FOUND THEN
            INSERT INTO globalusername (global_user_name)
                VALUES (in_global_user_name) RETURNING id INTO globalusername_id;
        END IF;
    END IF;

    -- vo information
    IF in_vo_name is NULL THEN
        voinformation_id = NULL;
    ELSE
        SELECT INTO voinformation_id id
               FROM voinformation
               WHERE vo_type        IS NOT DISTINCT FROM in_vo_type AND
                     vo_issuer      IS NOT DISTINCT FROM in_vo_issuer AND
                     vo_name        IS NOT DISTINCT FROM in_vo_name AND
                     vo_attributes  IS NOT DISTINCT FROM in_vo_attributes;
        IF NOT FOUND THEN
            INSERT INTO voinformation (vo_type, vo_issuer, vo_name, vo_attributes)
                   VALUES (in_vo_type, in_vo_issuer, in_vo_name, in_vo_attributes) RETURNING id INTO voinformation_id;
        END IF;
    END IF;

    -- machine name
    IF in_machine_name IS NULL THEN
        machinename_id = NULL;
    ELSE
        SELECT INTO machinename_id id
               FROM machinename
               WHERE machine_name = in_machine_name;
        IF NOT FOUND THEN
            INSERT INTO machinename (machine_name) VALUES (in_machine_name) RETURNING id INTO machinename_id;
        END IF;
    END IF;

    -- status
    IF in_status IS NULL THEN
        status_fid = NULL;
    ELSE
        SELECT INTO status_fid id FROM jobstatus WHERE status = in_status;
        IF NOT FOUND THEN
            INSERT INTO jobstatus (status) VALUES (in_status) RETURNING id INTO status_fid;
        END IF;
    END IF;

    -- queue
    IF in_queue IS NULL THEN
        queue_fid = NULL;
    ELSE
        SELECT INTO queue_fid id FROM jobqueue WHERE queue = in_queue;
        IF NOT FOUND THEN
            INSERT INTO jobqueue (queue) VALUES (in_queue) RETURNING id INTO queue_fid;
        END IF;
    END IF;

    -- host
    IF in_host IS NULL THEN
        host_fid = NULL;
    ELSE
        SELECT INTO host_fid id FROM host WHERE host = in_host;
        IF NOT FOUND THEN
            INSERT INTO host (host) VALUES (in_host) RETURNING id INTO host_fid;
        END IF;
    END IF;

    -- project name
    IF in_project_name IS NULL THEN
        project_name_fid = NULL;
    ELSE
        SELECT INTO project_name_fid id FROM projectname WHERE project_name = in_project_name;
        IF NOT FOUND THEN
            INSERT INTO projectname (project_name) VALUES (in_project_name) RETURNING id INTO project_name_fid;
        END IF;
    END IF;

    -- submit host
    IF in_submit_host IS NULL THEN
        submit_host_fid = NULL;
    ELSE
        SELECT INTO submit_host_fid id FROM submithost WHERE submit_host = in_submit_host;
        IF NOT FOUND THEN
            INSERT INTO submithost (submit_host) VALUES (in_submit_host) RETURNING id INTO submit_host_fid;
        END IF;
    END IF;

    -- insert host
    IF in_insert_host IS NULL THEN
        inserthost_id = NULL;
    ELSE
        SELECT INTO inserthost_id id
               FROM inserthost
               WHERE insert_host = in_insert_host;
        IF NOT FOUND THEN
            INSERT INTO inserthost (insert_host) VALUES (in_insert_host) RETURNING id INTO inserthost_id;
        END IF;
    END IF;

    -- insert identity
    IF in_insert_identity IS NULL THEN
        insertidentity_id = NULL;
    ELSE
        SELECT INTO insertidentity_id id
               FROM insertidentity
               WHERE insert_identity = in_insert_identity;
        IF NOT FOUND THEN
            INSERT INTO insertidentity (insert_identity) VALUES (in_insert_identity) RETURNING id INTO insertidentity_id;
        END IF;
    END IF;

    INSERT INTO usagedata (
                        record_id,
                        create_time,
                        global_user_name_id,
                        vo_information_id,
                        machine_name_id,
                        global_job_id,
                        local_job_id,
                        local_user_id,
                        job_name,
                        charge,
                        status_id,
                        queue_id,
                        host_id,
                        node_count,
                        processors,
                        project_name_id,
                        submit_host_id,
                        start_time,
                        end_time,
                        submit_time,
                        cpu_duration,
                        wall_duration,
                        user_time,
                        kernel_time,
                        major_page_faults,
                        exit_code,
                        insert_host_id,
                        insert_identity_id,
                        insert_time
                    )
            VALUES (
                        in_record_id,
                        in_create_time,
                        globalusername_id,
                        voinformation_id,
                        machinename_id,
                        in_global_job_id,
                        in_local_job_id,
                        local_user_fid,
                        in_job_name,
                        in_charge,
                        status_fid,
                        queue_fid,
                        host_fid,
                        in_node_count::smallint,
                        in_processors,
                        project_name_fid,
                        submit_host_fid,
                        in_start_time,
                        in_end_time,
                        in_submit_time,
                        in_cpu_duration,
                        in_wall_duration,
                        in_user_time,
                        in_kernel_time,
                        in_major_page_faults,
                        in_exit_code::smallint,
                        inserthost_id,
                        insertidentity_id,
                        in_insert_time
                    )
            RETURNING id into ur_id;

    -- runtime environments
    IF in_runtime_environments IS NOT NULL THEN
        FOR i IN array_lower(in_runtime_environments, 1) .. array_upper(in_runtime_environments, 1) LOOP
            -- check if re exists, isert if it does not
            SELECT INTO runtime_environment_id id FROM runtimeenvironment WHERE runtime_environment = in_runtime_environments[i];
            IF NOT FOUND THEN
                INSERT INTO runtimeenvironment (runtime_environment) VALUES (in_runtime_environments[i]) RETURNING id INTO runtime_environment_id;
            END IF;
            -- insert record ur usage, perform duplicate check first though
            PERFORM * FROM runtimeenvironment_usagedata WHERE usagedata_id = ur_id AND runtime_environment_id = runtimeenvironments_id;
            IF NOT FOUND THEN
                INSERT INTO runtimeenvironment_usagedata (usagedata_id, runtimeenvironments_id) VALUES (ur_id, runtime_environment_id);
            END IF;
        END LOOP;
    END IF;

    -- create rows for file transfers
    IF in_downloads IS NOT NULL THEN
        FOR i IN array_lower(in_downloads, 1) .. array_upper(in_downloads, 1) LOOP
            -- check if url exists, insert if it does not
            SELECT INTO jobtransferurl_id id FROM jobtransferurl WHERE url = in_downloads[i][1];
            IF NOT FOUND THEN
                INSERT INTO jobtransferurl (url) VALUES (in_downloads[i][1]) RETURNING id INTO jobtransferurl_id;
            END IF;
            -- insert download
            INSERT INTO jobtransferdata (usage_data_id, job_transfer_url_id, transfer_type,
                                         size, start_time, end_time, bypass_cache, retrieved_from_cache)
                   VALUES (ur_id, jobtransferurl_id, 'download',
                           in_downloads[i][2]::bigint, in_downloads[i][3]::timestamp, in_downloads[i][4]::timestamp,
                           in_downloads[i][5]::boolean, in_downloads[i][6]::boolean);
        END LOOP;
    END IF;

    IF in_uploads IS NOT NULL THEN
        FOR i IN array_lower(in_uploads, 1) .. array_upper(in_uploads, 1) LOOP
            -- check if url exists, insert if it does not
            SELECT INTO jobtransferurl_id id FROM jobtransferurl WHERE url = in_uploads[i][1];
            IF NOT FOUND THEN
                INSERT INTO jobtransferurl (url) VALUES (in_uploads[i][1]) RETURNING id INTO jobtransferurl_id;
            END IF;
            -- insert upload
            INSERT INTO jobtransferdata (usage_data_id, job_transfer_url_id, transfer_type, size, start_time, end_time)
                   VALUES (ur_id, jobtransferurl_id, 'upload',
                           in_uploads[i][2]::bigint, in_uploads[i][3]::timestamp, in_uploads[i][4]::timestamp);
        END LOOP;
    END IF;

    -- finally we update the table describing what aggregated information should be updated
    PERFORM * FROM uraggregated_update WHERE insert_time = in_insert_time::date AND machine_name_id = machinename_id;
    IF NOT FOUND THEN
        INSERT INTO uraggregated_update (insert_time, machine_name_id) VALUES (in_insert_time::date, machinename_id);
    END IF;

    result[0] = in_record_id;
    result[1] = ur_id;
    RETURN result;

END;
$recordid_rowid$
LANGUAGE plpgsql;
