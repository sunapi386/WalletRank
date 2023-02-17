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

In creating a better fraud detection model, each of these can be considered a feature task to solve, keeping track
of them in Jira or a similar issue tracking product.

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

### Python wrapper `resolve_addr2stake`
Since these are command line tools, it makes sense to have a python wrapper.

In [resolve.py](src%2Fresolve.py):

```python
def resolve_addr2stake(address: str) -> str:
    """
     same as 'echo "e1$(echo {address} | ./bech32 | tail -c 57)" |./bech32 stake'
     It may be quicker to cache the address, result in a lookup table
    :param address: wallet address, such as
    addr1q9f2prypgqkrmr5497d8ujl4s4qu9hx0w6kruspdkjyudc2xjgcagrdn0jxnf47yd96p7zdpfzny30l2jh5u5vwurxasjwukdr
    :return: stake key, such as
    stake1g6frr4qdkd7g6dxhc35hg8cf59y2vj9la227nj33msvmkczsmnx
    """
    p1 = subprocess.Popen(["echo", address], stdout=subprocess.PIPE)
    p2 = subprocess.run(['./cardano-wallet/bech32'], stdin=p1.stdout, capture_output=True)
    s = p2.stdout.strip().decode('utf-8')
    p3 = subprocess.Popen(["echo", s[-56:]], stdout=subprocess.PIPE)
    p4 = subprocess.run(['./cardano-wallet/bech32', 'stake'], stdin=p3.stdout, capture_output=True)
    return p4.stdout.strip().decode('utf-8')
```

## Test the pipeline with a small subset of the data from `sender_reciver_amount_id` material view.

Dump 100 rows of the table as csv using `psql2csv`

```bash
./psql2csv postgres://cardano:qwe123@mini.ds:5432/dbsync "select * from sender_reciver_amount_id limit 100" > sender_reciver_amount_id-100.csv
```

Load this into pandas (or dask, if there are many large csvs).


In `sender_reciver_amount_id-100.csv` there are 100 rows. We can easily load to a df and use `apply`.

```python
df = pd.read_csv('./sender_reciver_amount_id-100.csv')
df['src'] = df.sender.apply(resolve_addr2stake)
df['dst'] = df.receiver.apply(resolve_addr2stake)
```

This takes a long time
```
In [76]: %time df['dst'] = df.receiver.apply(resolve_addr2stake)
CPU times: user 210 ms, sys: 1.65 s, total: 1.86 s
Wall time: 5.61 s
```

Result

