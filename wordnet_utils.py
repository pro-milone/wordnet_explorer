import re
import pandas as pd

# ---------------------------------
# POINTER LABELS
# ---------------------------------
POINTER_LABELS = {
    "@": "hypernym",
    "~": "hyponym",
    "@i": "instance hypernym",
    "~i": "instance hyponym",
    "#m": "member meronym",
    "#s": "substance meronym",
    "#p": "part meronym",
    "%m": "member holonym",
    "%s": "substance holonym",
    "%p": "part holonym",
    "+": "derivationally related form",
    "=": "attribute",
    "!": "antonym",
    ">": "cause",
    "^": "entailment",
    "$": "verb group",
    "&": "similar to",
    ";c": "domain - topic",
    ";r": "domain - region",
    ";u": "domain - usage"
}

# ---------------------------------
# PARSE DATA FILES
# ---------------------------------
def parse_wn_line(line):
    """Parse one synset line from a data.* file"""
    if " | " in line:
        data, gloss = line.split(" | ", 1)
    else:
        data, gloss = line, ""

    parts = data.split()

    synset_offset = parts[0]
    lex_filenum = parts[1]
    pos = parts[2]
    w_cnt = int(parts[3], 16)  # hex

    words = []
    idx = 4
    for _ in range(w_cnt):
        word = parts[idx]
        lex_id = parts[idx + 1]
        words.append({"word": word, "lex_id": lex_id})
        idx += 2

    p_cnt = int(parts[idx])
    idx += 1

    pointers = []
    for _ in range(p_cnt):
        symbol = parts[idx]
        target_offset = parts[idx + 1]
        target_pos = parts[idx + 2]
        source_target = parts[idx + 3]
        pointers.append({
            "symbol": symbol,
            "relation": POINTER_LABELS.get(symbol, symbol),
            "target_offset": target_offset,
            "target_pos": target_pos,
            "source_target": source_target
        })
        idx += 4

    return {
        "synset_offset": synset_offset,
        "lex_filenum": lex_filenum,
        "pos": pos,
        "words": words,
        "pointers": pointers,
        "gloss": gloss.strip()
    }

def load_wordnet(data_files):
    """Load multiple WordNet data.* files into a single DataFrame"""
    records = []
    for fname in data_files:
        with open(fname, "r") as f:
            for line in f:
                line = line.strip()
                if not line or not re.match(r"^\d{8}\s", line):
                    continue
                records.append(parse_wn_line(line))
    return pd.DataFrame(records)

# ---------------------------------
# PARSE INDEX FILES
# ---------------------------------
def load_index(index_files):
    """
    Load WordNet index.* files into a dict:
    {lemma: [offsets...]}
    """
    index = {}
    for fname in index_files:
        with open(fname, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(" "):
                    continue
                parts = line.split()

                # Skip headers
                if len(parts) < 5:
                    continue
                if parts[1] not in {"n", "v", "a", "r"}:
                    continue

                lemma = parts[0]
                synset_cnt = int(parts[2])
                offsets = parts[-synset_cnt:]
                index.setdefault(lemma, []).extend(offsets)
    return index

# ---------------------------------
# SEARCH FUNCTION
# ---------------------------------
def explore_word(df, index_dict, word):
    """
    Find a word in WordNet (using index) and return formatted results.
    Instead of printing, this returns a list of markdown strings
    (so it works well in Streamlit).
    """
    output = []
    if word not in index_dict:
        return [f"❌ Word '{word}' not found in index."]

    offsets = index_dict[word]
    for offset in offsets:
        syn = df[df["synset_offset"] == offset]
        if syn.empty:
            continue

        row = syn.iloc[0]
        syn_words = [w["word"] for w in row["words"]]
        header = f"### Synset {row['synset_offset']} ({row['pos']}): {', '.join(syn_words)}"
        gloss = f"_Gloss_: {row['gloss']}"
        block = [header, gloss]

        for ptr in row["pointers"]:
            target_offset = ptr["target_offset"]
            target = df[df["synset_offset"] == target_offset]
            relation = ptr["relation"]

            if not target.empty:
                target_words = [w["word"] for w in target.iloc[0]["words"]]
                block.append(f"- **{relation}** ({ptr['symbol']}) → {', '.join(target_words)}")
            else:
                block.append(f"- **{relation}** ({ptr['symbol']}) → [missing synset {target_offset}]")

        output.append("\n".join(block))

    return output
