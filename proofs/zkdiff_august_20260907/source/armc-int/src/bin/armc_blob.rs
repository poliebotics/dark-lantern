//! `armc-blob <oracle_export_dir> <out_dir>`: build the constants blob and the raw input files the
//! SP1 bench host feeds to the guest, print their SHA-256 and sizes, and verify the blob
//! round-trips through the parser.

use armc_int::loader::{i16_le_bytes, load_constants, load_oracle, sha256_hex};
use armc_int::Constants;
use std::path::PathBuf;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 3 {
        eprintln!("usage: armc-blob <oracle_export_dir> <out_dir>");
        std::process::exit(2);
    }
    let dir = PathBuf::from(&args[1]);
    let out = PathBuf::from(&args[2]);
    std::fs::create_dir_all(&out).expect("create out dir");

    let k = load_constants(&dir);
    let bytes = k.to_bytes();
    let back = Constants::parse(&bytes).expect("blob parses");
    assert!(back == k, "blob round trip");
    let blob_path = out.join(format!("constants_{}.blob", k.qmax_tag()));
    std::fs::write(&blob_path, &bytes).expect("write blob");
    println!("{}  {}  ({} bytes)", sha256_hex(&bytes), blob_path.display(), bytes.len());

    let o = load_oracle(&dir);
    for (name, v) in [("C_int", &o.c_int), ("noise_int", &o.noise_int), ("E_int", &o.e_int), ("Ct_int", &o.ct_int)] {
        let b = i16_le_bytes(v);
        let p = out.join(format!("{name}_{}_row{}_cond{}.i16", o.index.manifest.sid, o.index.manifest.row, o.index.manifest.conditioning_row));
        std::fs::write(&p, &b).expect("write input");
        println!("{}  {}  ({} bytes)", sha256_hex(&b), p.display(), b.len());
    }
    println!("residual_sum_int={}  scheme={}  convs={} groupnorms={} attentions={} luts={} exp_entries={}", o.residual_sum_int, o.index.manifest.scheme, k.convs.len(), k.gns.len(), k.attns.len(), k.luts.len(), k.exp_table.len());
    let macs: u64 = k
        .convs
        .iter()
        .map(|l| {
            // MACs per pass need the spatial size of each layer; report weights instead here
            (l.w.len()) as u64
        })
        .sum();
    println!("weights={macs}");
}

trait QmaxTag {
    fn qmax_tag(&self) -> &'static str;
}

impl QmaxTag for Constants {
    fn qmax_tag(&self) -> &'static str {
        if self.qmax == 127 {
            "int8"
        } else {
            "int16"
        }
    }
}
