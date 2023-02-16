# Cardano WalletRank

Google uses the Page-Rank graph algorithm to measure the importance of web pages. This works by giving a "vote of
confidence" when pages that are highly trusted link to your page, which then passes on some of that trust to your
page. All the information and procedures for PageRank can be found publicly.

## PageRank Algorithm
- Initialize every node with a value of 1
- For each iteration, update value of every node in the graph
- The new PageRank is the sum of the proportional rank of all of its parents
- Apply random walk to the new PageRank
- PageRank value will converge after enough iterations

### Modeled Signals

On a high level, PageRank can only model the transaction direction. E.g. Alice sends money to Bob. Modeling the
amount sent to Bob is beyond the scope at the moment, and is not modeled.

### Not Modeled Signals
PageRank is simpler than what WalletRank could & should model in hopes of fraud detection. For example:

- PageRank's links do not have a "quantity" associated, but a transaction does. E.g. Alice sends 20 ADA to Bob.
- PageRank's links do not have a "time" unit, nor how "often", but transactions do.
  - PageRank does not consider how old the links are. E.g. The newer transactions may be more useful in catching
    on-going fraud.
  - Nor consider how frequent the transactions occur. E.g. Alice sends Bob a recurring transaction each week.
- PageRank's links do not interact with smart-contracts. E.g. There exists smart contracts out there such as Tornado
  Cash, which can be maliciously used for money laundering. At a high level, they work by pooling the funds
  deposited by many users together, shuffling them in a seemingly random fashion, and then subtracting a small
  service fee and returning the remaining funds to each depositor.
  https://blog.chainalysis.com/reports/tornado-cash-sanctions-challenges/

# Cardano Ecosystem
Cardano uses the unspent transaction output (UTXO) model, refers to a transaction output that can be
used as input where each blockchain transaction starts and finishes.

In short, Cardano has four different types of addresses:

- Base (stake) addresses. A wallet is a collection of UTXOs.
- Pointer addresses. These are used in transactions, controlled by a single staking address.
- Enterprise addresses. These are addresses that do not carry staking rights.
- Reward account addresses. Also controlled by the base (stake) address.

A block represents a fixed time interval. The average block time on Cardano is ~20 seconds, though this is fluid and
can change with time depending on various factors. A block contains many transaction.


# How can the Cardano transaction schema be mapped to the PageRank algorithm?

The blockchain data on Cardano is parsed and inserted to Postgres server.

## Cardano DB Sync

Cardano DB Sync is program that follows the Cardano chain and takes information from the chain and an internally
maintained copy of ledger state an inserts that data into a PostgreSQL database. SQL (structured query language)
queries can then be written directly against the database schema or as queries embedded in any language with
libraries for interacting with an SQL database.

The database provided and maintained by cardano-db-sync allows anybody with some SQL expertise to extract
information about the Cardano chain (including some data that is not on the chain but rather is part of ledger state)
. This information includes things like

- The transactions in a specific block (from the chain).
- The balance of a specific address (from the chain).
- The staking rewards earned by a pool or address for a specific epoch (from ledger state).

The SQL equivalent schema is at https://github.com/input-output-hk/cardano-db-sync/blob/master/doc/schema.md

For sake of simplicity, only the tables related to transactions `tx` is used here.

### Database size
To connect: `psql postgres://cardano:qwe123@mini.ds:5432/dbsync`


It is approx 400GB up until Epoch 384. As of Feb 15, 2023, it is Epoch 394.

```
dbsync=# select id, epoch_no, epoch_slot_no,block_no from block order by id desc limit 1;
    id    | epoch_no | epoch_slot_no | block_no
----------+----------+---------------+----------
 16301161 |      384 |        264955 |  8203499
(1 row)
```

A cardano transaction can have multiple inputs and multiple outputs. In the same way that the multiple outputs can
go to different addresses, the multiple inputs can come from different addresses too. As long as the transaction is
signed by all the private keys of all the input addresses, the transaction is valid.

Also, a single wallet can have multiple derived addresses. So what you are seeing as multiple senders might actually
be the same sender. You can confirm this by checking whether the staking_address_id values of all the sender
addresses are the same.

### The structure of `tx` table

A table for transactions within a block on the chain. 57,791,426 rows.

* Primary Id: `id`

