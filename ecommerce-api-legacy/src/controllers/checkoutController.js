class CheckoutController {
    constructor(service, parseInput) { this.service = service; this.parseInput = parseInput; }
    execute = async (req, res, next) => {
        try {
            const result = await this.service.execute(this.parseInput(req.body));
            res.status(200).json(result);
        } catch (error) { next(error); }
    };
}

module.exports = CheckoutController;
