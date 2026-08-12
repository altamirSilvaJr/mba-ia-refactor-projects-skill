function loadConfig(env = process.env) {
    const port = Number(env.PORT || 3000);
    if (!Number.isInteger(port) || port < 0 || port > 65535) {
        throw new Error('PORT deve ser um inteiro entre 0 e 65535');
    }
    if (!env.ADMIN_API_KEY || env.ADMIN_API_KEY.length < 16) {
        throw new Error('ADMIN_API_KEY deve conter pelo menos 16 caracteres');
    }

    return {
        port,
        adminApiKey: env.ADMIN_API_KEY,
        databasePath: env.DATABASE_PATH || ':memory:'
    };
}

module.exports = { loadConfig };
