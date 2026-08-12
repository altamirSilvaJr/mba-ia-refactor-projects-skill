const assert = require('assert');
const http = require('http');
const { createApplication } = require('../src/app');
const { parseCheckoutInput } = require('../src/validation/checkoutInput');
const PasswordHasher = require('../src/security/passwordHasher');

const ADMIN_KEY = 'test-admin-key-with-32-characters';

function request(server, method, path, options = {}) {
    const body = options.body === undefined ? null : JSON.stringify(options.body);
    const address = server.address();
    return new Promise((resolve, reject) => {
        const req = http.request({
            hostname: '127.0.0.1',
            port: address.port,
            method,
            path,
            headers: {
                ...(body ? { 'content-type': 'application/json', 'content-length': Buffer.byteLength(body) } : {}),
                ...(options.apiKey ? { 'x-api-key': options.apiKey } : {})
            }
        }, (res) => {
            let responseBody = '';
            res.setEncoding('utf8');
            res.on('data', (chunk) => { responseBody += chunk; });
            res.on('end', () => resolve({ status: res.statusCode, contentType: res.headers['content-type'], body: responseBody }));
        });
        req.on('error', reject);
        if (body) req.write(body);
        req.end();
    });
}

async function withApplication(test) {
    const { app, db } = await createApplication({ port: 0, adminApiKey: ADMIN_KEY, databasePath: ':memory:' });
    const server = app.listen(0, '127.0.0.1');
    await new Promise((resolve, reject) => {
        server.once('listening', resolve);
        server.once('error', reject);
    });
    try { await test({ server, db }); }
    finally {
        await new Promise((resolve) => server.close(resolve));
        await db.close();
    }
}

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

test('validação rejeita payload inseguro e normaliza payload válido', () => {
    assert.throws(() => parseCheckoutInput({}), /Bad Request/);
    const input = parseCheckoutInput({ usr: ' User ', eml: 'USER@EXAMPLE.COM', pwd: 'password123', c_id: 2, card: '4000000000000000' });
    assert.strictEqual(input.name, 'User');
    assert.strictEqual(input.email, 'user@example.com');
});

test('password hasher usa salt e não conserva senha em texto', async () => {
    const hasher = new PasswordHasher();
    const first = await hasher.hash('same-password');
    const second = await hasher.hash('same-password');
    assert.notStrictEqual(first, second);
    assert(!first.includes('same-password'));
    assert(first.startsWith('scrypt$'));
});

test('contratos HTTP, autenticação e integridade referencial', () => withApplication(async ({ server, db }) => {
    const anonymousReport = await request(server, 'GET', '/api/admin/financial-report');
    assert.strictEqual(anonymousReport.status, 401);

    const forbiddenReport = await request(server, 'GET', '/api/admin/financial-report', { apiKey: 'wrong-key' });
    assert.strictEqual(forbiddenReport.status, 403);

    const report = await request(server, 'GET', '/api/admin/financial-report', { apiKey: ADMIN_KEY });
    assert.strictEqual(report.status, 200);
    assert.match(report.contentType, /^application\/json/);
    const reportBody = JSON.parse(report.body);
    assert.deepStrictEqual(reportBody[0], { course: 'Clean Architecture', revenue: 997, students: [{ student: 'Leonan', paid: 997 }] });
    assert.deepStrictEqual(reportBody[1], { course: 'Docker', revenue: 0, students: [] });

    const invalidCheckout = await request(server, 'POST', '/api/checkout', { body: {} });
    assert.strictEqual(invalidCheckout.status, 400);
    assert.strictEqual(invalidCheckout.body, 'Bad Request');

    const deniedCheckout = await request(server, 'POST', '/api/checkout', {
        body: { usr: 'Denied', eml: 'denied@example.com', pwd: 'password123', c_id: 1, card: '5000000000000000' }
    });
    assert.strictEqual(deniedCheckout.status, 400);
    assert.strictEqual(deniedCheckout.body, 'Pagamento recusado');

    const checkout = await request(server, 'POST', '/api/checkout', {
        body: { usr: 'Approved', eml: 'approved@example.com', pwd: 'password123', c_id: 2, card: '4000000000000000' }
    });
    assert.strictEqual(checkout.status, 200);
    assert.deepStrictEqual(JSON.parse(checkout.body), { msg: 'Sucesso', enrollment_id: 2 });
    const storedUser = await db.get('SELECT pass FROM users WHERE email = ?', ['approved@example.com']);
    assert(storedUser.pass.startsWith('scrypt$'));

    const deleteResponse = await request(server, 'DELETE', '/api/users/1', { apiKey: ADMIN_KEY });
    assert.strictEqual(deleteResponse.status, 200);
    const orphans = await db.get('SELECT COUNT(*) AS count FROM enrollments WHERE user_id = 1');
    assert.strictEqual(orphans.count, 0);
}));

test('checkout faz rollback integral quando uma etapa falha', () => withApplication(async ({ server, db }) => {
    await db.run("CREATE TRIGGER fail_audit BEFORE INSERT ON audit_logs BEGIN SELECT RAISE(FAIL, 'audit failure'); END");
    const checkout = await request(server, 'POST', '/api/checkout', {
        body: { usr: 'Rollback', eml: 'rollback@example.com', pwd: 'password123', c_id: 2, card: '4000000000000000' }
    });
    assert.strictEqual(checkout.status, 500);
    const user = await db.get('SELECT id FROM users WHERE email = ?', ['rollback@example.com']);
    const enrollments = await db.get('SELECT COUNT(*) AS count FROM enrollments');
    const payments = await db.get('SELECT COUNT(*) AS count FROM payments');
    assert.strictEqual(user, undefined);
    assert.strictEqual(enrollments.count, 1);
    assert.strictEqual(payments.count, 1);
}));

(async () => {
    let failures = 0;
    for (const current of tests) {
        try {
            await current.fn();
            console.log(`PASS ${current.name}`);
        } catch (error) {
            failures += 1;
            console.error(`FAIL ${current.name}`);
            console.error(error.stack);
        }
    }
    if (failures) process.exitCode = 1;
})();
