/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { PwSignaturePopup } from "@pw_pos_signature/input_popups/signature_popup";

patch(PaymentScreen.prototype, {
    async addSignature() {
        this.popup.add(PwSignaturePopup);
    }
});
