class DeleteUserService {
    constructor(users, db) { this.users = users; this.db = db; }
    execute(id) { return this.db.transaction(() => this.users.deleteById(id)); }
}

module.exports = DeleteUserService;
