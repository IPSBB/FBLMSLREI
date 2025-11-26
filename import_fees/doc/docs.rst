.. |company| image:: icon-withtext.png
   :width: 5em
   :alt: Odoo Skillz


|company|





Setup
----------------


`1. HS Codes setup (added by this module)`


This allows you to input various import rates and taxes. The feature is available in Inventory &gt; Configuration &gt; HS CodesTo enable customs duties calculation, the newHarmonized Code field should be defined either on Product or on Product Category hierarchy
   
      
      .. image:: hs-code-list.png
         :alt: Harmonized codes list
         :align: center
         :class: img-fluid
      Harmonized codes list
   

`2. Related setup in standard Odoo Inventory Module`


For Landed Costs valuation to function properly, Product Categories need to have a Costing Method set on Average costs or FIFOFor foreign currencies to be enabled in Odoo, you need to enable it in Settings &gt; Invoicing &gt; Currencies Section &gt; Multi Currencies 
   
      






Feature Overview
----------------


`Customs duties calculation, to save you time`




No need for tedious Excel Sheet formulas and macros, customs duties are calculated for each HS (Harmonized System) Code



.. image:: heart.jpg
   :alt: Customs duties automated calculation
   :align: center
   :class: img-fluid
   
Customs duties automated calculation


`Seamless Customs Duties Integration into Landed Costs`




Attach Vendor Bills, Customs Broker Bills to Landed Costs, and the tool will split the customs duties, so you can be sure that you're always getting the right numbers.



.. image:: two-way.png
   :alt: Bring customs duties into Landed Costs
   :align: center
   :class: img-fluid
   
Bring customs duties into Landed Costs


`Tariffs Rates by Country or Region`




Got different rates for different countries? No problem! Our tool allows you to set up different rates for each country or region seamlessly.



.. image:: hsperregion.png
   :alt: Customs duties and taxes by country or region with the same HS Code
   :align: center
   :class: img-fluid
   
Customs duties and taxes by country or region with the same HS Code












Feature Matrix
----------------

.. csv-table::
   :header: "Feature / Odoo Version","v13","v14","v15","v16","v17","v18"
   :widths: 60,10,10,10,10,10,10
   :class: table table-bordered table-striped

    "Split Customs Duties from Customs Bills in Landed Costs","N/A","N/A","N/A","N/A","✔️","✔️"
    "HS Codes definition per Product or Product Category","✔️","✔️","✔️","✔️","✔️","✔️"
    "HS Codes rates by country or region","N/A","N/A","N/A","N/A","✔️","✔️"
    "Customs Duties calculation","✔️","✔️","✔️","✔️","✔️","✔️"
    "CIF value calculation","✔️","✔️","✔️","✔️","✔️","✔️"
    "Manual CIF value update for each HS Code","✔️","✔️","✔️","✔️","✔️","✔️"
    "Preview all transfered products in Landed Costs","✔️","✔️","✔️","✔️","✔️","✔️"
    "Customs & Shipping Bills Generation from Landed Costs","✔️","✔️","✔️","✔️","✔️","✔️"
    "Customizable Duties Fields (in Odoo Configuration)","N/A","N/A","N/A","N/A","✔️","✔️"
    "Editable Customs Duties amounts per HS Code in Landed Costs (sometimes required to match customs bills)","✔️","N/A","N/A","N/A","✔️","✔️"
    "Multiple vendor Bills per Landed Cost (with multiple currencies support)","N/A","N/A","N/A","N/A","✔️","✔️"
    "Multi-company support : HS Codes configuration for Products and Categpries per company","N/A","N/A","N/A","N/A","✔️","✔️"
    "Configuration option : Add 10% CIF in VAT, CESS LEVY and SSCL","N/A","N/A","N/A","N/A","✔️","✔️"
   



|company|

`www.odooskillz.com <https://www.odooskillz.com>`_