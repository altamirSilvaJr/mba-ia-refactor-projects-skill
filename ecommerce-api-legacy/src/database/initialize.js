const crypto = require('crypto');

async function initializeDatabase(db, passwordHasher) {
    await db.run('PRAGMA foreign_keys = ON');
    await db.run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, pass TEXT NOT NULL)');
    await db.run('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT NOT NULL, price REAL NOT NULL, active INTEGER NOT NULL)');
    await db.run('CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT)');
    await db.run('CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE, amount REAL NOT NULL, status TEXT NOT NULL)');
    await db.run('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT NOT NULL, created_at DATETIME NOT NULL)');

    const seedPassword = await passwordHasher.hash(crypto.randomBytes(32).toString('hex'));
    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', ['Leonan', 'leonan@fullcycle.com.br', seedPassword]);
    await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)', ['Clean Architecture', 997, 1, 'Docker', 497, 1]);
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
    await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [1, 997, 'PAID']);
}

module.exports = { initializeDatabase };
