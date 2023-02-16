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


# Data Preparation

What we care about are, given the scope of our problem described in the [Modeled Signal section](#modeled-signals):

- What is the sender's address?
- Who is the receiver?
- What amount?

In Cardano, "stake key" can be thought of as a wallet. Since `address` can uniquely map to a stake key, it may
be enough to just build a table `stake_address_id`. However, `stake_address_id` may be `NULL`, which means that
transaction some transactions would have null sender and/or receiver.

Each Cardano address can be transformed into a stake key, which represents a wallet. Wallets have many addresses,
adding to a layer of indirection. An intermediate table is needed, for


### Creating a material view (Postgres feature)

Materialized views cache the fetched data. The use cases for using materialized views are when
the underlying query takes a long time and when having timely data is not critical. You often encounter these
scenarios when building online analytical processing (OLAP) applications. Material view differs from a regular
View in that you can add indexes to materialized views to speed up the read.

The reason we build a material view table is to cache the results for this complex join that is performed by the
database itself, rather than pulling data to code and doing joins ourselves, saving the network bandwidth.

For sake of limiting scope, let's look at Taking a look at the last 1M transactions.


### Prepare a material view for the last 1M entries.

```
dbsync=# select id from tx order by id desc limit 1 offset 10000000;
    id
-----------
 103167513
(1 row)

Time: 18300.319 ms (00:18.300)
```

What we need is in 3 tables and only some columns are useful. We can build a material view table, so the database
can help out in preparing the data we need for building the WalletRank graph.

```
dbsync=# CREATE MATERIALIZED VIEW sender_reciver_amount_id AS
SELECT prev_tx_out.address  sender ,
       this_tx_out.address  receiver ,
       this_tx_out.value    amount,
       this_tx.id           tx_id
FROM tx this_tx
INNER JOIN tx_out this_tx_out ON this_tx_out.tx_id = this_tx.id
INNER JOIN tx_in this_tx_in ON this_tx_in.tx_in_id = this_tx.id
INNER JOIN tx_out prev_tx_out ON prev_tx_out.tx_id = this_tx_in.tx_out_id
AND prev_tx_out.index = this_tx_in.tx_out_index
WHERE this_tx.id > 103167513;
SELECT 169393154
Time: 970864.750 ms (16:10.865)

```

Here's 10 results from this material view

### Material View Table `sender_reciver_amount_id`

This table is 33GB. It will not fit in memory.

| Schema | Name                     | Type              | Owner   | Persistence | Access method | Size  | Description |
|:-------|:-------------------------|:------------------|:--------|:------------|:--------------|:------|:------------|
| public | sender_reciver_amount_id | materialized view | cardano | permanent   | heap          | 33 GB |             |


|                                                 sender                                                  |                                                receiver                                                 |   amount    |   tx_id   |
|---------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|-------------|-----------|
| addr1qy9yrva9vnxjd09vvnr7v8z7qzr73vyyd40qhnhz98yk9aq3wj76wr3m5njwkezqp2qzed6cgy40q3ax3yxddm29ygcqez2pvl | addr1qy9yrva9vnxjd09vvnr7v8z7qzr73vyyd40qhnhz98yk9aq3wj76wr3m5njwkezqp2qzed6cgy40q3ax3yxddm29ygcqez2pvl |   280113718 | 106066808|
| addr1qxlhz4d0vcmut378mu56zgzng4wm8xj4dqjahdvxn6tzk3mj58v9gz4wrerzqvm0v5xvcygl0unpe2ndw4yuy679nz3qv7hv3f | addr1wxn9efv2f6w82hagxqtn62ju4m293tqvw0uhmdl64ch8uwc0h43gt                                              |    22265944 | 109537649|
| addr1qxlhz4d0vcmut378mu56zgzng4wm8xj4dqjahdvxn6tzk3mj58v9gz4wrerzqvm0v5xvcygl0unpe2ndw4yuy679nz3qv7hv3f | addr1qxlhz4d0vcmut378mu56zgzng4wm8xj4dqjahdvxn6tzk3mj58v9gz4wrerzqvm0v5xvcygl0unpe2ndw4yuy679nz3qv7hv3f |     1150770 | 109537649|
| addr1qxlhz4d0vcmut378mu56zgzng4wm8xj4dqjahdvxn6tzk3mj58v9gz4wrerzqvm0v5xvcygl0unpe2ndw4yuy679nz3qv7hv3f | addr1qyylzh9428hzu2rlsuv50hntjm8qw6s3may0a2fcsd8demmj58v9gz4wrerzqvm0v5xvcygl0unpe2ndw4yuy679nz3q9j4umr | 13884036547 | 109537649|
| addr1q8k8fauns9syu05xc0n0rtaa6sj2cl6kwlpcx2jvvjdz4j5cell99ey8lzj65ne7m8pvvr2cuswkkflal02agavlwxdsmq45n8 | addr1qx3jt2ddwkcwccku7e7nfmmmd0d5sguy3cdjnv6m7zf03p2hf6gsq5ye5wgu25kyrwlggl523ff6qtf3u2skntuwryeqj5f5xp |     1232660 | 109878818|
| addr1q8k8fauns9syu05xc0n0rtaa6sj2cl6kwlpcx2jvvjdz4j5cell99ey8lzj65ne7m8pvvr2cuswkkflal02agavlwxdsmq45n8 | addr1q8m97lg7rrnk6cl6rh2lzpw5dfyx5vf98f4kpek547yg6lvcell99ey8lzj65ne7m8pvvr2cuswkkflal02agavlwxdsxwfjuy |    50801581 | 109878818|
| addr1q84fpuye5x98qh423fc5sg5nwx6zg3qrll6d9kr5kz47g249e23557mnyl44zshd4k6hx5plt867c9lt5ehcz85rlaxsqxtsrd | addr1q84fpuye5x98qh423fc5sg5nwx6zg3qrll6d9kr5kz47g249e23557mnyl44zshd4k6hx5plt867c9lt5ehcz85rlaxsqxtsrd |     1379280 | 103705810|
| addr1qy6pk28tku9un33mr9frhzswl3smh5mq574tvvh9fla4uqlk7clayad5pu8ync9q6kngp5y5mwmul7zwzmzp48lnvm0q0xpe50 | addr1q8hw32qj56pz9k4pmrzqvlvm26zdj6udxltyxh4nq45sgrj04y59cvptj4a0qvemzz52n36jl33fwv4sk4vj60qu5wesldascj |     1344798 | 104998886|
| addr1qy6pk28tku9un33mr9frhzswl3smh5mq574tvvh9fla4uqlk7clayad5pu8ync9q6kngp5y5mwmul7zwzmzp48lnvm0q0xpe50 | addr1qx7zqkf4aapmdh6js3xe3c6k2mnfpfj69crf2rpg2du26s0k7clayad5pu8ync9q6kngp5y5mwmul7zwzmzp48lnvm0q7qzata |   103120160 | 104998886|
| addr1qy6pk28tku9un33mr9frhzswl3smh5mq574tvvh9fla4uqlk7clayad5pu8ync9q6kngp5y5mwmul7zwzmzp48lnvm0q0xpe50 | addr1qx7zqkf4aapmdh6js3xe3c6k2mnfpfj69crf2rpg2du26s0k7clayad5pu8ync9q6kngp5y5mwmul7zwzmzp48lnvm0q7qzata |     2824075 | 104998886|

### How to derive the staking address from the payment address?

Compute the stake key for each row. Cardano uses bech32. Install bech32 instead and decode/encode the address.

Download the bech32 tool as part of cardano-wallet from github

```bash
wget https://github.com/input-output-hk/cardano-wallet/releases/download/v2022-12-14/cardano-wallet-v2022-12-14-linux64.tar.gz
tar -xf cardano-wallet-v2022-12-14-linux64.tar.gz
cd cardano-wallet-v2022-12-14-linux64
./bech32
```

Let’s say you have address
```bash
$ set addr addr1q9f2prypgqkrmr5497d8ujl4s4qu9hx0w6kruspdkjyudc2xjgcagrdn0jxnf47yd96p7zdpfzny30l2jh5u5vwurxasjwukdr
$ echo "e1$(echo $addr | ./bech32 | tail -c 57)" | ./bech32 stake
stake1u9rfyvw5pkeherf56lzxjaqlpxs53fjghl4ft6w2x8wpnwchfeam3
```
