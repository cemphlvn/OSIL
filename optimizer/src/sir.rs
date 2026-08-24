//! Minimal reader for the slice's `.osil` case files.
//!
//! Deliberately NOT a fork of the reference lexer in `tools/osil_check.py`.
//! The slice's case files use constructs (`sir { ... }`, applied terms like
//! `(reduce mul a 32000)`) that the ratified grammar v0.6 does NOT contain —
//! `factor = identifier | number | "(" expr ")"` has no application form.
//! Formalizing them is the spec's job (see docs/research/U6); this reader
//! exists so the tool can run BEFORE that happens, per the working-tool-first
//! decision. Keep it dumb, and delete it when the grammar catches up.

use std::collections::BTreeMap;

#[derive(Debug)]
pub struct Case {
    pub name: String,
    pub sir: String,
    pub guards: BTreeMap<String, String>,
    pub constraints: BTreeMap<String, String>,
}

/// Strip `//` line comments, keeping the rest verbatim.
fn decomment(src: &str) -> String {
    src.lines()
        .map(|l| match l.find("//") {
            Some(i) => &l[..i],
            None => l,
        })
        .collect::<Vec<_>>()
        .join("\n")
}

/// Return the text between the brace that follows `head` and its match.
fn block<'a>(src: &'a str, head: &str) -> Option<&'a str> {
    let start = src.find(head)? + head.len();
    let open = start + src[start..].find('{')?;
    let mut depth = 0usize;
    for (i, ch) in src[open..].char_indices() {
        match ch {
            '{' => depth += 1,
            '}' => {
                depth -= 1;
                if depth == 0 {
                    return Some(&src[open + 1..open + i]);
                }
            }
            _ => {}
        }
    }
    None
}

/// Parse `k = v` lines into a map.
fn kvs(body: &str) -> BTreeMap<String, String> {
    body.lines()
        .filter_map(|l| l.split_once('='))
        .map(|(k, v)| (k.trim().to_string(), v.trim().to_string()))
        .filter(|(k, v)| !k.is_empty() && !v.is_empty())
        .collect()
}

pub fn parse(src: &str) -> Result<Case, String> {
    let src = decomment(src);

    let name = src
        .split_whitespace()
        .skip_while(|w| *w != "model")
        .nth(1)
        .ok_or("no `model <name>` declaration")?
        .trim_end_matches('{')
        .to_string();

    let sir = block(&src, "sir")
        .ok_or("no `sir { ... }` block")?
        .trim()
        .to_string();
    if sir.is_empty() {
        return Err("empty sir block".into());
    }

    Ok(Case {
        name,
        sir,
        guards: block(&src, "guards").map(kvs).unwrap_or_default(),
        constraints: block(&src, "constraints").map(kvs).unwrap_or_default(),
    })
}
