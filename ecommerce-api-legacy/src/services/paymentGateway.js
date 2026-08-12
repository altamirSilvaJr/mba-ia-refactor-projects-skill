class PaymentGateway {
    charge(card) {
        return card.startsWith('4') ? 'PAID' : 'DENIED';
    }
}

module.exports = PaymentGateway;