```
                                               sender                                           receiver       amount      tx_id                                                src                                                dst
0   addr1qy9yrva9vnxjd09vvnr7v8z7qzr73vyyd40qhnhz9...  addr1qy9yrva9vnxjd09vvnr7v8z7qzr73vyyd40qhnhz9...    280113718  106066808  stake1z96tmfcw8wjwf6mygq9gqt9htpqj4uz856yse4hd...  stake1z96tmfcw8wjwf6mygq9gqt9htpqj4uz856yse4hd...
1   addr1qxlhz4d0vcmut378mu56zgzng4wm8xj4dqjahdvxn...  addr1wxn9efv2f6w82hagxqtn62ju4m293tqvw0uhmdl64...     22265944  109537649  stake1w2sas4q24c0yvgpndajsenq3raljv892d465nsnt...  stake15ew2tzjwn364l2pszu7j5h9w63v2crrnl97m074w...
2   addr1qxlhz4d0vcmut378mu56zgzng4wm8xj4dqjahdvxn...  addr1qxlhz4d0vcmut378mu56zgzng4wm8xj4dqjahdvxn...      1150770  109537649  stake1w2sas4q24c0yvgpndajsenq3raljv892d465nsnt...  stake1w2sas4q24c0yvgpndajsenq3raljv892d465nsnt...
3   addr1qxlhz4d0vcmut378mu56zgzng4wm8xj4dqjahdvxn...  addr1qyylzh9428hzu2rlsuv50hntjm8qw6s3may0a2fcs...  13884036547  109537649  stake1w2sas4q24c0yvgpndajsenq3raljv892d465nsnt...  stake1w2sas4q24c0yvgpndajsenq3raljv892d465nsnt...
4   addr1q8k8fauns9syu05xc0n0rtaa6sj2cl6kwlpcx2jvv...  addr1qx3jt2ddwkcwccku7e7nfmmmd0d5sguy3cdjnv6m7...      1232660  109878818  stake1nr8lu5hyslu2t2j08mvu93sdtrjp66e8lhaat4r4...  stake12a8fzqzsnx3er32jcsdmapr732998gpdx832z6d0...
..                                                ...                                                ...          ...        ...                                                ...                                                ...
95  addr1q85drlt7c7fkxde5rpx5vdrgpnpdnt8nnza5a68dw...  addr1q85drlt7c7fkxde5rpx5vdrgpnpdnt8nnza5a68dw...    138821262  104348981  stake1f93gr5yqz29nqlsgpq3fzpfmkkttmvkcuys8tkyx...  stake1f93gr5yqz29nqlsgpq3fzpfmkkttmvkcuys8tkyx...
96  addr1q85drlt7c7fkxde5rpx5vdrgpnpdnt8nnza5a68dw...  addr1wxn9efv2f6w82hagxqtn62ju4m293tqvw0uhmdl64...      4068744  104348981  stake1f93gr5yqz29nqlsgpq3fzpfmkkttmvkcuys8tkyx...  stake15ew2tzjwn364l2pszu7j5h9w63v2crrnl97m074w...
97  addr1qylz2azpzq47j84xuv00jlnsh4gkzpl370ne65nsh...  addr1v8vqt24ee97ks09lp9tfupen3p09knqqw2ryp2c5p...     40000000  106169755  stake1quewckyn8s26taneauq30l6l4s7cz2kgrhks6eaa...  stake1mqz64wwf045re0cf260qwvugted5cqrjseq2k9q0...
98  addr1qylz2azpzq47j84xuv00jlnsh4gkzpl370ne65nsh...  addr1qxq74c8dr75m2j0ejmewrkpztd2kvj63kdujren7l...     10094086  106169755  stake1quewckyn8s26taneauq30l6l4s7cz2kgrhks6eaa...  stake1quewckyn8s26taneauq30l6l4s7cz2kgrhks6eaa...
99  addr1q8x8uxfmj2v7xcyp92vcsmfdnxs9slsvekc6nrdqn...  addr1vx69slry2j9sevq3jstfws2wm8q3zeqra59vm0mc4...      5000000  107627554  stake1jjp537auwgldqhzjnyc3xa9t7exaavw5fuzhdczz...  stake1k3v8cez53vxtqyv5z6t5znkecygkgqldptxm779v...

[100 rows x 6 columns]
```

For more details, see [src_dst_amount_id-100.csv](data/src_dst_amount_id-100.csv).

**Note:** there are numerous rows that have duplicate src & dst -- this is the result of UXTOs model approach.

## To run

```bash
python3 main.py -f data/simple.csv
python3 main.py -f data/src_dst_amount_id-100.csv
```

# Future Work

### Pipeline notes and potential Jira issues

In the interest of time, these issue will be beyond the scope; but can be tracked as Jira issues.

