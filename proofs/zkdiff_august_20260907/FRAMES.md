---
version: 1.2
date: 2026-09-09
status: the 112 raw sensor frames of the proof rows, published on the data layer by the principal's decision of 8 September 2026: paths, sizes, BLAKE3 (the chain log's and the statements') and SHA-256 (the receipts'), and how to re-execute any row from them
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

# The raw frames of the proof rows

The camera's frame for each proof row 600 to 711, exactly the bytes the guest hashed in circuit (`BLAKE3(raw_r)` at statement
offset 420, `STATEMENT.md` section 2): `uint8 4600 x 5320` row-major `RGGB`, 24,472,000 bytes each, 2,740,864,000 bytes in all.
They are served from the data layer (bucket `truthbeam`, `https://data.truthbeam.com/`), prefix `results/zkdiff_august_20260907/v1/`,
as `frames/frame_NNNNNN.raw`, beside `frames/FRAMES.json` (this table as JSON) and `frames/README.md`. An earlier revision of this
package held them; the principal decided on 8 September 2026 to publish them together with the August camera-derived tensors
(`LARGE_FILES.md`; `REDACTION.md`). The frames of the training rows 0 to 599 are not part of this package.

What the frames show. The August frames depict a masked participant in a recognisable indoor setting: the participant wears a
full face covering, a top hat and distinctive clothing, and no unobscured face appears in any of the 112 frames (every frame was
viewed before publication). Camera-derived tensors retain images of participants and their surroundings, including
earlier-session examples (the cached d2 and v10 rows and the four August training rows 587, 592, 597 and 598 whose reductions
serve as wrong-row hints, `LARGE_FILES.md`). These materials are not anonymised; identity may be inferred from clothing,
movement or context. A frame is a plain `uint8` array: `numpy.fromfile(path, dtype=numpy.uint8).reshape(4600, 5320)` reads it,
and `[0::2, 0::2]`, `[0::2, 1::2]`, `[1::2, 0::2]`, `[1::2, 1::2]` are the R, G, G and B planes.

Each frame's BLAKE3 equals the chain log's `bayer_blake3_hex` for its row and the digest every statement carries, and its SHA-256
equals the receipt's `raw_sha256`; both were checked when the data-layer bundle was built, and a reader checks a downloaded frame
with `sha256sum` against this table (or `b3sum` against the chain log). With a frame, `capsule/reexecute/reexecute_row.sh ROW
--frames-dir DIR` recomputes the row's 752-byte statement on the CPU with no toolchain and compares it with the published one
(`capsule/README.md`); with the SP1 toolchain, `replicate/replicate.sh execute ROW --frame PATH` does the same through the
complete guest in the SP1 executor, and `prove` re-proves the row on a CUDA GPU (`replicate/README.md`). What a frame establishes
is bounded by `CLAIM_BOUNDARY.md`: the proofs bind its bytes, not its origin, and say nothing about the people it shows.

