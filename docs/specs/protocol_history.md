# Protocol History

The tables below list every Ethereum hardfork, its mainnet activation, the EIPs it includes, its meta EIP, its specification in EELS, and the Ethereum Foundation announcement blog post.

## Stable specifications

| Version and Code Name | Fork Block / Timestamp | Incl EIPs | Meta EIP | Specification | Blog |
|-----------------------|------------------------|-----------|----------|---------------|------|
| Frontier | Block `0` |  |  | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/frontier) | [Blog](https://blog.ethereum.org/2015/07/22/frontier-is-coming-what-to-expect-and-how-to-prepare/) |
| Frontier Thawing | Block `200000` |  |  |  | [Blog](https://blog.ethereum.org/2015/08/04/the-thawing-frontier/) |
| Homestead | Block `1150000` | [EIP-2] <br/> [EIP-7] <br/> [EIP-8] | [EIP-606] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/homestead) | [Blog](https://blog.ethereum.org/2016/02/29/homestead-release/) |
| DAO Wars | aborted |  |  |  | [Blog](https://blog.ethereum.org/2016/06/24/dao-wars-youre-voice-soft-fork-dilemma/) |
| DAO Fork | Block `1920000` |  | [EIP-779] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/dao_fork) | [Blog](https://blog.ethereum.org/2016/07/15/to-fork-or-not-to-fork/) |
| Tangerine Whistle | Block `2463000` | [EIP-150] | [EIP-608] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/tangerine_whistle) | [Blog](https://blog.ethereum.org/2016/10/13/announcement-imminent-hard-fork-eip150-gas-cost-changes/) |
| Spurious Dragon | Block `2675000` | [EIP-155] <br/> [EIP-160] <br/> [EIP-161] <br/> [EIP-170] | [EIP-607] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/spurious_dragon) | [Blog](https://blog.ethereum.org/2016/11/18/hard-fork-no-4-spurious-dragon/) |
| Byzantium | Block `4370000` | [EIP-100] <br/> [EIP-140] <br/> [EIP-196] <br/> [EIP-197] <br/> [EIP-198] <br/> [EIP-211] <br/> [EIP-214] <br/> [EIP-649] <br/> [EIP-658] | [EIP-609] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/byzantium) | [Blog](https://blog.ethereum.org/2017/10/12/byzantium-hf-announcement/) |
| Constantinople | Block `7280000` | [EIP-145] <br/> [EIP-1014] <br/> [EIP-1052] <br/> [EIP-1234] <br/> [EIP-1283] | [EIP-1013] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/constantinople) | [Blog](https://blog.ethereum.org/2019/02/22/ethereum-constantinople-st-petersburg-upgrade-announcement/) |
| Petersburg | Block `7280000` | [EIP-145] <br/> [EIP-1014] <br/> [EIP-1052] <br/> [EIP-1234] | [EIP-1716] |  | [Blog](https://blog.ethereum.org/2019/02/22/ethereum-constantinople-st-petersburg-upgrade-announcement/) |
| Istanbul | Block `9069000` | [EIP-152] <br/> [EIP-1108] <br/> [EIP-1344] <br/> [EIP-1884] <br/> [EIP-2028] <br/> [EIP-2200] | [EIP-1679] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/istanbul) | [Blog](https://blog.ethereum.org/2019/11/20/ethereum-istanbul-upgrade-announcement/) |
| Muir Glacier | Block `9200000` | [EIP-2384] | [EIP-2387] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/muir_glacier) | [Blog](https://blog.ethereum.org/2019/12/23/ethereum-muir-glacier-upgrade-announcement/) |
| Berlin | Block `12244000` | [EIP-2565] <br/> [EIP-2929] <br/> [EIP-2718] <br/> [EIP-2930] | ~~[EIP-2070]~~ <br/> [EIP-7568] (backfill) | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/berlin) | [Blog](https://blog.ethereum.org/2021/03/08/ethereum-berlin-upgrade-announcement/) |
| London | Block `12965000` | [EIP-1559] <br/> [EIP-3198] <br/> [EIP-3529] <br/> [EIP-3541] <br/> [EIP-3554] | [EIP-7568] (backfill) | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/london) | [Blog](https://blog.ethereum.org/2021/07/15/london-mainnet-announcement/) |
| Arrow Glacier | Block `13773000` | [EIP-4345] | [EIP-7568] (backfill) | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/arrow_glacier) | [Blog](https://blog.ethereum.org/2021/11/10/arrow-glacier-announcement/) |
| Gray Glacier | Block `15050000` | [EIP-5133] | [EIP-7568] (backfill) | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/gray_glacier) | [Blog](https://blog.ethereum.org/2022/06/16/gray-glacier-announcement/) |
| Paris | Block `15537394` | [EIP-3675] <br/> [EIP-4399] | [EIP-7568] (backfill) | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/paris) | [Blog](https://blog.ethereum.org/2022/08/24/mainnet-merge-announcement) |
| Shanghai | Timestamp `1681338455` | [EIP-3651] <br/> [EIP-3855] <br/> [EIP-3860] <br/> [EIP-4895] | [EIP-7568] (backfill) | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/shanghai) | [Blog](https://blog.ethereum.org/2023/03/28/shapella-mainnet-announcement) |
| Cancun | Timestamp `1710338135` | [EIP-1153] <br/> [EIP-4788] <br/> [EIP-4844] <br/> [EIP-5656] <br/> [EIP-6780] <br/> [EIP-7044] <br/> [EIP-7045] <br/> [EIP-7514] <br/> [EIP-7516] | [EIP-7569] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/cancun) | [Blog](https://blog.ethereum.org/2024/02/27/dencun-mainnet-announcement) |
| Prague | Timestamp `1746612311` | [EIP-2537] <br/> [EIP-2935] <br/> [EIP-6110] <br/> [EIP-7002] <br/> [EIP-7251] <br/> [EIP-7549] <br/> [EIP-7623] <br/> [EIP-7685] <br/> [EIP-7691] <br/> [EIP-7702] | [EIP-7600] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/prague) | [Blog](https://blog.ethereum.org/2025/04/23/pectra-mainnet) |
| Osaka | Timestamp `1764798551` | [EIP-7594] <br/> [EIP-7642] <br/> [EIP-7823] <br/> [EIP-7825] <br/> [EIP-7883] <br/> [EIP-7892] <br/> [EIP-7910] <br/> [EIP-7917] <br/> [EIP-7918] <br/> [EIP-7934] <br/> [EIP-7935] <br/> [EIP-7939] <br/> [EIP-7951] | [EIP-7607] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/osaka) | [Blog](https://blog.ethereum.org/2025/11/06/fusaka-mainnet-announcement) |
| BPO1 | Timestamp `1765290071` | [EIP-7892] |  | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/bpo1) |  |
| BPO2 | Timestamp `1767747671` | [EIP-7892] | [EIP-8135] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/bpo2) |  |

!!! note "Activation mechanism"
    Starting with Paris, updates are no longer rolled out based on block numbers. Paris was enabled once proof-of-work Total Difficulty reached `58750000000000000000000`. As of Shanghai (at `1681338455`), upgrade activation is based on timestamps.

## Unstable specifications

| Version and Code Name | Fork Block / Timestamp | Incl EIPs | Meta EIP | Specification | Blog |
|-----------------------|------------------------|-----------|----------|---------------|------|
| Amsterdam | TBD | [EIP-2780] <br/> [EIP-7708] <br/> [EIP-7778] <br/> [EIP-7843] <br/> [EIP-7928] <br/> [EIP-7954] <br/> [EIP-7976] <br/> [EIP-7981] <br/> [EIP-7997] <br/> [EIP-8024] <br/> [EIP-8037] <br/> [EIP-8038] <br/> [EIP-8246] <br/> [EIP-8282] | [EIP-7773] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/amsterdam) |  |
| Bogota | TBD |  | [EIP-8081] | [Spec](https://github.com/ethereum/execution-specs/tree/HEAD/src/ethereum/forks/bogota) |  |

[EIP-2]: https://eips.ethereum.org/EIPS/eip-2
[EIP-7]: https://eips.ethereum.org/EIPS/eip-7
[EIP-8]: https://eips.ethereum.org/EIPS/eip-8
[EIP-100]: https://eips.ethereum.org/EIPS/eip-100
[EIP-140]: https://eips.ethereum.org/EIPS/eip-140
[EIP-145]: https://eips.ethereum.org/EIPS/eip-145
[EIP-150]: https://eips.ethereum.org/EIPS/eip-150
[EIP-152]: https://eips.ethereum.org/EIPS/eip-152
[EIP-155]: https://eips.ethereum.org/EIPS/eip-155
[EIP-160]: https://eips.ethereum.org/EIPS/eip-160
[EIP-161]: https://eips.ethereum.org/EIPS/eip-161
[EIP-170]: https://eips.ethereum.org/EIPS/eip-170
[EIP-196]: https://eips.ethereum.org/EIPS/eip-196
[EIP-197]: https://eips.ethereum.org/EIPS/eip-197
[EIP-198]: https://eips.ethereum.org/EIPS/eip-198
[EIP-211]: https://eips.ethereum.org/EIPS/eip-211
[EIP-214]: https://eips.ethereum.org/EIPS/eip-214
[EIP-606]: https://eips.ethereum.org/EIPS/eip-606
[EIP-607]: https://eips.ethereum.org/EIPS/eip-607
[EIP-608]: https://eips.ethereum.org/EIPS/eip-608
[EIP-609]: https://eips.ethereum.org/EIPS/eip-609
[EIP-649]: https://eips.ethereum.org/EIPS/eip-649
[EIP-658]: https://eips.ethereum.org/EIPS/eip-658
[EIP-779]: https://eips.ethereum.org/EIPS/eip-779
[EIP-1013]: https://eips.ethereum.org/EIPS/eip-1013
[EIP-1014]: https://eips.ethereum.org/EIPS/eip-1014
[EIP-1052]: https://eips.ethereum.org/EIPS/eip-1052
[EIP-1108]: https://eips.ethereum.org/EIPS/eip-1108
[EIP-1153]: https://eips.ethereum.org/EIPS/eip-1153
[EIP-1234]: https://eips.ethereum.org/EIPS/eip-1234
[EIP-1283]: https://eips.ethereum.org/EIPS/eip-1283
[EIP-1344]: https://eips.ethereum.org/EIPS/eip-1344
[EIP-1559]: https://eips.ethereum.org/EIPS/eip-1559
[EIP-1679]: https://eips.ethereum.org/EIPS/eip-1679
[EIP-1716]: https://eips.ethereum.org/EIPS/eip-1716
[EIP-1884]: https://eips.ethereum.org/EIPS/eip-1884
[EIP-2028]: https://eips.ethereum.org/EIPS/eip-2028
[EIP-2070]: https://eips.ethereum.org/EIPS/eip-2070
[EIP-2200]: https://eips.ethereum.org/EIPS/eip-2200
[EIP-2384]: https://eips.ethereum.org/EIPS/eip-2384
[EIP-2387]: https://eips.ethereum.org/EIPS/eip-2387
[EIP-2537]: https://eips.ethereum.org/EIPS/eip-2537
[EIP-2565]: https://eips.ethereum.org/EIPS/eip-2565
[EIP-2718]: https://eips.ethereum.org/EIPS/eip-2718
[EIP-2780]: https://eips.ethereum.org/EIPS/eip-2780
[EIP-2929]: https://eips.ethereum.org/EIPS/eip-2929
[EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930
[EIP-2935]: https://eips.ethereum.org/EIPS/eip-2935
[EIP-3198]: https://eips.ethereum.org/EIPS/eip-3198
[EIP-3529]: https://eips.ethereum.org/EIPS/eip-3529
[EIP-3541]: https://eips.ethereum.org/EIPS/eip-3541
[EIP-3554]: https://eips.ethereum.org/EIPS/eip-3554
[EIP-3651]: https://eips.ethereum.org/EIPS/eip-3651
[EIP-3675]: https://eips.ethereum.org/EIPS/eip-3675
[EIP-3855]: https://eips.ethereum.org/EIPS/eip-3855
[EIP-3860]: https://eips.ethereum.org/EIPS/eip-3860
[EIP-4345]: https://eips.ethereum.org/EIPS/eip-4345
[EIP-4399]: https://eips.ethereum.org/EIPS/eip-4399
[EIP-4788]: https://eips.ethereum.org/EIPS/eip-4788
[EIP-4844]: https://eips.ethereum.org/EIPS/eip-4844
[EIP-4895]: https://eips.ethereum.org/EIPS/eip-4895
[EIP-5133]: https://eips.ethereum.org/EIPS/eip-5133
[EIP-5656]: https://eips.ethereum.org/EIPS/eip-5656
[EIP-6110]: https://eips.ethereum.org/EIPS/eip-6110
[EIP-6780]: https://eips.ethereum.org/EIPS/eip-6780
[EIP-7002]: https://eips.ethereum.org/EIPS/eip-7002
[EIP-7044]: https://eips.ethereum.org/EIPS/eip-7044
[EIP-7045]: https://eips.ethereum.org/EIPS/eip-7045
[EIP-7251]: https://eips.ethereum.org/EIPS/eip-7251
[EIP-7514]: https://eips.ethereum.org/EIPS/eip-7514
[EIP-7516]: https://eips.ethereum.org/EIPS/eip-7516
[EIP-7549]: https://eips.ethereum.org/EIPS/eip-7549
[EIP-7568]: https://eips.ethereum.org/EIPS/eip-7568
[EIP-7569]: https://eips.ethereum.org/EIPS/eip-7569
[EIP-7594]: https://eips.ethereum.org/EIPS/eip-7594
[EIP-7600]: https://eips.ethereum.org/EIPS/eip-7600
[EIP-7607]: https://eips.ethereum.org/EIPS/eip-7607
[EIP-7623]: https://eips.ethereum.org/EIPS/eip-7623
[EIP-7642]: https://eips.ethereum.org/EIPS/eip-7642
[EIP-7685]: https://eips.ethereum.org/EIPS/eip-7685
[EIP-7691]: https://eips.ethereum.org/EIPS/eip-7691
[EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702
[EIP-7708]: https://eips.ethereum.org/EIPS/eip-7708
[EIP-7773]: https://eips.ethereum.org/EIPS/eip-7773
[EIP-7778]: https://eips.ethereum.org/EIPS/eip-7778
[EIP-7823]: https://eips.ethereum.org/EIPS/eip-7823
[EIP-7825]: https://eips.ethereum.org/EIPS/eip-7825
[EIP-7843]: https://eips.ethereum.org/EIPS/eip-7843
[EIP-7883]: https://eips.ethereum.org/EIPS/eip-7883
[EIP-7892]: https://eips.ethereum.org/EIPS/eip-7892
[EIP-7910]: https://eips.ethereum.org/EIPS/eip-7910
[EIP-7917]: https://eips.ethereum.org/EIPS/eip-7917
[EIP-7918]: https://eips.ethereum.org/EIPS/eip-7918
[EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
[EIP-7934]: https://eips.ethereum.org/EIPS/eip-7934
[EIP-7935]: https://eips.ethereum.org/EIPS/eip-7935
[EIP-7939]: https://eips.ethereum.org/EIPS/eip-7939
[EIP-7951]: https://eips.ethereum.org/EIPS/eip-7951
[EIP-7954]: https://eips.ethereum.org/EIPS/eip-7954
[EIP-7976]: https://eips.ethereum.org/EIPS/eip-7976
[EIP-7981]: https://eips.ethereum.org/EIPS/eip-7981
[EIP-7997]: https://eips.ethereum.org/EIPS/eip-7997
[EIP-8024]: https://eips.ethereum.org/EIPS/eip-8024
[EIP-8037]: https://eips.ethereum.org/EIPS/eip-8037
[EIP-8038]: https://eips.ethereum.org/EIPS/eip-8038
[EIP-8081]: https://eips.ethereum.org/EIPS/eip-8081
[EIP-8135]: https://eips.ethereum.org/EIPS/eip-8135
[EIP-8246]: https://eips.ethereum.org/EIPS/eip-8246
[EIP-8282]: https://eips.ethereum.org/EIPS/eip-8282

## Clarifications without a protocol release

Some clarifications were enabled without protocol releases:

| EIP | Block No. |
|-----|-----------|
| [EIP-2681](https://eips.ethereum.org/EIPS/eip-2681) | 0 |
| [EIP-3607](https://eips.ethereum.org/EIPS/eip-3607) | 0 |
| [EIP-7523](https://eips.ethereum.org/EIPS/eip-7523) | 15537394 |
