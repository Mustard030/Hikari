# task
CREATE_LINK_TASK_SQL = r"""INSERT INTO task (content, fail, complete, create_date) VALUES (%s, 0, 0, now())"""
UPDATE_TASK_DONE_SQL = r"""UPDATE task SET complete=1, complete_date=now() WHERE id=%s"""
UPDATE_TASK_FAIL_SQL = r"""UPDATE task SET fail=1, reason=%s WHERE id=%s"""
CHECK_DUPLICATED_TASK_ID_SQL = r"""SELECT `id`, complete, fail FROM task WHERE content=%s LIMIT 1"""
QUERY_HISTORY_BY_TASK_ID_SQL = r"""SELECT `id`, `source`, picUrl, local_path, complete, task_id, author_id FROM download_history WHERE task_id=%s"""

# author
CREATE_AUTHOR_SQL = r"""INSERT INTO author (platform, `name`, userid) VALUES (%s, %s, %s)"""
QUERY_AUTHOR_SQL = r"""SELECT `id` FROM author WHERE platform=%s AND `name`=%s AND userid=%s LIMIT 1"""

# download_history
CREATE_DOWNLOAD_HISTORY_SQL = r"""INSERT INTO download_history (`source`, picUrl, local_path, complete, submit_date, task_id, author_id) 
							  VALUES (%s, %s, %s, 0, now(), %s, %s)"""
UPDATE_DOWNLOAD_DONE_SQL = r"""UPDATE download_history SET complete=1, complete_date=now() 
							   WHERE id=%s"""