| Column            | Type       | Nullable | Description                                                                               |
|:------------------|:-----------|:---------|:------------------------------------------------------------------------------------------|
| id                | bigint     | not null |                                                                                           |
| hash              | hash32type | not null | The hash identifier of the transaction.                                                   |
| block_id          | bigint     | not null | The Block table index of the block that contains this transaction.                        |
| block_index       | word31type | not null | The index of this transaction with the block (zero based).                                |
| out_sum           | lovelace   | not null | The sum of the transaction outputs (in Lovelace).                                         |
| fee               | lovelace   | not null | The fees paid for this transaction.                                                       |
| deposit           | bigint     | not null | Deposit (or deposit refund) in this transaction. Deposits are positive, refunds negative. |
| size              | word31type | not null | The size of the transaction in bytes.                                                     |
| invalid_before    | word64type |          | Transaction in invalid before this slot number.                                           |
| invalid_hereafter | word64type |          | Transaction in invalid at or after this slot number.                                      |
| valid_contract    | boolean    | not null | False if the contract is invalid. True if the contract is valid or there is no contract.  |
| script_size       | word31type | not null | The sum of the script sizes (in bytes) of scripts in the transaction.                     |


### The structure of `tx_in` table

A table for transaction inputs. 147,114,212 rows.

* Primary Id: `id`

| Column name    | Type         | Nullable | Description                                                                            |
|:---------------|:-------------|:---------|:---------------------------------------------------------------------------------------|
| `id`           | integer (64) | not null |                                                                                        |
| `tx_in_id`     | integer (64) | not null | The Tx table index of the transaction that contains this transaction input.            |
| `tx_out_id`    | integer (64) | not null | The Tx table index of the transaction that contains the referenced transaction output. |
| `tx_out_index` | txindex      | not null | The index within the transaction outputs.                                              |
| `redeemer_id`  | integer (64) |          | The Redeemer table index which is used to validate this input.                         |


### The structure of `tx_out` table

A table for transaction outputs. 156,647,847 rows.

* Primary Id: `id`

| Column name           | Type         | Nullable | Description                                                                                                                           |
|:----------------------|:-------------|:---------|:--------------------------------------------------------------------------------------------------------------------------------------|
| `id`                  | integer (64) | not null |                                                                                                                                       |
| `tx_id`               | integer (64) | not null | The Tx table index of the transaction that contains this transaction output.                                                          |
| `index`               | txindex      | not null | The index of this transaction output with the transaction.                                                                            |
| `address`             | string       | not null | The human readable encoding of the output address. Will be Base58 for Byron era addresses and Bech32 for Shelley era.                 |
| `address_raw`         | blob         | not null | The raw binary address.                                                                                                               |
| `address_has_script`  | boolean      | not null | Flag which shows if this address is locked by a script.                                                                               |
| `payment_cred`        | hash28type   |          | The payment credential part of the Shelley address. (NULL for Byron addresses). For a script-locked address, this is the script hash. |
| `stake_address_id`    | integer (64) |          | The StakeAddress table index for the stake address part of the Shelley address. (NULL for Byron addresses).                           |
| `value`               | lovelace     | not null | The output value (in Lovelace) of the transaction output.                                                                             |
| `data_hash`           | hash32type   |          | The hash of the transaction output datum. (NULL for Txs without scripts).                                                             |
| `inline_datum_id`     | integer (64) |          | The inline datum of the output, if it has one. New in v13.                                                                            |
| `reference_script_id` | integer (64) |          | The reference script of the output, if it has one. New in v13.                                                                        |


### Creating a view

