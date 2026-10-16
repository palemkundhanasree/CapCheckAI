import sqlite3

conn = sqlite3.connect('storage/capcheck.db')
cursor = conn.cursor()
cursor.execute('SELECT id, email, username FROM users')
users = cursor.fetchall()
print("Users:", users)

cursor.execute("SELECT id, user_id, title FROM reports WHERE user_id IS NULL")
orphans = cursor.fetchall()
print("Orphan reports:", orphans)

if orphans and users:
    admin_id = users[0][0]
    cursor.execute("UPDATE reports SET user_id = ? WHERE user_id IS NULL", (admin_id,))
    cursor.execute("UPDATE verification_jobs SET user_id = ? WHERE user_id IS NULL", (admin_id,))
    conn.commit()
    print(f"Updated orphan records to user_id: {admin_id}")
