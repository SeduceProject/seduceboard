from database import ContinuousQueryRecomputeJob
from redlock import RedLock
from database import db
from sqlalchemy import or_
import celery
import time
import datetime
import re
from core.data.influx import influx_run_query


MAX_EXECUTION_TIME_PER_RUN = 5.0
MAX_TIME_DELTA = 3600 * 24 * 30 * 6

@celery.task()
def run_job():
    print("Checking cq_jobs in 'created' or 'waiting' state")

    with RedLock("lock/recomputation_jobs/run_job"):
        jobs = ContinuousQueryRecomputeJob.query.filter(or_(ContinuousQueryRecomputeJob.state == "created",
                                                            ContinuousQueryRecomputeJob.state == "waiting")).all()
        for recomputation_job in jobs:
            if recomputation_job.state == "created":
                recomputation_job.last_run_start = recomputation_job.time_interval_end
                recomputation_job.last_run_end = recomputation_job.time_interval_end

            time_interval_start_ts = float(time.mktime(recomputation_job.time_interval_start.timetuple()))
            last_run_start_ts = float(time.mktime(recomputation_job.last_run_start.timetuple()))

            if last_run_start_ts > time_interval_start_ts:

                if recomputation_job.last_execution_time:
                    interval_processed = recomputation_job.last_run_end.timestamp() - recomputation_job.last_run_start.timestamp()
                    time_delta = interval_processed * (MAX_EXECUTION_TIME_PER_RUN / recomputation_job.last_execution_time)
                else:
                    time_delta = 12 * 3600

                time_delta = min(time_delta, MAX_TIME_DELTA)

                recomputation_job.last_run_end = recomputation_job.last_run_start
                recomputation_job.last_run_start = recomputation_job.last_run_end - datetime.timedelta(seconds=time_delta)

                if time_delta == 0.0:
                    recomputation_job.finish()
                else:
                    recomputation_job.run()

                db.session.add(recomputation_job)
                db.session.commit()
        db.session.remove()


@celery.task()
def wait_job():
    from core.continuous_queries.continuous_queries import get_continuous_query_by_name,cq_generate_update_query
    print("Checking cq_jobs in 'running' state")

    with RedLock("lock/recomputation_jobs/wait_job"):
        jobs = ContinuousQueryRecomputeJob.query.filter(or_(ContinuousQueryRecomputeJob.state == "running")).all()
        jobs = sorted(jobs, key=lambda x: 1 if x.priority == "high" else 2)
        for recomputation_job in jobs:
            # I will execute re-execute the continuous query
            cq = get_continuous_query_by_name(recomputation_job.cq_name)

            last_run_start_ts = int(time.mktime(recomputation_job.last_run_start.timetuple()))
            last_run_end_ts = int(time.mktime(recomputation_job.last_run_end.timetuple()))

            last_run_start_ts = max(last_run_start_ts, 0)
            last_run_end_ts = max(last_run_end_ts, 0)

            cq_update_query = cq_generate_update_query(recomputation_job.cq_name, last_run_start_ts, last_run_end_ts)

            execution_start = time.time()
            result = influx_run_query(cq_update_query)
            execution_end = time.time()
            recomputation_job.last_execution_time = execution_end - execution_start

            recomputation_job.wait()
            db.session.add(recomputation_job)
            db.session.commit()
            pass
        db.session.remove()
    pass


@celery.task()
def finish_job():
    print("Checking cq_jobs in 'waiting' state")

    with RedLock("lock/recomputation_jobs/run_job"):
        jobs = ContinuousQueryRecomputeJob.query.filter(ContinuousQueryRecomputeJob.state == "waiting").all()
        for recomputation_job in jobs:
            time_interval_start_ts = float(time.mktime(recomputation_job.time_interval_start.timetuple()))
            last_run_start_ts = float(time.mktime(recomputation_job.last_run_start.timetuple()))

            if last_run_start_ts <= time_interval_start_ts:
                recomputation_job.finish()
                db.session.add(recomputation_job)
                db.session.commit()
        db.session.remove()
    pass
