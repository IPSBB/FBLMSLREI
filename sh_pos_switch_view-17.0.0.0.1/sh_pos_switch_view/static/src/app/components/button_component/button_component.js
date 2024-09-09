/** @odoo-module */

import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";

export class ViewModeButtons extends Component {
    static template = "sh_pos_switch_view.button_component";
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.clickedProductListView = false
        this.clickedProductGridView = false
        this.selectedView()

    }
    selectedView(){
        if(this.pos.config.sh_default_view == "grid_view"){
            this.clickedProductGridView = true
            this.clickedProductListView = false
            this.pos.product_view = "grid"
        }
        if(this.pos.config.sh_default_view == "list_view"){
            this.clickedProductGridView = false
            this.clickedProductListView = true
            this.pos.product_view = "list"
        }
        
    }
    onClickProductGridView(){
        if(!this.clickedProductGridView){
            this.clickedProductGridView = true
            this.clickedProductListView = false
        }
        else{
            this.clickedProductGridView = false
        }
        this.pos.product_view = "grid"
        this.render(true)
    }
    onClickProductListView() {
        if(!this.clickedProductListView){
                this.clickedProductGridView = false
                this.clickedProductListView = true
            }
            else{
                this.clickedProductListView = false
            }
            this.pos.product_view = "list"
            this.render(true)
    }
    
}
