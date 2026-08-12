class HttpError extends Error {
    constructor(status, publicMessage) {
        super(publicMessage);
        this.status = status;
        this.publicMessage = publicMessage;
    }
}

function errorHandler(error, req, res, next) {
    if (res.headersSent) return next(error);
    if (error instanceof HttpError) return res.status(error.status).send(error.publicMessage);
    if (error instanceof SyntaxError && error.status === 400 && Object.prototype.hasOwnProperty.call(error, 'body')) {
        return res.status(400).send('Bad Request');
    }
    console.error('Erro não tratado', { method: req.method, path: req.path, message: error.message });
    return res.status(500).send('Erro interno');
}

module.exports = { HttpError, errorHandler };