1. CSVs. This is to test the infrastructure pipeline prior to setting up database as our backend.
   Or, to run on a one-time basis. Anything on a large scale is in-appropriate to store in csv files, so this is only
   done for ease of testing access. Also see the [section on scaling up](#scaling-up).
2. The function `resolve_addr2stake` runs as subprocess - this takes a long time due to the 4 sys-calls. It isn't what
   should be used here. In processing 100 rows, it took 5.61 s and there was a lot of overhead.
3. Looking at `src` and `dst` columns, there are many duplicate stake keys, because of the UXTOs model. Rows where
   `src == dst` should be ignored, because it does not represent a transaction where "Alice" sends amount to "Bob".
   Furthermore, this row should be dropped when processing the transaction, because less data means less scaling.
4. Multiple rows exist for the same `tx_id`. A single cardano transaction may contain multiple inputs per address
   from multiple wallets, so long as the transaction contains a signature for every unique address from which a UTXO
   is being consumed. Although the Cardano protocol supports sending to multiple wallet address at once, this is
   usually not the case -- at least not from a visual inspection of the 100 rows. Usually the stake address is
   one-to-one. So it may be of interest to look into `tx_id`s for many-to-many, many-to-one, one-to-many transactions.
5. Following up on many-to-many, many-to-one, one-to-many transactions: these may be more heavily used by smart
   contracts, or web2 apps such as Splitwise, Venmo, Zelle, etc, when if and when they support Cardano to split bills.


## Scaling up

The existing data can be batch-processed. It is processing the (near) real-time data that would be of interest. What
would be the infrastructure setup needed to do that?

1. The speed to process a transaction needs to be quicker than the speed the transactions, ideally more
   than the theoretical maximum.
2. For Ethereum Proof-of-Stake can process 20,000 to 100,000 TPS.
3. For Cardano it is presently at 250 TPS. However, in the future upgrade,
 [Hydra](https://iohk.io/en/blog/posts/2020/03/26/enter-the-hydra-scaling-distributed-ledgers-the-evidence-based-way/)
, it is possible to achieve roughly 1,000 TPS.

It's a lot, but thankfully, blockchains are slower than traditional sharded databases. But, can we just reach any TPS
number that we want?

### Factors in scaling up

TPS as a metric to compare systems is an oversimplification. Without further context, a TPS number is close to
meaningless. In order to properly interpret it, and make comparisons, you need to know
- how quickly the transaction analysis can be done
- how large and complicated the transactions are (which has an impact on transaction validation times,
message propagation time, requirements on the local storage system, and composition of the head participants);
- what kind of hardware and network connections exist in those locations;
- size of the cluster (which influences the communication overhead);
- its geographic distribution (which determines how much time it takes for information to transit through the system);
- how the quality of service (speed of transaction / analysis to providing data to end users) is impacted by a high rate of
transactions;

### Epic Roadmap

As an epic roadmap to building out scalable infrastructure, we likely need to investigate the following
["Jira Epics"](https://support.atlassian.com/jira-software-cloud/docs/what-is-an-epic/).

- Determine what blockchain, and speed of transactions we need to ingress
- Determine the type of analytics and its "online" processing speed
- Approximate compute and database needs; caching, real time changelist data streaming, etc.
- Shop to compare and select service provider for compute / database
- Automate (devops) scaling out infrastructure: images, docker containers, infrastructure-as-code, etc.
- Modify backend/frontend to use the new data sources


## Todo plan

1. Create or use/modify existing graph library, such as [networkx](https://networkx.org/) for backend storage.
   What is needed is a NetworkX-like interface for large persistent graphs stored inside DBMS, enabling to upscale from
   Gigabyte graphs to even Terabyte-Petabyte graphs (that won't fit into RAM), without changing code. Similar to
   (NetworkXum)[https://github.com/unum-cloud/NetworkXum]. This graph system can be used for other transaction
   analysis. For Cardano, there will be at a minimum over 11M unique entries, approximately 2GB of stake addresses,
   and approx 115M transactions. This part may take 2 days developer time.
   - Setup any infrastructure, such as MongoDB, as the backend.
2. Add feature to the graph library, for PageRank. This part may take 1-2 days developer time.
    - Per-iteration of updating and normalizing weights, keeping track of weights only.
    - Graph meta function for running through n-iterations.
3. Construct a complete material view (not just the last 1M entries). Likely will take 115 x 16 min ~= 31 hrs.
4. Transform the payment address to a stake address. Assume taking 5s to run 100 entries, this will take
   - 115M / 100 * 5s / 60s / 60s ~= 160 hrs (approx 6.7 days - but this could be parallelized)
5. Construct the graph from stake address. Unknown how long to run. Assuming speed to process 1M tx per second:
     -  115M rows would take 115s to process.
6. Iterate 500 times over 2M stake addresses. Assuming 2s per iteration of 2M stake address:
   - 2 * 500 times / 60s / 24h ~= 68 mins
