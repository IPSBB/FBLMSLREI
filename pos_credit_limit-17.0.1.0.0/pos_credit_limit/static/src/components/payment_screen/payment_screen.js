/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { useService } from "@web/core/utils/hooks";
/**
 * Override of PaymentScreen to check the payment method and credit limit of the customer.
 */
patch(PaymentScreen.prototype,{
    setup() {
       super.setup();
       this.numberBuffer = useService("number_buffer");
    },
    /**
     * Checks the payment method and credit limit/warning limit of the selected customer.
     *
     * @param {Object} paymentMethod
     */
    addNewPaymentLine(paymentMethod) {
        var self = this;
        var current_order = this.currentOrder;
        var paymentContinue = true
        if (paymentMethod.type == 'pay_later') {
            if (!current_order.partner){
                paymentContinue = false
                self.select_customer(self);
                return false;
            }
            else{
                if (current_order.partner.use_partner_credit_limit) {
                    if(current_order.partner.credit > current_order.partner.blocking_credit_limit && current_order.partner.blocking_credit_limit != 0){
                        paymentContinue = false
                        this.env.services.popup.add(ErrorPopup,{
                            title: _t("Exceeded Credit Limit"),
                            body: _t("Sorry you have exceeded your Credit Limit , Please use another Payment Method or Contact Manager ")
                        });
                        return false;
                    }
                }
            }
        }
        if (paymentContinue) {
            self.changePaymentLine(self, paymentMethod);
        }
    },
    /**
     * Checks if any electronic payment is in progress.
     *
     * @async
     * @param {Object} self
     * @param {Object} paymentMethod
     */
    async changePaymentLine (self, paymentMethod) {
        if (self.currentOrder.electronic_payment_in_progress()) {
            self.popup.add(ErrorPopup,{
                title: _t('Error'),
                body: _t('There is already an electronic payment in progress.')
            });
            return false;
        }
        else {
            self.currentOrder.add_paymentline(paymentMethod);
            this.numberBuffer.reset();
            self.payment_interface = paymentMethod.payment_terminal;
            if (self.payment_interface) {
                self.currentOrder.selected_paymentline.set_payment_status('pending');
            }
            return true;
        }
    },
    /**
     * Checks if the empty order is  valid or not.
     */
    _isValidEmptyOrder() {
        const order = this.currentOrder;
        if (order.get_orderlines().length == 0) {
            return order.get_paymentlines().length != 0;
        } else {
            return true;
        }
    },
    /**
     * Checks if the customer selected while payment or not.
     *
     * @async
     * @param {Object} self
     */
    async select_customer (self) {
        const { confirmed } = await this.popup.add(ConfirmPopup, {
            title: _t('Please select the Customer'),
            body: _t('You need to select a customer for using this Payment Method.')
        });
        if (confirmed) {
            this.selectPartner();
        }
    },
    /**
     * Checks if the current order is valid or not. If the order is valid then it checks the warning limit/credit limit of the customner.
     *
     * @async
     * @param {boolean} isForceValidate
     */
    async _isOrderValid(isForceValidate) {
        var self = this;
        var order = this.pos.get_order();
        if (this.currentOrder.get_orderlines().length === 0 && this.currentOrder.is_to_invoice()) {
            this.popup.add(ErrorPopup, {
                title: _t('Empty Order'),
                body: _t('There must be at least one product in your order before it can be validated and invoiced.')
            });
            return false;
        }
        const splitPayments = this.paymentLines.filter(payment => payment.payment_method.split_transactions)
        if (splitPayments.length && !this.currentOrder.get_partner()) {
            const paymentMethod = splitPayments[0].payment_method
            const { confirmed } = await this.popup.add(ConfirmPopup, {
                title: _t('Customer Required'),
                body: _.str.sprintf(_t('Customer is required for %s payment method.'), paymentMethod.name)
            });
            if (confirmed) {
                this.selectPartner();
            }
            return false;
        }
        if ((this.currentOrder.is_to_invoice() || this.currentOrder.getShippingDate()) && !this.currentOrder.get_partner()) {
            const { confirmed } = await this.popup.add(ConfirmPopup, {
                title: _t('Please select the Customer'),
                body: _t('You need to select the customer before you can invoice or ship an order.')
            });
            if (confirmed) {
               this.selectPartner();
            }
            return false;
        }
        for(var i=0;i < order.paymentlines.length;i++){
            if (order.paymentlines[i].payment_method.type == 'pay_later') {
                if (order.partner.partner_block_credit){
                    var temp_credit = order.partner.credit;
                    temp_credit += order.paymentlines[i].amount;
                    if(temp_credit >= order.partner.blocking_credit_limit && order.partner.blocking_credit_limit != 0){
                        this.popup.add(ErrorPopup,{
                            title: _t("Exceeding Credit Limit"),
                            body: _t(['Sorry, the allowed credit will reach its limit. \nAllowed Credit Limit is' +order.partner.blocking_credit_limit+' . ',
                                        '\nYour current credit is '+order.partner.credit+' . ',
                                        'Please pay using a different Payment Method or Contact manager'].join(' '))
                            });
                        return false;
                        }
                    else if(temp_credit >= order.partner.credit_limit){
                        order.partner.credit = temp_credit;
                            await this.popup.add(ErrorPopup,{
                                title: _t("Warning Limit Reminder"),
                                body: _t(['The credit has exceeded the sales credit limit. \nYour limit is ' +order.partner.credit_limit+' and maximum allowed limit is '+order.partner.blocking_credit_limit+'.',
                                          'Your current credit is '+order.partner.credit].join(' '))
                                });
                            return true
                        }
                    else {
                        order.partner.credit = temp_credit;
                    }
                }
            }
        }
        var customer = this.currentOrder.get_partner()
        if (this.currentOrder.getShippingDate() && !(customer.name && customer.street && customer.city && customer.country_id)) {
            this.popup.add(ErrorPopup, {
                title: _t('Incorrect address for shipping'),
                body: _t('The selected customer needs an address.')
            });
            return false;
        }
        if (!this.currentOrder.is_paid() || this.invoicing) {
            return false;
        }
        if (this.currentOrder.has_not_valid_rounding()) {
            var line = this.currentOrder.has_not_valid_rounding();
            this.popup.add(ErrorPopup, {
                title: _t('Incorrect rounding'),
                body: _t('You have to round your payments lines.' + line.amount + ' is not rounded.')
            });
            return false;
        }
        // The exact amount must be paid if there is no cash payment method defined.
        if (
            Math.abs(
                this.currentOrder.get_total_with_tax() - this.currentOrder.get_total_paid()  + this.currentOrder.get_rounding_applied()
            ) > 0.00001
        ) {
            var cash = false;
            for (var i = 0; i < this.pos.payment_methods.length; i++) {
                cash = cash || this.pos.payment_methods[i].is_cash_count;
            }
            if (!cash) {
                this.popup.add(ErrorPopup, {
                    title: _t('Cannot return change without a cash payment method'),
                    body: _t('There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration')
                });
                return false;
            }
        }
        // if the change is too large, it's probably an input error, make the user confirm.
        if (
            !isForceValidate &&
            this.currentOrder.get_total_with_tax() > 0 &&
            this.currentOrder.get_total_with_tax() * 1000 < this.currentOrder.get_total_paid()
        ) {
            this.popup.add(ConfirmPopup, {
                title: _t('Please Confirm Large Amount'),
                body:
                    _t('Are you sure that the customer wants to  pay') + ' ' +
                    this.pos.format_currency(this.currentOrder.get_total_paid()) + ' ' +
                    _t('for an order of') + ' ' +
                    this.pos.format_currency(this.currentOrder.get_total_with_tax()) + ' ' +
                    _t('? Clicking "Confirm" will validate the payment.')
            }).then(({ confirmed }) => {
                if (confirmed) {
                    this.validateOrder(true);
                }
            });
            return false;
        }
        if (!this._isValidEmptyOrder()){
            return false;
        }
        return true;
    }
});
