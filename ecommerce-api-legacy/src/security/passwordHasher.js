const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);

class PasswordHasher {
    async hash(password) {
        const salt = crypto.randomBytes(16).toString('hex');
        const derivedKey = await scrypt(password, salt, 64);
        return `scrypt$${salt}$${derivedKey.toString('hex')}`;
    }
}

module.exports = PasswordHasher;
