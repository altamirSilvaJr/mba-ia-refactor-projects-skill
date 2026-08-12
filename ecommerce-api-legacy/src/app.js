const express = require('express');
const Database = require('./database/database');
const { initializeDatabase } = require('./database/initialize');
const PasswordHasher = require('./security/passwordHasher');
const UserRepository = require('./repositories/userRepository');
const CourseRepository = require('./repositories/courseRepository');
const EnrollmentRepository = require('./repositories/enrollmentRepository');
const PaymentRepository = require('./repositories/paymentRepository');
const AuditRepository = require('./repositories/auditRepository');
const ReportRepository = require('./repositories/reportRepository');
const PaymentGateway = require('./services/paymentGateway');
const CheckoutService = require('./services/checkoutService');
const FinancialReportService = require('./services/financialReportService');
const DeleteUserService = require('./services/deleteUserService');
const CheckoutController = require('./controllers/checkoutController');
const AdminController = require('./controllers/adminController');
const UserController = require('./controllers/userController');
const { parseCheckoutInput, parseUserId } = require('./validation/checkoutInput');
const { createAdminAuth } = require('./middlewares/adminAuth');
const { errorHandler } = require('./middlewares/errorHandler');
const { buildRoutes } = require('./routes');

async function createApplication(config) {
    const db = new Database(config.databasePath);
    const passwordHasher = new PasswordHasher();
    await initializeDatabase(db, passwordHasher);

    const users = new UserRepository(db);
    const checkoutService = new CheckoutService({
        db,
        users,
        courses: new CourseRepository(db),
        enrollments: new EnrollmentRepository(db),
        payments: new PaymentRepository(db),
        audit: new AuditRepository(db),
        passwordHasher,
        paymentGateway: new PaymentGateway()
    });
    const dependencies = {
        checkoutController: new CheckoutController(checkoutService, parseCheckoutInput),
        adminController: new AdminController(new FinancialReportService(new ReportRepository(db))),
        userController: new UserController(new DeleteUserService(users, db), parseUserId),
        adminAuth: createAdminAuth(config.adminApiKey)
    };

    const app = express();
    app.disable('x-powered-by');
    app.use(express.json());
    app.use(buildRoutes(dependencies));
    app.use(errorHandler);
    return { app, db };
}

module.exports = { createApplication };
