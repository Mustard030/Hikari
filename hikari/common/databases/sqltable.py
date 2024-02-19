########################################
# task
CREATE_TASK_SQL = r"""INSERT INTO task (content, fail, complete, create_date, retry) VALUES (%s, 0, 0, now(), 0)"""
UPDATE_TASK_DONE_SQL = r"""UPDATE task SET complete=1, complete_date=now(),fail=0,reason=NULL WHERE id=%s"""
UPDATE_TASK_FAIL_SQL = r"""UPDATE task SET complete=0,fail=1, complete_date=NULL, reason=%s WHERE id=%s"""
QUERY_DUPLICATED_TASK_ID_SQL = r"""SELECT `id`, content, complete, fail, reason FROM task WHERE content=%s LIMIT 1"""
INCREASE_RETRY_TIMES = r"""UPDATE task 
						   SET retry=retry+1 
						   WHERE id = %s"""
QUERY_TASK_BY_ID_SQL = r"""SELECT id, content, complete, fail, reason, retry FROM task WHERE id=%s"""
QUERY_UNCOMPLETE_AND_RETRY_LEAST_TIMES_TASK_SQL = r"""SELECT id,content,complete,fail,reason,retry 
															FROM task 
															WHERE complete=0 AND retry<=20
															ORDER BY retry 
															LIMIT 1"""
########################################

########################################
# author
CREATE_AUTHOR_SQL = r"""INSERT INTO author (platform, `name`, userid) VALUES (%s, %s, %s)"""
QUERY_AUTHOR_SQL = r"""SELECT `id` FROM author 
					   WHERE platform=%s AND `name`=%s AND userid=%s LIMIT 1"""
########################################

########################################
# download_history
QUERY_HISTORY_BY_TASK_ID_SQL = r"""SELECT `id`, `source`, url, local_path, complete, task_id, author_id, filetype FROM download_history WHERE task_id=%s"""
CREATE_DOWNLOAD_HISTORY_SQL = r"""INSERT INTO download_history (`source`, url, local_path, complete, submit_date, task_id, author_id, filetype) 
							      VALUES (%s, %s, %s, 0, now(), %s, %s, %s)"""

UPDATE_DOWNLOAD_DONE_SQL = r"""UPDATE download_history 
							   SET complete=1, complete_date=now() 
							   WHERE id=%s"""
########################################
