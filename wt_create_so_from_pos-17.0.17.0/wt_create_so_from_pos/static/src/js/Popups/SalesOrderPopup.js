/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _lt } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class SalesOrderPopup extends AbstractAwaitablePopup {
    static template = "wt_create_so_from_pos.SalesSelectionPopup";
    static defaultProps = {
        cancelText: _lt("Cancel"),
        title: _lt("Select"),
        body: "",
        list: [],
        confirmKey: false,
    };
    setup() {
        super.setup();
        this.state = useState({ selectedId: this.props.list.find((item) => item.isSelected) });
    }
    selectItem(itemId) {
        this.state.selectedId = itemId;
        this.confirm();
    }
    getPayload() {
        const selected = this.props.list.find((item) => this.state.selectedId === item.id);
        return selected && selected.item;
    }
}
