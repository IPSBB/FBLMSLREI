/** @odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { useService } from "@web/core/utils/hooks";

export class BiWarningBlockingPopup extends AbstractAwaitablePopup {
    static template = "bi_credit_limit_on_pos.BiWarningBlockingPopup";

    setup() {
        super.setup();
        this.pos = usePos();
    } 
}
