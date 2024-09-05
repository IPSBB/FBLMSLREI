/** @odoo-module **/


import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    set_signature(signature) {
        this.pw_signature = set_signature;
    },
    get_signature() {
        return this.pw_signature || false;
    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        if (this.pos.config.pw_enable_signature) {
            json.pw_signature = this.get_signature();
        }
        return json;
    },
    export_for_printing() {
        var receipt = super.export_for_printing(...arguments);
        if (this.pos.config.pw_enable_signature && this.pos.config.pw_print_signature) {
            receipt['pw_signature'] = this.get_signature();
        }
        return receipt;
    }
});
