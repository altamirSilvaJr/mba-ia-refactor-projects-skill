class UserController {
    constructor(service, parseId) { this.service = service; this.parseId = parseId; }
    delete = async (req, res, next) => {
        try {
            await this.service.execute(this.parseId(req.params.id));
            res.send('Usuário deletado.');
        } catch (error) { next(error); }
    };
}

module.exports = UserController;
