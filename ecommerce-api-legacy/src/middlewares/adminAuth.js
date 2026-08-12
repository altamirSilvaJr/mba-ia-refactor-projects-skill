const crypto = require('crypto');

function safeEqual(left, right) {
    const leftBuffer = Buffer.from(left || '');
    const rightBuffer = Buffer.from(right || '');
    return leftBuffer.length === rightBuffer.length && crypto.timingSafeEqual(leftBuffer, rightBuffer);
}

function createAdminAuth(expectedKey) {
    return (req, res, next) => {
        const bearer = req.get('authorization');
        const suppliedKey = req.get('x-api-key') || (bearer && bearer.startsWith('Bearer ') ? bearer.slice(7) : '');
        if (!suppliedKey) return res.status(401).send('Não autenticado');
        if (!safeEqual(suppliedKey, expectedKey)) return res.status(403).send('Não autorizado');
        next();
    };
}

module.exports = { createAdminAuth };
