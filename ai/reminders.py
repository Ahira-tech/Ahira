from ai.database import get_connection


def add_reminder(task, date=None, time=None, priority="normal", user_id=1):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO reminders (user_id, task, date, time, priority, completed)
        VALUES (?, ?, ?, ?, ?, 0)
    """, (user_id, task, date, time, priority))
    conn.commit()
    conn.close()


def get_reminders(user_id=1):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, task, date, time, priority, completed
        FROM reminders
        WHERE user_id = ?
        ORDER BY completed ASC, id DESC
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_reminder(reminder_id, user_id=1):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE id=? AND user_id=?", (reminder_id, user_id))
    conn.commit()
    conn.close()


def toggle_reminder(reminder_id, user_id=1):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE reminders
        SET completed = CASE WHEN completed=1 THEN 0 ELSE 1 END
        WHERE id=? AND user_id=?
    """, (reminder_id, user_id))
    conn.commit()
    conn.close()