| row | data-layer path | bytes | BLAKE3 (chain log, statement offset 420) | SHA-256 (receipt `raw_sha256`) |
|---:|---|---:|---|---|
| 600 | `results/zkdiff_august_20260907/v1/frames/frame_000600.raw` | 24,472,000 | `9d4a0745dd0990b12ab8c94d524430dd3b3559face4d7d4d621c481a72087d4a` | `5c8e785610872115a5a67f90ae14b7b3b35cf3e1da8f5762c2d48386f7be211c` |
| 601 | `results/zkdiff_august_20260907/v1/frames/frame_000601.raw` | 24,472,000 | `6b78b755bfd7ac35c34ffadcf405ee77d7ac46c355690c6be2c7bcf908f390eb` | `5b46ae57e79250e6982bf0b1276e54a001cf3559aaea40ad8b9cadd7069e94a7` |
| 602 | `results/zkdiff_august_20260907/v1/frames/frame_000602.raw` | 24,472,000 | `ef923610c7bfa7b3f75c3b81ae1d7b53d13835a5db52bb4f7595061f9584b5fa` | `78a5f19d7085604ceb38028a2fe12e39088699cdba8297fe1251b3e17e58efb5` |
| 603 | `results/zkdiff_august_20260907/v1/frames/frame_000603.raw` | 24,472,000 | `495d42da124cd7071afba43221d24d342b41e317a7736dd9189b09be285bb623` | `45ae9a130bb274d7617bb81fd2147e5661b49d120c3ad595d93e5d6e4f6829b2` |
| 604 | `results/zkdiff_august_20260907/v1/frames/frame_000604.raw` | 24,472,000 | `895e059e825cb3ac157b10231c6414c531072609ebd3f3a472fa5573e05a4572` | `0cde47a5b093169df59b38cd2116968c117284cc8aa9f7aa18b51403b7472f43` |
| 605 | `results/zkdiff_august_20260907/v1/frames/frame_000605.raw` | 24,472,000 | `18bc4f775052d4f21408c91fba512a0cdcf641437cd33f9da5166c7bb4e085d8` | `dfd5d0b8f6a80d59c28531020ba1f9b519bdc6fd80b54af6a20fcbb109d8f716` |
| 606 | `results/zkdiff_august_20260907/v1/frames/frame_000606.raw` | 24,472,000 | `ccd3ae6f6471b3bcdaa86c32cffd0014cffadf4e0f1b27689a141d66752ac6b8` | `b2b3d06c8767005628b28389a2d131b21b083aacbf7298bdf07d40d997891c46` |
| 607 | `results/zkdiff_august_20260907/v1/frames/frame_000607.raw` | 24,472,000 | `6330bdfdfe10f0c8c39aa9bf0a4af3a8a7a4bd59e55988e64b8f44d9d2e64a7e` | `84b95b359baf94271481619374a848f11aa0a97373a55e69eb7af097e1b1f14d` |
| 608 | `results/zkdiff_august_20260907/v1/frames/frame_000608.raw` | 24,472,000 | `28692c240d7741e58f3344635607f0875f04109b105f7ae420bcad9eaa44fdd8` | `34ba7714a572d3e5e994135ba97e03d853d29d30a62e9605ec1f651ded3cd464` |
| 609 | `results/zkdiff_august_20260907/v1/frames/frame_000609.raw` | 24,472,000 | `333c95c18c71ff1e050cee16d28c4c08b8f710003364818414d8efafaba5df6b` | `3888ab1df94d63535a4d289ffe4b10476673490483d21301c7448d95cefc701b` |
| 610 | `results/zkdiff_august_20260907/v1/frames/frame_000610.raw` | 24,472,000 | `b496ae309f2c945da783cf96e0dc7330ad2c6406e618090254f5596b1b6cdc74` | `0a0febbb9e30ae5eba71ae0a9f6b6f1981345b4373138f644d6276c14fa54362` |
| 611 | `results/zkdiff_august_20260907/v1/frames/frame_000611.raw` | 24,472,000 | `2cc33dc18c6367154e57eda772db9790923e50a45a1727675332b79c3d60a1ff` | `3493ea93be1da2b4eb60cd74289eeb5e404c330c0317abfd1c73f8365b1113f8` |
| 612 | `results/zkdiff_august_20260907/v1/frames/frame_000612.raw` | 24,472,000 | `e5b78826c63ba29fbe5bd45005c1aa46ed773f7fae2b76ba4fed7af16691a880` | `1d020d8a608b8d1959ef98b613ddc73d069b6a88f8a8e069b6410805b321fc02` |
| 613 | `results/zkdiff_august_20260907/v1/frames/frame_000613.raw` | 24,472,000 | `3c10180d13b47f4bc4f2aaa94048969594dbdb214e51eb946564ea78ff6a19eb` | `3c3dc9bf78e741b65ac044a223960a0bef2f5feea637b145414ac6f42c4b0ba0` |
| 614 | `results/zkdiff_august_20260907/v1/frames/frame_000614.raw` | 24,472,000 | `a01b996247b33977407ebca9d61a9ca17bc68b85d2a7997efa8e0df9b883fa0a` | `6b7bf5839c77fa4f04631e10b4513572b2d47f4c733af985f131c4c10dce42f7` |
| 615 | `results/zkdiff_august_20260907/v1/frames/frame_000615.raw` | 24,472,000 | `8076a1658e38f33b16d70774a436e63269241e148f216a7c0fa9d47a122ee5e1` | `60d347b6a7787eb46dc52e7aa33dff88fb8f7d91b13c616481c6b16061da9b5e` |
| 616 | `results/zkdiff_august_20260907/v1/frames/frame_000616.raw` | 24,472,000 | `666cdb996a1a80b5b609580378aaf451e282b13b59be5d6573d5c28f57b71c28` | `d2c43f4c048fb5fb2cff3372f281e69e09b3d8edfb9fea2faf008ed15a5d7e79` |
| 617 | `results/zkdiff_august_20260907/v1/frames/frame_000617.raw` | 24,472,000 | `0a1ecd2e916e50daa0d05bd40bb48e373ca79ffaf9dce78e791da57aaf6e1c63` | `8c4a0a54338e49738c1cc0e0a444341694e5a51dd9da3ac677fef65a3a84149d` |
| 618 | `results/zkdiff_august_20260907/v1/frames/frame_000618.raw` | 24,472,000 | `64628432fc495896fcaeb9d64142e293f8d11d09667d17a02157b27ed9878652` | `e3726a2db1ccee918de492f3e53a3ebe18eb9a3926f84ba5640b54aea2c766c0` |
| 619 | `results/zkdiff_august_20260907/v1/frames/frame_000619.raw` | 24,472,000 | `6a377dc94e83a9abdf295ba0f757c0b55487c751768f7f72e8d18caa769b2b7d` | `a737c92eadd7a8035b15b49091db08481226ca65ccb60e70a9ed973d2724a136` |
| 620 | `results/zkdiff_august_20260907/v1/frames/frame_000620.raw` | 24,472,000 | `df144585a9d34cf443863204269039451e841c693b908a29b520a4de5b5ff49a` | `acfb94f8a203495b9f6a336eee655c1052de3ad4db1f9846c05f206b824cce86` |
| 621 | `results/zkdiff_august_20260907/v1/frames/frame_000621.raw` | 24,472,000 | `7659b3e3caa2592a44ce9d72078ca0d56525daab9ba8398af959de73633c7a47` | `9b7af229faa857560115ea8747bfc3ff402823ce60a06f79b937189d9aa2b2e0` |
| 622 | `results/zkdiff_august_20260907/v1/frames/frame_000622.raw` | 24,472,000 | `7241263840f361c8f4f97f962c8972db4c17fd00675407a109a18698c639a8df` | `8f826f8cd4f2fc5376f01ebfd4c487143bf35a3b448077421400c8a5d03679a5` |
| 623 | `results/zkdiff_august_20260907/v1/frames/frame_000623.raw` | 24,472,000 | `74e7ccfac5a8dfbc0eabec61fa692f12196c21426d2417783374e7a67b1d3b08` | `02ac5f8be8b0764e8554eb3c2fcce02ee82cf7faced1d1dd4a0c2cfba1b58c6d` |
| 624 | `results/zkdiff_august_20260907/v1/frames/frame_000624.raw` | 24,472,000 | `547a13f6033cd8e35537ad1aa74a45387c2c2093926a9d43e1b79a45dbbb5377` | `859d228afd243c7f71f8491d6313e2fc7438c4abda9781a616299933cd3308ce` |
| 625 | `results/zkdiff_august_20260907/v1/frames/frame_000625.raw` | 24,472,000 | `ab17aab8e3ec03c7055738465662168b4f67d5dd937c04e6a04932022e3d5b00` | `527bbd63f4cd39ad5dd1626ee138c5efbccfe1b346eb11bed720e9e08e6344d0` |
| 626 | `results/zkdiff_august_20260907/v1/frames/frame_000626.raw` | 24,472,000 | `484b6819824fa2300bef0b11624f3091dc8125b3f2e79521b1118ad3faf6a064` | `c65e9bd35f09e2cd68797dea4acf6a3a4c1fecc3567c40eeb80ab717e9dc7311` |
| 627 | `results/zkdiff_august_20260907/v1/frames/frame_000627.raw` | 24,472,000 | `3c9ebcc6eadb07a01d0b94516f35945d53dd8b717a19cd7347a4930a9880ffa2` | `2e0881f15d12d3530b531345df4065ded8073e5c68eb36b6f4935477c1a368f0` |
| 628 | `results/zkdiff_august_20260907/v1/frames/frame_000628.raw` | 24,472,000 | `d2114e980b27642ce885d5b7a0be14710e4e73a8ac382c831312c4fc4ec186f9` | `b802e8795d4bdadb0e6a4f860de29cae73367fa32dc361b4062e470136d2a91b` |
| 629 | `results/zkdiff_august_20260907/v1/frames/frame_000629.raw` | 24,472,000 | `509c567f8b1e81992000a2bedf4f5097f6b0c48c31bae0a66bd5739f22cdfa02` | `1d448912d2f93038bf17fd8ed3e2f34475894a47e7503b5832960d7850af105b` |
| 630 | `results/zkdiff_august_20260907/v1/frames/frame_000630.raw` | 24,472,000 | `081afdb97c55708795ada0877781ba4405a9a3c73ee2b367ae37ca1564628fa2` | `ab1a9fb0ea2c4dacc4e9526ccabdd5c12c6d7ea71e1680b1719016f0bd6ed0a9` |
| 631 | `results/zkdiff_august_20260907/v1/frames/frame_000631.raw` | 24,472,000 | `d9920b86e76544ab19dba86052171c3f16fb727151e8e69052474c632c83b587` | `8f88dab3a8ca5f580bec86c67f3d75943fba463bbdd304de6b0bf3a953144cc8` |
| 632 | `results/zkdiff_august_20260907/v1/frames/frame_000632.raw` | 24,472,000 | `2c78a2f8d6c51f2287397412b168a8d103fb8299a7e2fab8b77d5ac02b1fce08` | `685b5c224c34b361ee0f573024c617e6e5e936bf8ad137ef8357be4cc3dfb70a` |
| 633 | `results/zkdiff_august_20260907/v1/frames/frame_000633.raw` | 24,472,000 | `5037e99abdc48e0cea4cbfbf2632cf4938d16759e10b1c86836ce937132ede7a` | `51bbd55a9c3579f569fb352d356952dc2a2d796045a653875d119e229fe2d7ff` |
| 634 | `results/zkdiff_august_20260907/v1/frames/frame_000634.raw` | 24,472,000 | `74dbd74924be2463cb827d29b257d6d01c428a1f2396ba7b270406850b915fa1` | `7530ab5f22d15ed66088fbd9f1aa24e31b3d0f3ffbee6be16a74c19af8022776` |
| 635 | `results/zkdiff_august_20260907/v1/frames/frame_000635.raw` | 24,472,000 | `d9aa9cd42a8a49ed918bfd8678c1c38c0cfda08abbd24fb27563cbcf4726ac79` | `51cb819578356d073505b7d4cbd827c0eaf445d7b4bdd3ee5acde3a316d8177e` |
| 636 | `results/zkdiff_august_20260907/v1/frames/frame_000636.raw` | 24,472,000 | `6f01941fa8a245708abb5d847e2a24b87bfc34eee5bef1724a6ecdf7ead212b7` | `aa103b261a87dcd3663f94bd0dd3eb3e221aca4d296800f29b3a18d48768fb30` |
| 637 | `results/zkdiff_august_20260907/v1/frames/frame_000637.raw` | 24,472,000 | `26c5f2fe85fc4d7df594d7b355f79d4e25e69f4ec661777e9c59a6a54365159e` | `3aa9f987aff4842524cdcf5be2f428c34a1fa548375dcf156c11e49487291554` |
| 638 | `results/zkdiff_august_20260907/v1/frames/frame_000638.raw` | 24,472,000 | `74bf1d7e7323c53b9de04473c765fdb31d8ab1829c7fc0ba441109e6bb9df11c` | `f0f18ae118ea807533529d3e20a61904523ff546cb9e1148bcd080d896aa4274` |
| 639 | `results/zkdiff_august_20260907/v1/frames/frame_000639.raw` | 24,472,000 | `a04a03636fc94844b60ee99d1f3bd599bdfd75b0efb1ca01ca8c2c665f82317b` | `1a7a72124972a071741f696cbbffd41bf9a6222c42a3bed3770fd02a511e4153` |
| 640 | `results/zkdiff_august_20260907/v1/frames/frame_000640.raw` | 24,472,000 | `500d34f1a9f996e9cb352386c55af24df675b24316973428b912aa44ea2f0536` | `746cdd8ae809cf9cca461833c474065cb48f41e6b1dc06ad1b11dfd3f6cebcb6` |
| 641 | `results/zkdiff_august_20260907/v1/frames/frame_000641.raw` | 24,472,000 | `33034c47bb7afa0de7b910999badc16c4d16d5e3eb271fccdd2b7ce3d10849d7` | `fd204c64342a91d5cbdb8a900a2788d7a070cc73e1c87d819fc4fa1b588472b5` |
| 642 | `results/zkdiff_august_20260907/v1/frames/frame_000642.raw` | 24,472,000 | `8bf0989546414c79d62f722be14ad32c063e98a6896f3a2e14189ec1404be6e3` | `3135099dbdab336c07dfafb93924a6c517a980bc97d706da1b5fb8d8fe28d0fe` |
| 643 | `results/zkdiff_august_20260907/v1/frames/frame_000643.raw` | 24,472,000 | `84e3b179483423e56839ad16ffcebd1e39f0dbde7b9c25b2a419479a5b79d0c1` | `b8003dc8f638671f790caa9716bff61fa4e8c4d892c076c087698e94380fbc4d` |
| 644 | `results/zkdiff_august_20260907/v1/frames/frame_000644.raw` | 24,472,000 | `bef525ef769ae6f06109cb2e398eb90126aed8aeb04a900bcca2b06be0f19be2` | `c63dd65985d17b12bd5bdf1b0ab4eaad6a42d9c780067bc982623019e230e123` |
| 645 | `results/zkdiff_august_20260907/v1/frames/frame_000645.raw` | 24,472,000 | `dd29f57f4cbc6251714bbb6f9a260e20a87573a7d188252ca5fa11eebfefcf73` | `b817a2fe23dc845dddbb48a6fcdb4632e788861b69cac2ffbaf29d2363d28cf4` |
| 646 | `results/zkdiff_august_20260907/v1/frames/frame_000646.raw` | 24,472,000 | `49becc364580ba571c2809cc10670e9421903d21a74cf02c3c0c3c7d23374a06` | `8c2fbc3987d826033a2a533e2aed56d16579690df29ab4fbbc18582779ee679c` |
| 647 | `results/zkdiff_august_20260907/v1/frames/frame_000647.raw` | 24,472,000 | `350eecb536364dcad8c3a0780eb2fd5884e794fd3890f832e681b218733d56b3` | `a50363dcbcd86e1326e5a6767b493111b077c282ba069bfd9d25b816d15d7758` |
| 648 | `results/zkdiff_august_20260907/v1/frames/frame_000648.raw` | 24,472,000 | `485851e2a10158dfadcc7024b1c845a8955a04f524499bd8caae2aed8476751a` | `2bec398b04f12f126b6f946552356014051f0ffe3097f7e852c345c2e50e9d3f` |
| 649 | `results/zkdiff_august_20260907/v1/frames/frame_000649.raw` | 24,472,000 | `efe1eb58323f2f076d9ea824fbbf561ac9994728c99ede7cccc4fef1c1096139` | `728bf34e45ed470ddc515ea4bb412b377325f1abe8eac36eeb7c269ddb1ba426` |
| 650 | `results/zkdiff_august_20260907/v1/frames/frame_000650.raw` | 24,472,000 | `173704407de65d1d9589388545c540ceee58636d566eb7751c961de91cf8edcd` | `adfe8a07bc07a6d7e0415e3bfac5be2ccf983774aa41b4d501f6fd6644617fe8` |
| 651 | `results/zkdiff_august_20260907/v1/frames/frame_000651.raw` | 24,472,000 | `61f3612fc57ad90e74d9ddce92648b4b62215a5ddff20815e0ae708fd54e8859` | `d8b3c42c0bd430a27518e7dc9f5ddf146a22238724514394958d3a7cc2e34a77` |
| 652 | `results/zkdiff_august_20260907/v1/frames/frame_000652.raw` | 24,472,000 | `7d77b0e3c075e134d86f5331e2a769d2e1044cd6bd8986c69ff58e07780fc7bd` | `6452836a583437aff0bdc7613b7e85dab98bf0fe6cc69f223d0697c1741951de` |
| 653 | `results/zkdiff_august_20260907/v1/frames/frame_000653.raw` | 24,472,000 | `7b2fb6579417dd21329ca58196c0dcc2493da2e171db46190f8f47ae675f4b11` | `83a29d3b07148f899027afdbcb6c202aadd2277f6bb6b5a41265f02ad9a0af1d` |
| 654 | `results/zkdiff_august_20260907/v1/frames/frame_000654.raw` | 24,472,000 | `d5975f6d05b5cdafbe36003f55cfa4c4d4280422c46e488407a160be2190522e` | `eb90a52be98473762b2e8239ccd2327d48bd096c2702d7cb9d0760e4170ee1e5` |
| 655 | `results/zkdiff_august_20260907/v1/frames/frame_000655.raw` | 24,472,000 | `a70294073a1e9a5a319ac1342bf612eabe26ac7cb41bec10e6cb4b9d73cde32e` | `655bb9cdfc481cc1e9dff390f3402c231e6ab5608d647a1f35f28d3ba1410064` |
| 656 | `results/zkdiff_august_20260907/v1/frames/frame_000656.raw` | 24,472,000 | `aa5c6c81ca43327a74ba5b586c8118bf0eab719560b4529eccf902ac5bcad49c` | `e98f0acae25b97d6690d193662a46d036989db96fe7172f9e5e10a49f286bc2b` |
| 657 | `results/zkdiff_august_20260907/v1/frames/frame_000657.raw` | 24,472,000 | `9bba866cf450271b03bf3f5f808060a896b107d3cfb55b837bfbe4e5f5ea5f5c` | `e3c8e0c25178c0d730274238ed15a592fa67a038b3c1b46f5546efde70b95fcf` |
| 658 | `results/zkdiff_august_20260907/v1/frames/frame_000658.raw` | 24,472,000 | `454f2997517a5d3468f876cba4d14e99fc13d0b9cee3e9d81cc9a98a1bed06c8` | `b172325641ae634c326b5517dbc311dfa2b175d64e04d5cdf3a226b43cd5418f` |
| 659 | `results/zkdiff_august_20260907/v1/frames/frame_000659.raw` | 24,472,000 | `ada4c5f4d0f0ec55d9a407890b2bb0abc43767260c7e6a6f9c95aa0489867b59` | `20310db95fe907d2d7a4fea930e4e0855945f88a5493acb1ebc2d446f40d7009` |
| 660 | `results/zkdiff_august_20260907/v1/frames/frame_000660.raw` | 24,472,000 | `3e05aa447c22e638531578a50813c538d998aedc68b7aad3b274acb4b0ee0b7b` | `b8e13b6485fa601f3dfe4fa3d823614f0b15d853081e899af878f6a2644d0a6e` |
| 661 | `results/zkdiff_august_20260907/v1/frames/frame_000661.raw` | 24,472,000 | `d2eb1e7d78add2d81976bfcefc119b8a93f19e54622af593ed642661698676f4` | `7094ae4f6bde9b7db6ce56364ecdcf7a18663e10e9926d8e7737fc2da66fac7b` |
| 662 | `results/zkdiff_august_20260907/v1/frames/frame_000662.raw` | 24,472,000 | `39faa5ae880a05e29e329adf85714d6033563624fb0a7ebafb9975d2d30928bd` | `1971a23200901f191b65290e7d28ad0e56bf5e0be47616a11d23b644ae5ba782` |
| 663 | `results/zkdiff_august_20260907/v1/frames/frame_000663.raw` | 24,472,000 | `58a51d57bd7dc9e5427dd156233b9e3183a060cf256a8eebbe1145c6699db235` | `d774d4fbfba8af0e2d884b0379f378d6c17665e3c9942fc713fee67526607280` |
| 664 | `results/zkdiff_august_20260907/v1/frames/frame_000664.raw` | 24,472,000 | `79f4de7a8639c7d5923a94e7fe600837f611018847ee57dc34bcebc0745aae6c` | `15b1a58d054bf666a31b5c68518e950c209fa5b2c813075fcaf137f29afd9bd9` |
| 665 | `results/zkdiff_august_20260907/v1/frames/frame_000665.raw` | 24,472,000 | `f513031caafdbd1cca0f2be5255a579f7da405fe19ca673c6b70ef1a2220bd9d` | `175ecb372499ec3bc0bff8fa466e42b32360697aca62a34388be99ed5e45c6e6` |
| 666 | `results/zkdiff_august_20260907/v1/frames/frame_000666.raw` | 24,472,000 | `b4fbe28e36144468c62c69b2869c4ba28c94924a1ceac37ffe84cd3f958b28fb` | `116f819f6cf97f6f3e0c5a5b678ea0faa4dfcc0f0950f10418ea1fc451918397` |
| 667 | `results/zkdiff_august_20260907/v1/frames/frame_000667.raw` | 24,472,000 | `c4bcdf28ea6744a9b9a3fc5daad4a203024b2e37e5196f6e0e7663729b162f30` | `8551dcf66873a28c97fb16f1cdd0bd72d8278a5253f810fa91e262d0a2cd3030` |
| 668 | `results/zkdiff_august_20260907/v1/frames/frame_000668.raw` | 24,472,000 | `627297cf9fbedf3544d31a679a8361e7aa52ba76dcb173f9735eb12803ca39d4` | `e666b1463e94dfddea083bc8b65b44ae6cbf77dfa4cf413296050cd6d8dca777` |
| 669 | `results/zkdiff_august_20260907/v1/frames/frame_000669.raw` | 24,472,000 | `bb5031efa022c2a3cd566cc13e81d62351d64277051d4a0bd8b7aa5e382d4b1a` | `57720f59b60f75f66d08432bec99fb04f3a2adf0bc3924fc102c968e190f8ddf` |
| 670 | `results/zkdiff_august_20260907/v1/frames/frame_000670.raw` | 24,472,000 | `b831b6c3d107083773ef20123d6c7db01cc72f9e5849703d1b44b312e1806358` | `e9f3169d97466c6f8c98c99454f51656900013892d7094c440bc3b7a24c11215` |
| 671 | `results/zkdiff_august_20260907/v1/frames/frame_000671.raw` | 24,472,000 | `d6e0368e6c8e3e4414110ddc39420399faf7840275d1b26cd39ae4cc90843526` | `5dc37d9d334a22f2b0f2a0cf57d1d5e9440c2809959c55d97a5b6ed52107143b` |
| 672 | `results/zkdiff_august_20260907/v1/frames/frame_000672.raw` | 24,472,000 | `916febead42ba9e1f272ee5e4cf299eaea8219f9133dbbf16ac11137d5a18853` | `a1150270e0a8de9aa3ade89f81f94665f1495ecb1fa4f083211701350b383cfd` |
| 673 | `results/zkdiff_august_20260907/v1/frames/frame_000673.raw` | 24,472,000 | `294354a640bfea22b88cf53035edb061ac60639f2919a8b636d993a1c278a7d3` | `ff053da4c359da31c4346172b5cf1fff301cd39251611d728950950532107bb6` |
| 674 | `results/zkdiff_august_20260907/v1/frames/frame_000674.raw` | 24,472,000 | `cf451dcc3dfba32baa9f00460b133fc7a068a368477b14d64ca19cf09c4f3f25` | `444f1a1e16d08503ef54d5f394eb7b6617da739f18ae5cbb35ed5b255324ce3e` |
| 675 | `results/zkdiff_august_20260907/v1/frames/frame_000675.raw` | 24,472,000 | `e3602205dbba76d3e295cc65379f36f185ffa268b5bdde64c3009b94bc1cfebb` | `9e2507ad683a35c62a676d2439ae2a4b33c56a30909a549f50505c9c1a0ab87b` |
| 676 | `results/zkdiff_august_20260907/v1/frames/frame_000676.raw` | 24,472,000 | `95e9facbc168954ecba32aabcdf83933e9f9e1b5ef760491bee17c93d2b0c64b` | `af20c45da2a5fd2001de07628c325c93e082c81ef0ab714f18dea8648b9f39c1` |
| 677 | `results/zkdiff_august_20260907/v1/frames/frame_000677.raw` | 24,472,000 | `36733612120e52150b4cf767d0736343d22f3495b31b6bf742fa62e4829730de` | `e8556772155e7dafd47856f2e35762150eb9abc4413f1a2fd511b59452f59165` |
| 678 | `results/zkdiff_august_20260907/v1/frames/frame_000678.raw` | 24,472,000 | `064785c5ea5937899f83db036829574b038a1f6646b337d1ee61e305009c0fcb` | `106ef10f93ed4a433f43da8757673e4ed4efced844c555b3a7235f51db72d9ec` |
| 679 | `results/zkdiff_august_20260907/v1/frames/frame_000679.raw` | 24,472,000 | `8c16f3cb27dd6e78beb0e3721363d56f2e0a466361e0af64a998d5059a876ac5` | `920689eb3b36abc797a5e3be2671646007161ec0566ae415964e1d66ca9a32a1` |
| 680 | `results/zkdiff_august_20260907/v1/frames/frame_000680.raw` | 24,472,000 | `71a5d6d4c42914fb8bac350010f9ac9b6ce00d6519f736f7b634b14b7f2893c3` | `1c201c56fcf63e281b697aeee8c300650bf56841d8124fc45678dace00492cd8` |
| 681 | `results/zkdiff_august_20260907/v1/frames/frame_000681.raw` | 24,472,000 | `08b963b22f384e71ce637c4af26e8843aa9b1e940bf610ba59db5e49b8f11a64` | `4ef0ea0e06e43f551b87dc54f8e1e575ad54a2640ad66ded533bf45a12e52dc8` |
| 682 | `results/zkdiff_august_20260907/v1/frames/frame_000682.raw` | 24,472,000 | `906dd390407636f0c2ad6f2be7fb27a1ec6e0196cc6c52b85af83ed8ed3d4979` | `bfd4f8edcf5eae51ac74addc2d16d0c57c3589359f78da016302b8b9f31c39e9` |
| 683 | `results/zkdiff_august_20260907/v1/frames/frame_000683.raw` | 24,472,000 | `90669fda3ad4f3c39ec6ac17c846f53cb00330a9ba533ead7dff5138147cfe9a` | `395bc546edb9c5872c1374c4511dfbbaf1936c37a38b16e0d62b44575b69e090` |
| 684 | `results/zkdiff_august_20260907/v1/frames/frame_000684.raw` | 24,472,000 | `dddbb6c317a2a043b794c0a1f1767637af02bddb32807f9b8dadab835b37e4a7` | `56601953910d443d648fe3b5a65e8a57af72ab431433cba62b2e2d4a206fbd3c` |
| 685 | `results/zkdiff_august_20260907/v1/frames/frame_000685.raw` | 24,472,000 | `e2eb7f54878d16e3dc2d575502eb1df34f5955119ddf5325342cd8e364ab085f` | `b2d138d3ad121f5b7e595704efeae7c263947366fba01680bf266eddae67579b` |
| 686 | `results/zkdiff_august_20260907/v1/frames/frame_000686.raw` | 24,472,000 | `adbe025d3f8c6ae1745687e0e4ef57c9b89dfc4d24f625dac16b8c4e2b8779c0` | `bbcc9c10a435b0f1dbfa0e77e56a0e13af6c5524607ca3ae49b40e0062a10e82` |
| 687 | `results/zkdiff_august_20260907/v1/frames/frame_000687.raw` | 24,472,000 | `367b88298921be64189070418901048bda846d6060beba35efc598e4b84ea32a` | `5813ef0893a7ff532931a2c9fa2c36211341ec3237e3e74e0d804bc43f9597b3` |
| 688 | `results/zkdiff_august_20260907/v1/frames/frame_000688.raw` | 24,472,000 | `5bd243bd0dbdf928aa7e494b276111304ed1ea43938a36325c7a234acbfddd42` | `5587cf3e5ab9ee3b4a4c55e4938a4fca1f1ebaeb4d7452d454c32585549d14ca` |
| 689 | `results/zkdiff_august_20260907/v1/frames/frame_000689.raw` | 24,472,000 | `8c0a007828016d63020a23f8924e6f9c70f9836194809cec90322c71e154b0b5` | `2e067404fd6183dd9de1b3eafeb1c2b198df4fb444b3943bc3c0672cd7b728bf` |
| 690 | `results/zkdiff_august_20260907/v1/frames/frame_000690.raw` | 24,472,000 | `d61f57bb874f9b0ab8a14ac0fcf05d970bb73d2a13d1e5b7f21afd51be99fbad` | `91732950049cef87fef38c61eeafd885b4dd775bcd64ae76014a125ddfbd0f16` |
| 691 | `results/zkdiff_august_20260907/v1/frames/frame_000691.raw` | 24,472,000 | `a2c0d10c880099aa9b012e91c2d4d4defbf53780331df30bd8dfaf651f6e3128` | `7464f8e39f14f88f018e7920c942937e691d21826b55193b738fc025a867df5c` |
| 692 | `results/zkdiff_august_20260907/v1/frames/frame_000692.raw` | 24,472,000 | `fde5f1bb6ede2fd7d3c339f1844423d85a3482206b3ba1a90ffe1124d821bf93` | `330fc005aeb1a219ae8883229307637377d6f16bd5441ff7f16022a804bc6efd` |
| 693 | `results/zkdiff_august_20260907/v1/frames/frame_000693.raw` | 24,472,000 | `60215b5a7fb423f50f59de7b9fd68db3bd7f4086e329d416e2efc0bc2601d8a4` | `ae79fab74d13567158fa4037323e9ac3870dc8f486a43c56495eba59137ba9b5` |
| 694 | `results/zkdiff_august_20260907/v1/frames/frame_000694.raw` | 24,472,000 | `a6a260eb1aa758a181988e75ea2c72257419e7507e10e2c3e5a4a5f591c79d41` | `0d0b3f9703e2a3c8bb97eff49571994bced9f894ea19bb6e9d4e56e84fc45fdb` |
| 695 | `results/zkdiff_august_20260907/v1/frames/frame_000695.raw` | 24,472,000 | `bbac3e0405cf12fe97b253efe052ceb0b0fa6e788079370555862f3c4cd8e54c` | `7797b2d8de6cf5bc553d459450f83fde586719544aa6daf3dad5f4087db77270` |
| 696 | `results/zkdiff_august_20260907/v1/frames/frame_000696.raw` | 24,472,000 | `cf06056558438d9b10db74c4ca57897e22b01c4abd9dfffcb327fcac092c6e03` | `a26bd8b4eaf280db479a376ddddad62fc5f4f3316985e36029335e0e0d2effbe` |
| 697 | `results/zkdiff_august_20260907/v1/frames/frame_000697.raw` | 24,472,000 | `888c92e7af383c99eeb5d30383783f01655a1da461ec11ac081527cb47738f3e` | `50e54450979f9310e20b1710af0632e92977fd36ca7cc3a344153d1f201dafcc` |
| 698 | `results/zkdiff_august_20260907/v1/frames/frame_000698.raw` | 24,472,000 | `4181fedefffb619f53d593ba0c6c6cb588f6429ab5c4bfbc7562d2088426b3fe` | `8e3210573d52d80b0730c7113bbcf2b1250bc6fe64bbdc0895a79cf4eda758d2` |
| 699 | `results/zkdiff_august_20260907/v1/frames/frame_000699.raw` | 24,472,000 | `27534fd49605ee98047b00f20d1be4d196585a24da4b9c752ed1a95e9dae53a6` | `4fe2ac89d2a49d61eb6edbb4fc38a3d5d8c2986cce69d1dda726aa5c5c644d1d` |
| 700 | `results/zkdiff_august_20260907/v1/frames/frame_000700.raw` | 24,472,000 | `f65658da6b3a1fac660b557977db7b3982fa5e94e6aaa19a89343f684938225b` | `c0d8438c338a1fc018f18a96bb0d1a68f8b3bde45a618830aec8a49ff064406c` |
| 701 | `results/zkdiff_august_20260907/v1/frames/frame_000701.raw` | 24,472,000 | `3b7fa296caf653d414c857aa2a38a64f46c23b4526ff98ba1299cba6e0a74fe4` | `0b47398f7ddd9bf93f49864c8e7323b5ca4e12221e6e5be9351f6b514cb28197` |
| 702 | `results/zkdiff_august_20260907/v1/frames/frame_000702.raw` | 24,472,000 | `ffec0b726bbbd949dc13020e141e78c4fed23c64d2d7fb881fcc59ff63c6f21f` | `5e1537494740b372e5470a1f07e3338453a2cf1887e89dd0bfc5e2e2827acc13` |
| 703 | `results/zkdiff_august_20260907/v1/frames/frame_000703.raw` | 24,472,000 | `4ef44e0e886f125cb8ce4bee599b289b6d59d54b7c5beaf13e8625e72cec383e` | `c8542469f69b2f438157bd249cf8507166a59c27b6db0333a49b89cf9f4918e0` |
| 704 | `results/zkdiff_august_20260907/v1/frames/frame_000704.raw` | 24,472,000 | `2cb84abe77ba699dc42648c67822214c8f00c0de9ccf28a74f76e515a29efa8c` | `c110b37b56f582ab4e65e4228da3e9b114f748ef05c1b1564b8ac95854278202` |
| 705 | `results/zkdiff_august_20260907/v1/frames/frame_000705.raw` | 24,472,000 | `98e6036f183f9d77ffc8c0d42f8611a51f4bac00fbefb6a847f651a176ee99b2` | `17f6a5155408174e0f3922514be24c1b82fa0dcd24119de3bcb4dc8cc144f7ce` |
| 706 | `results/zkdiff_august_20260907/v1/frames/frame_000706.raw` | 24,472,000 | `43e08170f060481438bea9dc891e8d4e4556645a3af07670e3c860d8c8d72ca9` | `01fb833593bbe832a3a52839970fbf9dd2263655a02298adc83ce22b1746bbb3` |
| 707 | `results/zkdiff_august_20260907/v1/frames/frame_000707.raw` | 24,472,000 | `632640d7726a4810d97fb9bb995905838772e8fe375965c5b21cabdbf521572b` | `d7c7d8ee35ce466c9de2f6daff29220d6eb6d0a99b4edf398414ed3098671f1c` |
| 708 | `results/zkdiff_august_20260907/v1/frames/frame_000708.raw` | 24,472,000 | `c0def59e06517d9fabb2a73a63d96aa766cad2dcc3479aaa855a6d62820e9b87` | `3545e699f4a4628db921c2777be32a84c8c9234315d4b6f960c666b315984597` |
| 709 | `results/zkdiff_august_20260907/v1/frames/frame_000709.raw` | 24,472,000 | `5d6d6ac3d0bbe3216294e742fceefb56673fc345e1b3613a29c5b91b0b1cf659` | `29ab7820f2eae9f4d504d6992e931b90dc41d95724f381706207dc22d3cfd470` |
| 710 | `results/zkdiff_august_20260907/v1/frames/frame_000710.raw` | 24,472,000 | `f4a83705ae4461cba0babff95f06d5c649380c575ec12efb32a4f58a3af82bbe` | `b3a1712058eac73cf863a6d8818a247fe5d7ec12b8c4c348d3e4a8240237603e` |
| 711 | `results/zkdiff_august_20260907/v1/frames/frame_000711.raw` | 24,472,000 | `88af26138f6cd783d67c1df60857715e6feb5fa97409febf174baee530c782ba` | `7bc477511cd6f17c8974930af3d3c9991e3357f2c1ba2604022886e5772b5d32` |

Verified frame by frame against the chain log and the receipts when the data-layer bundle was built (`build_r2_bundle.py`;
the bundle's `_control/RELEASE.json` carries the staging time); `PINS.json` `frames` carries the same digests.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-08 | BOSUN | First version, on the principal's decision to publish the frames. |
| 1.1 | 2026-09-08 | BOSUN | What the frames show (the privacy sweep, Astra round 7); how to read a frame; the staging time moved to the bundle's RELEASE.json. |
| 1.2 | 2026-09-09 | BOSUN | authorship line, 9 September 2026. |