What we care about are, given the scope of our problem described in the [Modeled Signal section](#modeled-signals):

- Who is Alice? Namely, the `stake_address_id` of the `tx_in`.
- Who is Bob? The `stake_address_id` of the `tx_out`.

In Cardano, "stake key" can be thought of as a wallet. Since `stake_address_id` uniquely maps to a stake key, it
suffices to just build a table `stake_address_id`. If we need the actual stake address, it is one lookup away.

The reason we build this table is to speed up the queries so that joins are performed by the database itself, rather
than pulling data to code and doing joins ourselves, saving the network bandwidth.

Let's look at the most recent transactions.
Taking a look at the transactions.
```
dbsync=# select id from tx order by id desc limit 1 offset 2;
    id
-----------
 114221813
(1 row)
```

Build a table with this

```sql
SELECT prev_tx_out.stake_address_id sender ,
       this_tx_out.stake_address_id receiver ,
       this_tx_out.value amount
FROM tx this_tx
INNER JOIN tx_out this_tx_out ON this_tx_out.tx_id = this_tx.id
INNER JOIN tx_in this_tx_in ON this_tx_in.tx_in_id = this_tx.id
INNER JOIN tx_out prev_tx_out ON prev_tx_out.tx_id = this_tx_in.tx_out_id
AND prev_tx_out.index = this_tx_in.tx_out_index
WHERE this_tx.id > 114221813;
```

This outputs

|  sender  | receiver |  amount   |
|----------|----------|-----------|
| 10751507 |  8765948 |   1344720|
|  8765948 |  8765948 |   1344720|
| 10751507 | 10751507 | 246589963|
|  8765948 | 10751507 | 246589963|
| 10751507 | 10751507 | 123294982|
|  8765948 | 10751507 | 123294982|
| 10751507 | 10751507 | 122963166|
|  8765948 | 10751507 | 122963166|
|  8765948 | 10335905 |   3675000|
| 10167344 | 10335905 |   3675000|
|  8765948 |  8665866 |   2100000|
| 10167344 |  8665866 |   2100000|
|  8765948 | 10693011 |  99225000|
| 10167344 | 10693011 |  99225000|
|  8765948 | 10167344 |   1168010|
| 10167344 | 10167344 |   1168010|
|  8765948 | 10167344 | 698382565|
| 10167344 | 10167344 | 698382565|
|  8765948 | 10167344 | 349191283|
| 10167344 | 10167344 | 349191283|
|  8765948 | 10167344 | 174595641|
| 10167344 | 10167344 | 174595641|
|  8765948 | 10167344 | 174157719|
| 10167344 | 10167344 | 174157719|

### Postgres feature: Material View

Materialized views cache the fetched data. The use cases for using materialized views are when
the underlying query takes a long time and when having timely data is not critical. You often encounter these
scenarios when building online analytical processing (OLAP) applications. Material view differs from a regular
View in that you can add indexes to materialized views to speed up the read.

What we need is in 3 tables and only some columns are useful. We can build a material view table, so the database
can help out in preparing the data we need for building the WalletRank graph.

```sql
CREATE MATERIALIZED VIEW sender_reciver_amount AS
SELECT prev_tx_out.stake_address_id sender ,
       this_tx_out.stake_address_id receiver ,
       this_tx_out.value amount
FROM tx this_tx
INNER JOIN tx_out this_tx_out ON this_tx_out.tx_id = this_tx.id
INNER JOIN tx_in this_tx_in ON this_tx_in.tx_in_id = this_tx.id
INNER JOIN tx_out prev_tx_out ON prev_tx_out.tx_id = this_tx_in.tx_out_id
AND prev_tx_out.index = this_tx_in.tx_out_index
WHERE this_tx.id > 114221813;
```

Double check we have the view

```
dbsync=# select * from sender_reciver_amount;
  sender  | receiver |  amount
----------+----------+-----------
 10751507 |  8765948 |   1344720
  8765948 |  8765948 |   1344720
 10751507 | 10751507 | 246589963
  8765948 | 10751507 | 246589963
 10751507 | 10751507 | 123294982
  8765948 | 10751507 | 123294982
 10751507 | 10751507 | 122963166
  8765948 | 10751507 | 122963166
  8765948 | 10335905 |   3675000
 10167344 | 10335905 |   3675000
  8765948 |  8665866 |   2100000
 10167344 |  8665866 |   2100000
  8765948 | 10693011 |  99225000
 10167344 | 10693011 |  99225000
  8765948 | 10167344 |   1168010
 10167344 | 10167344 |   1168010
  8765948 | 10167344 | 698382565
 10167344 | 10167344 | 698382565
  8765948 | 10167344 | 349191283
 10167344 | 10167344 | 349191283
  8765948 | 10167344 | 174595641
 10167344 | 10167344 | 174595641
  8765948 | 10167344 | 174157719
 10167344 | 10167344 | 174157719
```

### Prepare a material view for the last 1M entries.

```
dbsync=# select id from tx order by id desc limit 1 offset 10000000;
    id
-----------
 103167513
(1 row)

Time: 18300.319 ms (00:18.300)
```

```
dbsync=# CREATE MATERIALIZED VIEW sender_reciver_amount AS
SELECT prev_tx_out.stake_address_id sender ,
       this_tx_out.stake_address_id receiver ,
       this_tx_out.value amount
FROM tx this_tx
INNER JOIN tx_out this_tx_out ON this_tx_out.tx_id = this_tx.id
INNER JOIN tx_in this_tx_in ON this_tx_in.tx_in_id = this_tx.id
INNER JOIN tx_out prev_tx_out ON prev_tx_out.tx_id = this_tx_in.tx_out_id
AND prev_tx_out.index = this_tx_in.tx_out_index
WHERE this_tx.id > 103167513;
SELECT 169393154
Time: 510572.550 ms (08:30.573)
```
