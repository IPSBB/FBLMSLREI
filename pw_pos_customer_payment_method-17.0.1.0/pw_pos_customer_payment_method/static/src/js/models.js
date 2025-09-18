/** @odoo-module **/

import { Order } from "@point_of_sale/app/store/models";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

patch(Order.prototype, {
    add_paymentline(payment_method) {
        let customer = this.get_partner();
        if (this.pos.config.pw_restrict_pm && customer && customer.pw_pos_payment_ids.length > 0 && !customer.pw_pos_payment_ids.includes(payment_method.id)) {
            this.pos.env.services.popup.add(ErrorPopup, {
                title: _t("Payment Method Required"),
                body: _t("Please select payment method"),
            });
            return;
        }
        return super.add_paymentline(payment_method);
    },
    set_partner(partner) {
        super.set_partner(partner);
        var order = this.pos.get_order();
        if (order && !order.finalized) {
            var paymentLines = order.get_paymentlines();
            if (paymentLines.length != 0) {
                paymentLines.forEach(function (line) {
                    order.remove_paymentline(line);
                });
            }
        }
    }
});
