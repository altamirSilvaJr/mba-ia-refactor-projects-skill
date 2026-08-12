const { HttpError } = require('../middlewares/errorHandler');

class CheckoutService {
    constructor(dependencies) { Object.assign(this, dependencies); }

    async execute(input) {
        const course = await this.courses.findActiveById(input.courseId);
        if (!course) throw new HttpError(404, 'Curso não encontrado');

        const paymentStatus = this.paymentGateway.charge(input.card, course.price);
        if (paymentStatus === 'DENIED') throw new HttpError(400, 'Pagamento recusado');

        return this.db.transaction(async () => {
            let user = await this.users.findByEmail(input.email);
            let userId = user && user.id;
            if (!userId) {
                const passwordHash = await this.passwordHasher.hash(input.password);
                userId = await this.users.create(input.name, input.email, passwordHash);
            }
            const enrollmentId = await this.enrollments.create(userId, input.courseId);
            await this.payments.create(enrollmentId, course.price, paymentStatus);
            await this.audit.record(`Checkout curso ${input.courseId} por ${userId}`);
            return { msg: 'Sucesso', enrollment_id: enrollmentId };
        });
    }
}

module.exports = CheckoutService;
