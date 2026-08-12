const sqlite3 = require('sqlite3').verbose();

class Database {
    constructor(filename = ':memory:') {
        this.connection = new sqlite3.Database(filename);
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.run(sql, params, function onResult(error) {
                if (error) return reject(error);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.get(sql, params, (error, row) => {
                if (error) return reject(error);
                resolve(row);
            });
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.all(sql, params, (error, rows) => {
                if (error) return reject(error);
                resolve(rows);
            });
        });
    }

    async transaction(work) {
        await this.run('BEGIN IMMEDIATE');
        try {
            const result = await work();
            await this.run('COMMIT');
            return result;
        } catch (error) {
            await this.run('ROLLBACK');
            throw error;
        }
    }

    close() {
        return new Promise((resolve, reject) => {
            this.connection.close((error) => error ? reject(error) : resolve());
        });
    }
}

module.exports = Database;
