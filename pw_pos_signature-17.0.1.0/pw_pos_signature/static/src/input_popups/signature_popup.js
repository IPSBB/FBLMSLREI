/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { useService } from "@web/core/utils/hooks";
import { useAsyncLockedMethod } from "@point_of_sale/app/utils/hooks";
import { parseFloat } from "@web/views/fields/parsers";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component, onWillStart, onMounted, useState } from "@odoo/owl";


export class PwSignaturePopup extends AbstractAwaitablePopup {
    static template = "pw_pos_signature.PwSignaturePopup";
    static defaultProps = {
        cancelText: _t("Cancel"),
        confirmText: _t("Add"),
        title: _t("Add Signature"),
        body: "",
        list: [],
        confirmKey: false,
    };
    setup() {
        super.setup();
        this.notification = useService("pos_notification");
        this.popup = useService("popup");
        this.orm = useService("orm");
        this.pos = usePos();
        this.confirm = useAsyncLockedMethod(this.confirm);
        onMounted(() => {
            setTimeout(() => {
                $(".pw_signature").jSignature({
                    "background-color": "white",
                    "decor-color": "transparent",
                    'width': "75%",
                    'height': '150px',
                });
            }, 500)
        });
    }
    clear() {
        $("#pw_signature").jSignature("reset");
    }
    async confirm() {
        var order = this.pos.get_order();
        if ($("#pw_signature").jSignature("getData", "native").length > 0) {
            var value = $("#pw_signature").jSignature("getData", "image");
            order.pw_signature = value;
        }
        super.confirm();
    }
}
