const { HttpError } = require('../middlewares/errorHandler');

function parseCheckoutInput(body) {
    const input = body || {};
    if (typeof input.usr !== 'string' || !input.usr.trim() ||
        typeof input.eml !== 'string' || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(input.eml) ||
        typeof input.pwd !== 'string' || input.pwd.length < 8 ||
        !Number.isInteger(input.c_id) || input.c_id < 1 ||
        typeof input.card !== 'string' || !/^\d{12,19}$/.test(input.card)) {
        throw new HttpError(400, 'Bad Request');
    }

    return {
        name: input.usr.trim(),
        email: input.eml.trim().toLowerCase(),
        password: input.pwd,
        courseId: input.c_id,
        card: input.card
    };
}

function parseUserId(value) {
    if (!/^\d+$/.test(value) || Number(value) < 1) throw new HttpError(400, 'Bad Request');
    return Number(value);
}

module.exports = { parseCheckoutInput, parseUserId };
