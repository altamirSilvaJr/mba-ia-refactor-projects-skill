const express = require('express');

function buildRoutes({ checkoutController, adminController, userController, adminAuth }) {
    const router = express.Router();
    router.post('/api/checkout', checkoutController.execute);
    router.get('/api/admin/financial-report', adminAuth, adminController.financialReport);
    router.delete('/api/users/:id', adminAuth, userController.delete);
    return router;
}

module.exports = { buildRoutes };
