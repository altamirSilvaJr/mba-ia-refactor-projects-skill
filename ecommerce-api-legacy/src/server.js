const { loadConfig } = require('./config');
const { createApplication } = require('./app');

async function start() {
    const config = loadConfig();
    const { app, db } = await createApplication(config);
    const server = app.listen(config.port, () => console.log(`LMS API rodando na porta ${config.port}...`));

    const shutdown = () => server.close(() => db.close().finally(() => process.exit(0)));
    process.once('SIGINT', shutdown);
    process.once('SIGTERM', shutdown);
}

start().catch((error) => {
    console.error('Falha ao iniciar a aplicação:', error.message);
    process.exit(1);
});
