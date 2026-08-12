class AdminController {
    constructor(service) { this.service = service; }
    financialReport = async (req, res, next) => {
        try { res.json(await this.service.execute()); }
        catch (error) { next(error); }
    };
}

module.exports = AdminController;
