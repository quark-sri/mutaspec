# Shop requirements

The shop sells products from a fixed catalogue. Agent Mutants point to these rules with `spec_ref` (for example `docs/requirements.md#R3`).

- **R1** A customer can look up a product by id. An unknown id gives 404.
- **R2** An order has one product and a quantity from 1 to 10. Any other quantity gives 400.
- **R3** An order for more items than are in stock gives 409, and the stock does not change.
- **R4** A placed order takes its quantity out of stock.
- **R5** The order total is unit price × quantity, in cents.
- **R6** When the total before discount is 10 000 cents or more, the customer gets 10 % off, rounded down to the cent.
- **R7** A placed order gives 201 with the order id and total. The order can be read back by id; an unknown order id gives 404.
